import os
import sys
from dotenv import load_dotenv
from huggingface_hub import HfApi, whoami

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from fine_tune import get_hugging_face_client, fine_tune
from tools import evaluate, get_labels, load_test_data, get_file_path

SWEEP_ROOT = "fine_tuning/out/sweep"
EPOCHS = (3, 5, 10)
RANK = (8, 16, 32)
ALPHA_SCALE = (0.5, 1, 2)

ADVISOR_TYPE = "exit"

def score(pipe, test_data):
    accuracy = evaluate(pipe, test_data, get_labels(ADVISOR_TYPE))
    total = len(test_data)
    correct = round(accuracy * total / 100)
    return accuracy, correct, total


def print_best(loras):
    best = max(loras, key=lambda row: row["accuracy"])
    print(f"best epochs={best['epochs']}\n rank={best['rank']}\n alpha={best['alpha']}\n accuracy={best['accuracy']:.1f}%")

def main():
    test_data = load_test_data(get_file_path(ADVISOR_TYPE, "test"))
    pipe = get_hugging_face_client()
    accuracy, correct, total = score(pipe, test_data)
    base_results = {"accuracy": accuracy, "correct": correct, "total": total}
    del pipe
    loras = []
    for epochs in EPOCHS:
        for rank in RANK:
            for scale in ALPHA_SCALE:
                alpha = int(rank * scale)
                folder = os.path.join(SWEEP_ROOT, f"e{epochs}_r{rank}_a{alpha}")
                os.makedirs(folder, exist_ok=True)
                pipe = fine_tune(ADVISOR_TYPE, rank=rank, alpha=alpha, epochs=epochs, save_dir=folder)
                accuracy, correct, total = score(pipe, test_data)
                loras.append({"epochs": epochs, "rank": rank, "alpha": alpha, "accuracy": accuracy, "correct": correct, "total": total})
                del pipe
    print(f"base accuracy={base_results['accuracy']:.1f}%")
    print_best(loras)
    best = max(loras, key=lambda row: row["accuracy"])
    folder = os.path.join(SWEEP_ROOT, f"e{best['epochs']}_r{best['rank']}_a{best['alpha']}")
    upload_model(folder)

def upload_model(folder):
    load_dotenv()
    token = os.getenv("HF_TOKEN")
    username = whoami(token=token)["name"]
    repo_id = f"{username}/qwen-exit-advisor"
    api = HfApi(token=token)
    api.create_repo(repo_id, repo_type="model", private=True, exist_ok=True)
    api.upload_folder(
        folder_path=folder,
        repo_id=repo_id,
        repo_type="model",
        commit_message="Upload merged exit advisor",
    )
    print(f"Model uploaded to {repo_id}")
if __name__ == "__main__":
    main()