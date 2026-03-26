from langchain_ollama import ChatOllama
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from src.agent.config.settings import settings
from src.agent.editing.schemas import CodeEditProposal
from src.agent.editing.prompt_builder import build_edit_prompt


class CodeEditor:
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

    def propose_edit(
        self,
        user_request: str,
        rules_context: str,
        code_context: str,
    ) -> CodeEditProposal:
        prompt = build_edit_prompt(
            user_request=user_request,
            rules_context=rules_context,
            code_context=code_context,
        )

        structured_llm = self.ollama_llm.with_structured_output(CodeEditProposal)
        return structured_llm.invoke(prompt)