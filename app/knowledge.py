from pathlib import Path
import re

from docx import Document
from pypdf import PdfReader


def extract_text_from_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix in {".txt", ".md", ".csv", ".json", ".log", ".xml", ".yaml", ".yml"}:
        return file_path.read_text(encoding="utf-8", errors="ignore")

    if suffix == ".pdf":
        reader = PdfReader(str(file_path))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    if suffix == ".docx":
        document = Document(str(file_path))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    raise ValueError(f"Unsupported file type: {suffix}")


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 180) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0

    while start < len(normalized):
        end = min(len(normalized), start + chunk_size)
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(0, end - overlap)

    return chunks


def build_search_query(user_text: str, max_terms: int = 8) -> str:
    terms = re.findall(r"[A-Za-z0-9]{3,}", user_text.lower())
    unique_terms: list[str] = []

    for term in terms:
        if term not in unique_terms:
            unique_terms.append(term)
        if len(unique_terms) >= max_terms:
            break

    if not unique_terms:
        return ""

    return " OR ".join(unique_terms)


def format_knowledge_context(results: list[dict]) -> str:
    if not results:
        return ""

    lines = [
        "Knowledge snippets from uploaded attachments:",
    ]

    for idx, row in enumerate(results, start=1):
        doc_name = row.get("original_name") or "Uploaded document"
        snippet = (row.get("content") or "").strip()
        lines.append(f"{idx}. Source: {doc_name} | Snippet: {snippet}")

    return "\n".join(lines)
