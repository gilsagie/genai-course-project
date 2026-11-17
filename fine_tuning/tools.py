import json
from tqdm import tqdm
import os
import sys


TRAIN_TEST_FILES_DIR = "fine_tuning/train_test_files"

APP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
from config import EXIT_ADVISOR_VALID_RESPONSES, SCHEDULING_ADVISOR_VALID_RESPONSES, INFO_ADVISOR_VALID_RESPONSES

def normalize(text, labels):
    """Pull one of our valid labels out of the model's answer"""
    ordered = sorted(labels, key=len, reverse=True)
    for label in ordered:
        if label.lower() in text.lower():
            return label
    return text.strip()

def grade(prediction, correct_label):
    """string_check - operation: eq"""
    return prediction == correct_label

def evaluate(pipe, test_data, labels):
    correct = 0
    for item in tqdm(test_data, desc="Evaluating"):
        output = pipe(item["messages"], max_new_tokens=20, do_sample=False, return_full_text=False, continue_final_message=False)
        new_text = output[0]["generated_text"]
        prediction = normalize(new_text, labels)
        correct_label = item["label"]
        cuurent_grade = grade(prediction, correct_label)
        print(prediction, correct_label, cuurent_grade)
        if cuurent_grade:
            correct += 1
    accuracy = 100 * correct / len(test_data)
    print(f"accuracy: {accuracy:.1f}%")
    return accuracy

def load_test_data(file_path):
    test_data = []
    with open(file_path, encoding="utf-8") as f:
        for line in tqdm(f, desc="Loading test data"):
            if line.strip():
                messages = json.loads(line)["messages"]
                test_data.append({
                    "messages": messages[:-1],
                    "label": messages[-1]["content"],
                })
    return test_data

def get_file_path(advisor_type, train_or_test):
    if train_or_test != "train" and train_or_test != "test":
        raise ValueError("train_or_test must be 'train' or 'test'")
    return os.path.join(TRAIN_TEST_FILES_DIR, f"{advisor_type}_{train_or_test}.jsonl")

def get_labels(advisor_type):
    if advisor_type == "exit":
        return EXIT_ADVISOR_VALID_RESPONSES
    elif advisor_type == "scheduling":
        return SCHEDULING_ADVISOR_VALID_RESPONSES
    elif advisor_type == "info":
        return INFO_ADVISOR_VALID_RESPONSES