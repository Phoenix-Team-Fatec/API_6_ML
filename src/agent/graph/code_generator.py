from langchain_ollama import ChatOllama
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain.chat_models import init_chat_model, BaseChatModel
from src.agent.config.settings import settings

class CodeGeneratorModels:
    def __init__(self):
        self.ollama_llm = settings.llm_model
        self.huggingface_llm = settings.hugging_face_model
        self.temperature = settings.llm_temperature
      
    def hf_model(self) -> ChatHuggingFace:
        llm = HuggingFaceEndpoint(
            repo_id=self.huggingface_llm,
            temperature=self.temperature,
            return_full_text=False,
            max_new_tokens=4096,
            task="text-generation",
            huggingfacehub_api_token=settings.huggingfacehub_api_token
        )
        
        chat_model = ChatHuggingFace(llm=llm)
        
        return chat_model
    
    def ollama_model(self) -> ChatOllama:
        return ChatOllama(
            model=self.ollama_llm,
            temperature=self.temperature,
        )

    def google_genai_model(self) -> BaseChatModel:
        return init_chat_model(f"google_genai:{settings.google_model}")
    
    def groq_model(self) -> BaseChatModel:
        return init_chat_model(f"groq:{settings.groq_model}")

