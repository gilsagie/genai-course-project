import os

from prompts import INFO_ADVISOR_SYSTEM
from config import INFO_ADVISOR_VALID_RESPONSES
from prompts import INFO_EXECUTOR_SYSTEM, JOB_BRIEF_SYSTEM
from modules.job.brief import job_brief_path
from modules.advisors.base import SingleResponseAdvisor, one_time_advisor
from modules.agent_tools import build_lookup_executor, read_job_description, prompt_template
from modules.chroma import job_file_text


class InfoAdvisor(SingleResponseAdvisor):
    def __init__(self, job, model_size="big", temperature=0.0):
        super().__init__(INFO_ADVISOR_SYSTEM, INFO_ADVISOR_VALID_RESPONSES, model_size, temperature)
        self.job = job
        self.question = ""
        self.executor = build_lookup_executor([read_job_description], prompt_template(INFO_EXECUTOR_SYSTEM), self.model_size)

    def set_job(self, job):
            self.job = job

    def create_job_description(self):
        path = job_brief_path(self.job.title)
        if os.path.isfile(path):
            description = open(path, encoding="utf-8").read()
        else:
            text = job_file_text(self.job.title)
            messages = [{"role": "user", "content": text, "timestamp": None}]
            description = one_time_advisor(JOB_BRIEF_SYSTEM, messages, model_size=self.model_size)
        self.job.set_description(description)
        return description
    
    def reset_question(self):
        self.question = ""

    def set_question(self, question):
        self.question = question

    def ask_question(self, question = ""):
        if question != "":
            self.set_question(question)
        result = self.executor.invoke({
            "input": "job_title: " + self.job.title + "\nquestion: " + self.question,
            "chat_history": self.conversation.get_history(with_system=False),
        })
        return result["output"]

    def decide(self, user_message="", num_of_tries=0):
        if num_of_tries == 0:
            self.set_question(user_message if user_message != "" else self.conversation.messages[-1].content)
        return super().decide(user_message, num_of_tries)

    def reset_messages(self):
        self.reset_question()
        super().reset_messages()