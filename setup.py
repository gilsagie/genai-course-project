import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

def read_env(path):
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if text == "" or text.startswith("#") or "=" not in text:
            continue
        key, value = text.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def venv_python():
    if platform.system() == "Windows":
        return ROOT / ".venv" / "Scripts" / "python.exe"
    return ROOT / ".venv" / "bin" / "python"


def require_env():
    example = ROOT / ".env.example"
    env_path = ROOT / ".env"
    if not env_path.is_file():
        shutil.copy(example, env_path)
    values = read_env(env_path)
    missing = []
    if values.get("OPENAI_API_KEY", "") == "":
        missing.append("OPENAI_API_KEY")
    if platform.system() == "Darwin" and values.get("MSSQL_SA_PASSWORD", "") == "":
        missing.append("MSSQL_SA_PASSWORD")
    if missing:
        print("Fill " + ", ".join(missing) + " in .env, then run python setup.py again.")
        sys.exit(1)
    return values


def install(py):
    if not py.is_file():
        subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")], check=True)
    subprocess.run([str(py), "-m", "pip", "install", "-r", "requirements.txt"], check=True)


def docker_running():
    result = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", "tech-sql"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def wait_for_sql():
    deadline = time.time() + 180
    while time.time() < deadline:
        logs = subprocess.run(["docker", "logs", "tech-sql"], capture_output=True, text=True)
        text = logs.stdout + logs.stderr
        if "SQL Server is now ready for client connections" in text:
            return
        time.sleep(5)
    print("SQL Server did not become ready. Check docker logs tech-sql.")
    sys.exit(1)


def start_sql(password):
    if docker_running():
        return
    exists = subprocess.run(["docker", "inspect", "tech-sql"], capture_output=True)
    if exists.returncode == 0:
        subprocess.run(["docker", "start", "tech-sql"], check=True)
    else:
        env = os.environ.copy()
        env["MSSQL_SA_PASSWORD"] = password
        subprocess.run(
            [
                "docker", "run",
                "-e", "ACCEPT_EULA=Y",
                "-e", "MSSQL_SA_PASSWORD",
                "-p", "1433:1433",
                "--name", "tech-sql",
                "--platform", "linux/amd64",
                "-d",
                "mcr.microsoft.com/mssql/server:2022-latest",
            ],
            env=env,
            check=True,
        )
    wait_for_sql()

def main():
    values = require_env()
    py = venv_python()
    install(py)
    if platform.system() == "Darwin":
        start_sql(values["MSSQL_SA_PASSWORD"])
    subprocess.run([str(py), "app/modules/schedule_database_creator.py"], check=True)
    if platform.system() == "Windows":
        print(r"Activate with .venv\Scripts\activate")
    else:
        print("Activate with source .venv/bin/activate")
    print("Then run: streamlit run streamlit_app/streamlit_main.py")


if __name__ == "__main__":
    main()