from src.agent.editing.code_editor import CodeEditor
from src.agent.editing.prompt_builder import build_edit_prompt
from src.agent.rag.retriever import Retriever
from src.agent.rag.code_retriever import CodeRetriever
from src.agent.rag.vector_store import VectorStore

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

class Chains():
    def __init__(self):
        self.code_editor = CodeEditor()
        self.prompt = build_edit_prompt()
        self.vector_store = VectorStore()
        self.rules_retriever = Retriever(store=self.vector_store)
        self.code_retriever = CodeRetriever(store=self.vector_store)
        
        
    def edit_chain(self, model_type:str = "hf"):
        model = {
            "hf": self.code_editor.hf_model(),
            "ollama": self.code_editor.ollama_model()
        }
        
        llm = model[model_type]
        
        rag_chain = (
            RunnablePassthrough.assign(
                rules_context=RunnableLambda(lambda x: self.rules_retriever.get_context(x["input"])),
                code_context=RunnableLambda(lambda x: self.code_retriever.get_context(x["input"])),
                user_request= lambda x: x["input"]
            )
            | self.prompt
            | llm
            | StrOutputParser()
        )
        
        return rag_chain
         
        
        
        
        