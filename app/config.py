from datetime import datetime
def advisor_reply_line(labels):
    return f"Reply with only one line: {labels[0]} or {labels[1]}."



CHAT_START = datetime(2024, 4, 3, 15, 12, 0)

# OPENAI MODELS
OPENAI_MODEL_BIG="gpt-4.1-2025-04-14"
OPENAI_MODEL_MEDIUM="gpt-4.1-mini-2025-04-14"
OPENAI_MODEL_SMALL="gpt-5-nano"

# HUGGING FACE MODELS
HUGGING_FACE_MODEL_HUGE="openai/gpt-oss-20b"
HUGGING_FACE_MODEL_BIG="Qwen/Qwen2.5-7B-Instruct"
HUGGING_FACE_MODEL_MEDIUM="Qwen/Qwen2.5-3B-Instruct"
HUGGING_FACE_MODEL_SMALL="Qwen/Qwen2.5-0.5B-Instruct"
HUGGING_FACE_MODELS = {
    "HUGE": HUGGING_FACE_MODEL_HUGE,
    "BIG": HUGGING_FACE_MODEL_BIG,
    "MEDIUM": HUGGING_FACE_MODEL_MEDIUM,
    "SMALL": HUGGING_FACE_MODEL_SMALL,
}

# MODELS
MODELS = {
    "OPENAI_MODEL_BIG": OPENAI_MODEL_BIG,
    "OPENAI_MODEL_MEDIUM": OPENAI_MODEL_MEDIUM,
    "OPENAI_MODEL_SMALL": OPENAI_MODEL_SMALL,
}

# X[0] is the positive response, X[1] is the negative response
EXIT_ADVISOR_VALID_RESPONSES = ["End Conversation", "Don't End Conversation"]
SCHEDULING_ADVISOR_VALID_RESPONSES = ["Schedule Interview", "Don't Schedule Interview"]
INFO_ADVISOR_VALID_RESPONSES = ["Info Needed", "Info Not Needed"]

POSITIVE_VALID_RESPONSES = {
    "end": EXIT_ADVISOR_VALID_RESPONSES[0],
    "schedule": SCHEDULING_ADVISOR_VALID_RESPONSES[0],
    "info": INFO_ADVISOR_VALID_RESPONSES[0],
}

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
SMS_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
SLOT_DATE_FORMAT = "%Y-%m-%d %H:%M"