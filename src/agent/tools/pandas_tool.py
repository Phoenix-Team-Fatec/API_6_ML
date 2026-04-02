import pandas as pd
import traceback
from functools import lru_cache

from langchain.tools import tool
from src.agent.rag.retriever import Retriever
from src.agent.rag.vector_store import VectorStore
from src.agent.editing.code_editor import CodeEditor
from src.agent.prompts.pandas_prompt import PANDAS_PROMPT

CSV_RH_PATH = "src/data/preprocessed/rh_25.csv"
CSV_VENDAS_PATH = "src/data/preprocessed/vendas_25.csv"
CSV_COMISSAO_PATH = "src/data/preprocessed/comissao_25.csv"


@lru_cache(maxsize=1)
def load_csv_data() -> list[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rh_df = pd.read_csv(CSV_RH_PATH)
    vendas_df = pd.read_csv(CSV_VENDAS_PATH)
    comissao_df = pd.read_csv(CSV_COMISSAO_PATH)
    return rh_df, vendas_df, comissao_df


    