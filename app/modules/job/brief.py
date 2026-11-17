import os
from modules.job.text import DEFAULT_FILES_DIR


def job_brief_path(job):
    return os.path.join(DEFAULT_FILES_DIR, f"{job} job_brief.json")
