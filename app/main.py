from modules.main_agent import MainAgent
from modules.chroma import embed_all_job_descriptions

def main():
    embed_all_job_descriptions()
    main_agent = MainAgent(model_size="big")
    main_agent.chat()

if __name__ == "__main__":
    main()