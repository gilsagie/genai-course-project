import os
from dotenv import load_dotenv
from transformers import pipeline
from transformers.utils import logging
import sys
from tools import get_file_path
from lora import get_trainer, BASE_MODEL
from datasets import load_dataset
from transformers import AutoTokenizer

APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
from config import HUGGING_FACE_MODEL_SMALL

def get_hugging_face_client():
    load_dotenv()
    hf_token = os.getenv("HF_TOKEN")

    logging.set_verbosity_error()

    model_name = HUGGING_FACE_MODEL_SMALL
    return pipeline("text-generation", model=model_name, token=hf_token)


def fine_tune(advisor_type, rank=None, alpha=None, epochs=None, save_dir=None):
    train_path = get_file_path(advisor_type, "train")
    train_data = load_dataset("json", data_files=train_path, split="train")
    trainer = get_trainer(train_data, rank, alpha, epochs)
    trainer.train()
    saved = f"data/tuned/{advisor_type}_model" if save_dir is None else save_dir
    merged_model = trainer.model.merge_and_unload()
    merged_model.save_pretrained(saved)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.save_pretrained(saved)
    return pipeline("text-generation", model=saved)

def train_advisor(advisor):
    fine_tune(advisor)

def main():
    train_advisor("exit")

if __name__ == "__main__":
    main()