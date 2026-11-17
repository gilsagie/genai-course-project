import os
import sys
import chromadb
APP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
from modules.job.text import get_job_path, load_jobs_list
from modules.job.text import (
    get_path,
    build_job_description_chunks
)

PROJECT_ROOT = os.path.realpath(__file__)
for _ in range(3): # 3 levels up from chroma.py
    PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)
DEFAULT_CHROMA_PERSIST_DIR = os.path.join(PROJECT_ROOT, "data", "chroma_job_description")
COLLECTION_NAME = "job_descriptions"


def get_chroma_client(persist_directory):
    persist_dir = get_path(persist_directory, DEFAULT_CHROMA_PERSIST_DIR)
    os.makedirs(persist_dir, exist_ok=True)
    return chromadb.PersistentClient(path=str(persist_dir))

def _embedding_function():
    from dotenv import load_dotenv
    from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
    load_dotenv()
    return OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small",
    )


def get_job_description_collection(persist_directory=None):
    client = get_chroma_client(persist_directory)
    embedding = _embedding_function()
    try:
        return client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=embedding)
    except ValueError:
        client.delete_collection(COLLECTION_NAME)
        return client.get_or_create_collection(name=COLLECTION_NAME, embedding_function=embedding)



def embed_job_description_into_chroma(pdf_path, job_title, persist_directory=None, chunk_size=800, chunk_overlap=100):
    pdf_path = get_path(pdf_path, None)
    if pdf_path is None:
        raise ValueError("A job description PDF path is required")
    collection = get_job_description_collection(persist_directory)
    already = collection.get(where={"job": job_title}, include=[])
    if already["ids"]:
        return collection
    chunks = build_job_description_chunks(pdf_path, chunk_size, chunk_overlap)
    slug = "_".join(job_title.lower().split())
    documents = [str(chunk["text"]) for chunk in chunks]
    ids = [slug + "_" + str(chunk["id"]) for chunk in chunks]
    metadatas = [
        {
            "page": chunk["page"],
            "chunk": chunk["chunk"],
            "source": chunk["source"],
            "job": job_title,
        }
        for chunk in chunks
    ]
    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    return collection


def job_file_text(job_title, persist_directory=None):
    collection = get_job_description_collection(persist_directory)
    got = collection.get(where={"job": job_title})
    if not got["ids"]:
        raise ValueError(f"No documents for job {job_title}")
    rows = sorted(
        zip(got["metadatas"], got["documents"]),
        key=lambda row: (row[0]["page"], row[0]["chunk"]),
    )
    return "\n".join(doc for _, doc in rows if doc)

def query_job_description(job_title, question, persist_directory=None, n_results=None):
    collection = get_job_description_collection(persist_directory)
    ids = collection.get(where={"job": job_title}, include=[])["ids"]
    if not ids:
        raise ValueError(f"No documents for job {job_title}")
    if n_results is None:
        n_results = len(ids)
    results = collection.query(
        query_texts=[question],
        n_results=min(n_results, len(ids)),
        where={"job": job_title},
    )
    return "\n".join(doc for doc in results["documents"][0] if doc)

def embed_all_job_descriptions(persist_directory=None):
    for title in load_jobs_list():
        embed_job_description_into_chroma(get_job_path(title), title, persist_directory)

if __name__ == "__main__":
    embed_all_job_descriptions()