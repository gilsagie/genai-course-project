from dotenv import load_dotenv
import os
from config import MODELS
from langchain_openai import ChatOpenAI
import subprocess

def load_model(model_size = 'medium'):
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    openai_model = MODELS["OPENAI_MODEL" + "_" + model_size.upper()]
    openai_client = ChatOpenAI(model=openai_model, api_key=api_key)
    return openai_client, openai_model
        

def docker_is_on():
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", "tech-sql"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() == "true"