from tools import load_model
from prompts import JOB_TITLE_SYSTEM
from config import EXIT_ADVISOR_VALID_RESPONSES, advisor_reply_line
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from modules.conversations import Conversation
from hugging_face_client import load_exit_tuned_advisor, tuned_exit_label

def one_time_advisor(system_prompt, messages, timestamps=None, model_size="big", temperature=0.0, max_tokens=None):
    advisor = Advisor(system_prompt, model_size, temperature=temperature)
    advisor.add_multiple_messages(messages, "user", timestamps, reset=True)
    response = advisor.get_response(max_tokens=max_tokens)
    return response.strip()

class Advisor:
    def __init__(self, system_prompt, model_size="big",temperature=0.5):
        self.model_size = model_size
        self.llm, self.openai_model = load_model(model_size)
        self.conversation = Conversation(system_prompt)
        self.temperature = temperature
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "{system}"),
            MessagesPlaceholder("history"),
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()

    def _chat_history(self):
        return self.conversation.get_history(with_system=False)

    def add_message(self, message, role, timestamp=None):
        self.conversation.add(message, role, timestamp)

    def add_multiple_messages(self, messages, role, timestamps=None, reset=False):
        if reset:
            self.reset_messages()
        for index, message in enumerate(messages):
            if isinstance(message, dict):
                self.add_message(message["content"], message["role"], message["timestamp"])
            else:
                self.add_message(message, role, timestamps[index])
    
    def get_response(self, user_message= "", save_response=True, temperature=None, max_tokens=None):
        if user_message != "":
            self.add_message(user_message, "user", self.conversation.last_timestamp())
        temperature = temperature if temperature is not None else self.temperature
        messages = self._chat_history()
        bound = self.chain.bind(temperature=temperature)
        if max_tokens is not None:
            bound = bound.bind(max_tokens=max_tokens)
        response_content = bound.invoke({
            "system": self.conversation.system_prompt,
            "history": messages,
        })
        if save_response:
            self.add_message(response_content, "assistant", self.conversation.last_timestamp())
        return response_content

    def reset_messages(self):
        self.conversation.reset()


class SingleResponseAdvisor(Advisor):
    def __init__(self, system_prompt, valid_responses, model_size="big", temperature=0.0):
        super().__init__(system_prompt, model_size, temperature=temperature)
        self.valid_responses = valid_responses

    def decide(self, user_message = "", num_of_tries = 0):
        response = (self.get_response(user_message, max_tokens=32) or "").strip()
        if response not in self.valid_responses:
            if num_of_tries >= 3:
                return None
            mes = "Please reply with only one of the following: " + ", ".join(self.valid_responses) + "."
            return self.decide(mes, num_of_tries + 1)
        return response

class ExitAdvisor(SingleResponseAdvisor):
    def __init__(self, model_size="big", temperature=0.0):
        super().__init__(advisor_reply_line(EXIT_ADVISOR_VALID_RESPONSES), EXIT_ADVISOR_VALID_RESPONSES, model_size, temperature)
        self.pipe = load_exit_tuned_advisor()

    def decide(self, user_message="", num_of_tries=0):
        if user_message != "":
            self.add_message(user_message, "user", self.conversation.last_timestamp())
        response = tuned_exit_label(self.pipe, self._chat_history())
        if response not in self.valid_responses:
            return None
        return response


class JobTitleAdvisor(SingleResponseAdvisor):
    def __init__(self, jobs_list, model_size="big", temperature=0.0):
        system_prompt = JOB_TITLE_SYSTEM
        if len(jobs_list) > 0:
            system_prompt += "\n\n" + "Allowed job titles:\n" + "\n".join(jobs_list)
        super().__init__(system_prompt, ["Unknown"] + jobs_list, model_size, temperature=temperature)

        self.jobs_list = jobs_list

    def decide(self, user_message="", num_of_tries=0):
        response = (self.get_response(user_message, max_tokens=32) or "").strip()
        parsed = self.parse_job_title_reply(response)
        if parsed is not None:
            return parsed
        if num_of_tries >= 3:
            return None
        mes = "Reply with one allowed title, Unknown, or Not Offered: and the role they named."
        return self.decide(mes, num_of_tries + 1)

    def parse_job_title_reply(self, response):
        if response is None or response == "":
            line = ""
        else:
            line = response.strip()
        if line in self.jobs_list or line == "Unknown":
            return line
        prefix = "Not Offered:"
        if line.startswith(prefix) and line[len(prefix):].strip():
            return line
        return None