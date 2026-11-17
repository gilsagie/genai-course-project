import os

from pypdf import PdfReader

PROJECT_ROOT = os.path.realpath(__file__)
for _ in range(4):
    PROJECT_ROOT = os.path.dirname(PROJECT_ROOT)
DEFAULT_DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
DEFAULT_FILES_DIR = os.path.join(PROJECT_ROOT, "app", "files")



def get_path(path, default):
    if path is None:
        return default
    resolved = path
    if not os.path.isabs(path):
        resolved = os.path.join(PROJECT_ROOT, resolved)
    return resolved


def _chunk_text(text, chunk_size, chunk_overlap):
    text = text.strip()
    if not text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and smaller than chunk_size")

    chunks = []
    start = 0
    while start < len(text):
        piece = text[start : start + chunk_size].strip()
        if piece:
            chunks.append(piece)
        if start + chunk_size >= len(text):
            break
        start += chunk_size - chunk_overlap
    return chunks


def _extract_pdf_pages(pdf_path):
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"Job description PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))
    pages = []
    for page_index, page in enumerate(reader.pages):
        pages.append((page_index, (page.extract_text() or "").strip()))
    return pages


def build_job_description_chunks(pdf_path, chunk_size=800, chunk_overlap=100):

    pdf_path = get_path(pdf_path, None)
    if pdf_path is None:
        raise ValueError("A job description PDF path is required")
    chunks = []
    for page_index, page_text in _extract_pdf_pages(pdf_path):
        for chunk_index, chunk in enumerate(_chunk_text(page_text, chunk_size, chunk_overlap)):
            chunks.append(
                {
                    "id": f"page_{page_index}_chunk_{chunk_index}",
                    "page": page_index,
                    "chunk": chunk_index,
                    "source": os.path.basename(pdf_path),
                    "text": chunk,
                }
            )
    if not chunks:
        raise ValueError(f"No text extracted from PDF: {pdf_path}")
    return chunks

def get_job_path(job):
    return os.path.join(DEFAULT_DOCS_DIR, f"{job} Job Description.pdf")

def load_jobs_list():
    jobs_list = []
    suffix = " Job Description.pdf"
    for file in os.listdir(DEFAULT_DOCS_DIR):
        if file.endswith(suffix):
            jobs_list.append(file[:-len(suffix)])
    return sorted(jobs_list)
