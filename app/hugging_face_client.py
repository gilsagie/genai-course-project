from transformers import pipeline
from transformers.utils import logging
import os
from config import HUGGING_FACE_MODELS
from dotenv import load_dotenv
from config import EXIT_ADVISOR_VALID_RESPONSES, advisor_reply_line
import streamlit as st


EXIT_TUNED_SYSTEM = advisor_reply_line(EXIT_ADVISOR_VALID_RESPONSES)

EXIT_TUNED_MODEL = "gilsagie/qwen-exit-advisor"

EXIT_TUNED_LABELS = EXIT_ADVISOR_VALID_RESPONSES

@st.cache_resource
def load_exit_tuned_advisor():
    logging.set_verbosity_error()
    load_dotenv()
    folder = EXIT_TUNED_MODEL
    return pipeline("text-generation", model=folder)

def tuned_exit_label(pipe, history):
    messages = [{"role": "system", "content": EXIT_TUNED_SYSTEM}] + history
    output = pipe(messages, max_new_tokens=20, do_sample=False, return_full_text=False, continue_final_message=False)
    new_text = output[0]["generated_text"]
    labels = sorted(EXIT_TUNED_LABELS, key=len, reverse=True)
    for label in labels:
        if label.lower() in new_text.lower():
            return label
    return new_text.strip()

def get_hugging_face_client():
    load_dotenv()
    HF_TOKEN = os.getenv("HF_TOKEN")

    logging.set_verbosity_error()

    size = "MEDIUM"
    MODEL_NAME = HUGGING_FACE_MODELS[size]
    return pipeline("text-generation", model=MODEL_NAME, token=HF_TOKEN)


if __name__ == "__main__":
    client = get_hugging_face_client()
    output = client("Hello, how are you?", max_new_tokens=50, do_sample=False)
    print(output[0]["generated_text"])

