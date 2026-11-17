from peft import LoraConfig
from trl import SFTConfig, SFTTrainer
BASE_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

RANK = 32
ALPHA = 32

TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj"]
DROPOUT = 0.0
LEARNING_RATE = 2e-4
EPOCHS = 5
BATCH_SIZE = 4

def get_peft_config(rank=None, alpha=None):
    peft_config = LoraConfig(
        task_type="CAUSAL_LM",
        r=RANK if rank is None else rank,
        lora_alpha=ALPHA if alpha is None else alpha,
        lora_dropout=DROPOUT,
        bias="none",
        target_modules=list(TARGET_MODULES),
    )
    return peft_config

def get_args(epochs=None):
    args = SFTConfig(
        output_dir="fine_tuning/out",
        num_train_epochs=EPOCHS if epochs is None else epochs,
        per_device_train_batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        logging_steps=10,
        save_strategy="no",
        report_to="none",
    )
    return args

def get_trainer(train_data, rank, alpha, epochs=None):
    trainer = SFTTrainer(
        model=BASE_MODEL,
        args=get_args(epochs),
        train_dataset=train_data,
        peft_config=get_peft_config(rank, alpha),
    )
    return trainer