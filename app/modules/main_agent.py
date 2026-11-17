from prompts import GUIDE_TO_SCHEDULE_SYSTEM, GUIDE_TO_EXIT_SYSTEM, MAIN_AGENT_SYSTEM, CHOOSE_ADVISOR_SYSTEM, CONSULT_AGAIN_SYSTEM
from modules.advisors.base import ExitAdvisor, Advisor, one_time_advisor, JobTitleAdvisor
from modules.advisors.info import InfoAdvisor
from modules.advisors.scheduling import SchedulingAdvisor
from modules.job.text import load_jobs_list
from datetime import timedelta
from modules.job.job import Job
from config import POSITIVE_VALID_RESPONSES, CHAT_START

_EXIT = POSITIVE_VALID_RESPONSES["end"]
_SCHEDULE = POSITIVE_VALID_RESPONSES["schedule"]
_INFO = POSITIVE_VALID_RESPONSES["info"]

def choose_advisor_prompt(tried, remaining):
    if not tried:
        return CHOOSE_ADVISOR_SYSTEM
    return (
        CHOOSE_ADVISOR_SYSTEM
        + "\n\nAlready tried and vetoed: "
        + ", ".join(tried)
        + ". Choose only from: "
        + ", ".join(remaining)
        + "."
    )
def consult_again_prompt(tried, remaining):
    return (
        CONSULT_AGAIN_SYSTEM
        + "\n\nTried: "
        + ", ".join(tried)
        + ".\nRemaining: "
        + ", ".join(remaining)
        + "."
    )

class MainAgent(Advisor):
    def __init__(self, model_size="big", temperature=0.5):
        super().__init__(MAIN_AGENT_SYSTEM, model_size, temperature=temperature)
        self.jobs_list = self._load_jobs_list()
        self.job = Job(title=None, description=None)
        self.trying_to_schedule = False
        self._set_system_prompt()
        self._create_advisors()
        
        
    def _create_advisors(self):
        self.exit_advisor = ExitAdvisor(self.model_size, temperature=0.0)
        self.scheduling_advisor = SchedulingAdvisor(self.job.title, self.model_size, temperature=0.0)
        self.info_advisor = InfoAdvisor(self.job, self.model_size, temperature=0.0)
        self.job_title_advisor = JobTitleAdvisor(self.jobs_list, self.model_size, temperature=0.0)       

    def _load_jobs_list(self):
        return load_jobs_list()

    def _set_system_prompt(self):
        job_text = "No job description is available." if self.job.description is None else "Job description:\n" + self.job.description
        self.conversation.system_prompt = MAIN_AGENT_SYSTEM + "\n\n" + job_text
        return

    def _advisors(self):
        return (self.exit_advisor, self.scheduling_advisor, self.info_advisor, self.job_title_advisor)

    def reset_messages(self):
        self._set_system_prompt()
        super().reset_messages()
        for advisor in self._advisors():
            advisor.reset_messages()
        self.trying_to_schedule = False

    def add_message(self, message, role, timestamp=None):
        result = super().add_message(message, role, timestamp)
        for advisor in self._advisors():
            advisor.add_message(message, role, timestamp)
        return result
    
    def add_multiple_messages(self, messages, role, timestamps=None, reset=False):
        return super().add_multiple_messages(messages, role, timestamps, reset=reset)

    def reset_advisors(self):
        history = self.conversation.lines(with_system=False)
        for advisor in self._advisors():
            advisor.add_multiple_messages(history, "user", reset=True)

    # conversation workflow

    def _consult_single_advisor(self, chosen_label):
        if chosen_label == _EXIT:
            vote = self.exit_advisor.decide()
            if vote == _EXIT:
                return _EXIT, _EXIT
            return None, vote
        if chosen_label == _SCHEDULE:
            vote = self.scheduling_advisor.decide()
            if vote == _SCHEDULE:
                return self.scheduling_advisor.find_available_times(), _SCHEDULE
            return None, vote
        if chosen_label == _INFO:
            vote = self.info_advisor.decide()
            if vote == _INFO:
                return self.info_advisor.ask_question(), _INFO
            return None, vote
        return None, None

    def run_one_time_advisor(self, prompt):
        return one_time_advisor(
            prompt,
            self.conversation.lines(with_system=False),
            model_size=self.model_size,
            temperature=0.0,
            max_tokens=16,
        )

    def advisors_decision(self):
        tried = []
        labels = list(POSITIVE_VALID_RESPONSES.values())
        while len(tried) < 3:
            remaining = [label for label in labels if label not in tried]
            if len(tried) == 2:
                choice = remaining[0]
            else:
                prompt = choose_advisor_prompt(tried, remaining)
                choice = self.run_one_time_advisor(prompt)
                choice = (choice or "").strip()
                if choice not in labels or choice in tried:
                    return None, None

            decision_output, action_or_veto = self._consult_single_advisor(choice)
            tried.append(choice)
            if decision_output is not None:
                return decision_output, action_or_veto
            if len(tried) >= 3:
                return None, None
            remaining = [label for label in labels if label not in tried]
            prompt = consult_again_prompt(tried, remaining)
            again = self.run_one_time_advisor(prompt)
            again = (again or "").strip()
            if again != "Consult Advisor Again":
                return None, None
        return None, None

    def unknown_job_workflow(self):
        decision = self.job_title_advisor.decide()
        if decision is None or decision == "Unknown":
            return None
        if decision.startswith("Not Offered:"):
            return decision.split(":", 1)[1].strip()
        self.job.set_title(decision)
        self.scheduling_advisor.set_position(self.job.title)
        self.info_advisor.set_job(self.job)
        self.info_advisor.create_job_description()
        self._set_system_prompt()
        return None

    def message_workflow(self):
        missing = None
        if self.job.title is None:
            # if job is not known yet - try to find it
            missing = self.unknown_job_workflow()
        if self.job.title is None:
            # if job is still not known
            decision = self.exit_advisor.decide()
            if decision == _EXIT:
                return decision, _EXIT
            if missing:
                # if candidate asks for a role that does not exists
                return missing, "Not Offered"
            return None, None

        return self.advisors_decision()

    def run(self):
        exit = False
        decision, action = self.message_workflow()
        if action == "Not Offered":
            # if candidate asks for a role that does not exists
            decision = self.say_job_not_offered(decision)
        if action == _INFO and decision == "NOT IN DESCRIPTION":
            # if candidate asks questions that are not in the description
            decision = self.guide_to_schedule()
        if action == _SCHEDULE:
            # if advisor decide to schedule an interview
            self.trying_to_schedule = True
        if action == _EXIT:
            # if advisor decide to end the conversation
            decision = self.guide_to_exit()
            exit = True
            self.trying_to_schedule = False
        if decision == None:
            # if non of the above
            decision = self.continue_chat()
        self.add_message(decision, "assistant")
        return decision, exit

    def say_job_not_offered(self, asked):
        saved = self.conversation.system_prompt
        self.conversation.system_prompt = saved + "\n\nThe candidate asked for this role: " + asked + ". That role is not offered. Tell them it is not offered and ask which other job they came for. Name the role they asked for. Do not greet."
        reply = self.continue_chat()
        self.conversation.system_prompt = saved
        return reply

    # conversation advisors

    def guide_to_schedule(self):
        return one_time_advisor(GUIDE_TO_SCHEDULE_SYSTEM, self.conversation.lines(with_system=False), model_size=self.model_size, temperature=0.3, max_tokens=80)

    def guide_to_exit(self):
        return one_time_advisor(GUIDE_TO_EXIT_SYSTEM, self.conversation.lines(with_system=False), model_size=self.model_size, temperature=0.3, max_tokens=80)

    def continue_chat(self):
        return self.get_response(save_response=False, temperature=0.3, max_tokens=80)
        
    # Terminal chat loop

    def chat(self):
        self.reset_messages()
        when = CHAT_START  # the demo calendar is 2024, so the start stays inside that year
        while True:
            message = input("Enter your message: ")
            timestamp = when.strftime("%Y-%m-%dT%H:%M:%SZ")
            self.add_message(message, "user", timestamp)
            when = when + timedelta(minutes=1)
            decision, exit = self.run()
            print(decision)
            if exit:
                print("Thank you for using the chatbot. Goodbye!")
                break
        return 
