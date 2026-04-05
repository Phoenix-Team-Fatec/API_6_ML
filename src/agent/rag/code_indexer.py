from pathlib import Path
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_codebase(root_path: str, chunksize: int = 800, chunk_overlap: int = 120, extensions: tuple[str, ...] = (".py",)) -> list[dict]:
    root = Path(root_path)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = chunksize,
        chunk_overlap = chunk_overlap,
        separators=["\nclass ", "\ndef ", "\n\n", "\n", " ", ""],
    )

    chunks: List[dict] = []


    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix not in extensions:
            continue

        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception:
            continue

        split_texts = splitter.split_text(content)

        for i, chunk in enumerate(split_texts):
            if not chunk.strip():
                continue
            
            chunks.append(
                {
                    "text": chunk,
                    "file_path": str(file_path),
                    "chunk_id": i,
                    "language": file_path.suffix.lstrip("."),
                }
            )

    return chunks