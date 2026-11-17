import os
import sys


APP_DIR = os.path.realpath(__file__)
for _ in range(2):
    APP_DIR = os.path.dirname(APP_DIR)
APP_DIR = os.path.join(APP_DIR, "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)

from datetime import timedelta
from modules.main_agent import MainAgent
from modules.chroma import embed_all_job_descriptions, get_job_description_collection
from tools import docker_is_on
import platform
from config import CHAT_START

import streamlit as st

def reset_chat():
    st.session_state.agent = MainAgent(model_size="big")
    st.session_state.agent.reset_messages()
    st.session_state.when = CHAT_START
    st.session_state.lines = []
    st.session_state.ended = False
    st.session_state.awaiting_reply = False

if platform.system() == "Darwin" and not docker_is_on():
    st.warning("Docker is off or tech-sql is stopped. Run: docker start tech-sql")

root = os.path.dirname(APP_DIR)
logo, title = st.columns([1, 6], vertical_alignment="center")
with logo:
    st.image(os.path.join(root, "assets", "logo.png"), width=80)
with title:
    st.title("Recruiter Chatbot")
st.write("A recruiting chat that finds the job, answers questions, and sets an interview or ends the chat.")

if "agent" not in st.session_state:
    reset_chat()

if "chroma_ready" not in st.session_state:
    if get_job_description_collection().count() == 0:
        embed_all_job_descriptions()
    st.session_state.chroma_ready = True

if st.button("New chat"):
    reset_chat()
    st.rerun()

for line in st.session_state.lines:
    with st.chat_message(line["role"]):
        st.write(line["content"])
if st.session_state.ended:
    st.write("Conversation ended.")
else:
    if st.session_state.awaiting_reply:
        with st.spinner("Thinking..."):
            reply, ended = st.session_state.agent.run()
        st.session_state.lines.append({"role": "assistant", "content": reply})
        st.session_state.awaiting_reply = False
        if ended:
            st.session_state.ended = True
        st.rerun()
        
    elif not st.session_state.ended:
        user_message = st.chat_input("Your message")
        if user_message:
            timestamp = st.session_state.when.strftime("%Y-%m-%dT%H:%M:%SZ")
            st.session_state.when += timedelta(minutes=1)
            st.session_state.lines.append({"role": "user", "content": user_message})
            st.session_state.agent.add_message(user_message, "user", timestamp)
            st.session_state.awaiting_reply = True
            st.rerun()