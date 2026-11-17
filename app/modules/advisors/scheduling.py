
from prompts import SCHEDULING_ADVISOR_SYSTEM
from config import SCHEDULING_ADVISOR_VALID_RESPONSES
from modules.agent_tools import build_lookup_executor, offer_interview_slots, prompt_template
from prompts import SCHEDULE_EXECUTOR_SYSTEM
from modules.advisors.base import SingleResponseAdvisor

class SchedulingAdvisor(SingleResponseAdvisor):

    def __init__(self, position, model_size="big", temperature=0.0):
        super().__init__(SCHEDULING_ADVISOR_SYSTEM, SCHEDULING_ADVISOR_VALID_RESPONSES, model_size, temperature)
        self.schedule_code = "NOW"
        self.position = position
        self.executor = self._create_executor()
        

    def set_position(self, position):
        self.position = position

    def _create_executor(self):
        schedule_prompt = prompt_template(SCHEDULE_EXECUTOR_SYSTEM)
        return build_lookup_executor([offer_interview_slots], schedule_prompt, self.model_size)

    def decide(self, user_message="", num_of_tries=0):
        response = (self.get_response(user_message, max_tokens=40) or "").strip()
        lines = response.split("\n")
        label = lines[0].strip()
        if label not in SCHEDULING_ADVISOR_VALID_RESPONSES:
            if num_of_tries >= 3:
                return None
            mes = "The first line must be one of the following: " + ", ".join(SCHEDULING_ADVISOR_VALID_RESPONSES) + ". If you choose " + SCHEDULING_ADVISOR_VALID_RESPONSES[0] + ", put the time code on the next line."
            return self.decide(mes, num_of_tries + 1)
        self.schedule_code = "NOW"
        if len(lines) > 1 and lines[1].strip() != "":
            self.schedule_code = lines[1].strip()
        return label

    def find_available_times(self):
        times = [message.timestamp for message in self.conversation.messages if message.timestamp is not None]
        result = self.executor.invoke({
            "input": "schedule_code: " + self.schedule_code + "\nmessage_time: " + times[-1] + "\nposition: " + self.position,
            "chat_history": self.conversation.get_history(with_system=False)
        })
        return result["output"]