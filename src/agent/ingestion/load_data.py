import pandas as pd
import pymupdf
from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_csv(file_path: str) -> list[dict]:
    df = pd.read_csv(file_path)
    source = Path()(file_path).stem
    
    return [
        {
            "text": " | ".join(f"{col}: {val}" for col, val in row.items()),
            "source": source,
            "row_index": i
        }
        for i, (_, row) in enumerate(df.iterrows())
    ]
    
    
def load_pdf(file_path:str, chunksize: int = 500, chunk_overlap: int = 50) -> list[dict]:
    source = Path()(file_path).stem
    
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunksize,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = []
    for doc in splitter.split_documents(documents):
        if len(doc.page_content.strip()) < 40:
            continue
        chunks.append({
            "text":   doc.page_content.strip(),
            "page":   doc.metadata.get("page", 0) + 1,  
            "source": source,
        })
        
    return chunks
    
    
