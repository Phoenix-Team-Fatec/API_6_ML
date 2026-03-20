import pandas as pd
import re
from pathlib import Path

from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def _sanitize_text(text: str) -> str:
    """
    Remove caracteres problemáticos que podem causar NaN no embedding:
    - caracteres de controle
    - símbolos especiais perigosos
    - espaços múltiplos
    """
    # Remove caracteres de controle (exceto \n e \t)
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", " ", text)
    
    # Remove simbolos muito exóticos
    text = re.sub(r"[\u202a-\u202e\u2060-\u2064]", " ", text)
    
    # Normaliza espaços múltiplos
    text = re.sub(r"\s+", " ", text)
    
    return text.strip()


def _is_valid_chunk(text: str, min_length: int = 40) -> bool:
    """
    Rejeita chunks que causariam NaN no embedding:
    - muito curtos
    - só espaços/quebras de linha
    - só números e símbolos sem palavras reais
    - só caracteres especiais vindos do PDF
    """
    text = _sanitize_text(text)

    if len(text) < min_length:
        return False

    # remove espaços e quebras — se não sobrar nada, rejeita
    if not text.replace("\n", "").replace(" ", ""):
        return False

    # exige ao menos 10 caracteres alfabéticos (letras de verdade)
    letters = re.sub(r"[^a-zA-ZÀ-ÿ]", "", text)
    if len(letters) < 10:
        return False

    return True

        
def load_pdf(file_path:str, chunksize: int = 500, chunk_overlap: int = 50) -> list[dict]:
    source = Path(file_path).stem
    
    try:
        loader = PyMuPDFLoader(file_path)
        documents = loader.load()
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {file_path}")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunksize,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = []
    for doc in splitter.split_documents(documents):
        text = doc.page_content.strip()
        if _is_valid_chunk(text):
            chunks.append({
                "text":   _sanitize_text(text),
                "page":   doc.metadata.get("page", 0) + 1,  
                "source": source,
            })
        
    return chunks


def load_csv(file_path:str) -> list[dict]:
    df = pd.read_csv(file_path)
    df.fillna("", inplace=True)
    return df
    
    
