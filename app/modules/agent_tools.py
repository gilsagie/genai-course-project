from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from tools import load_model
from datetime import datetime
from config import SMS_DATE_FORMAT, DATE_FORMAT, SLOT_DATE_FORMAT
from modules.scheduler import closest_dates, schedule_time
from modules.chroma import query_job_description

@tool
def offer_interview_slots(schedule_code: str, message_time: str, position: str) -> str:
    """
    Return the three nearest interview times as one phrase.

    schedule_code is NOW, or weeks,day, or weeks,day,HH:MM. Monday is 0.
    message_time is the last SMS time, like 2024-04-03T15:12:00Z.
    """
    when_message = datetime.strptime(message_time, SMS_DATE_FORMAT)
    when = schedule_time(schedule_code, when_message)
    now = when_message.strftime(DATE_FORMAT)
    dates = closest_dates(when.strftime(DATE_FORMAT), now, position)
    if not dates:
        return "No interview times are open."
    slots = []
    for date in dates:
        slot = datetime.strptime(date, SLOT_DATE_FORMAT)
        hour = slot.strftime("%I").lstrip("0")
        clock = hour + " " + slot.strftime("%p")
        slots.append(slot.strftime("%A, %B") + " " + str(slot.day) + " at " + clock)
    times = ", ".join(slots[:-1]) + ", or " + slots[-1]
    return times

@tool
def read_job_description(job_title: str, question: str) -> str:
    """Return the passages from this job file closest to the question."""
    return query_job_description(job_title, question, n_results=2)

def prompt_template(system_prompt):
    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

def build_lookup_executor(tools, prompt, model_size="big"):
    llm, _ = load_model(model_size)
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools)