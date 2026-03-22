from langchain_ollama import ChatOllama
from src.agent.config.settings import settings
from src.agent.editing.schemas import CodeEditProposal
from src.agent.editing.prompt_builder import build_edit_prompt


class CodeEditor:
    def __init__(self):
        self.llm = ChatOllama(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
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

        structured_llm = self.llm.with_structured_output(CodeEditProposal)
        return structured_llm.invoke(prompt)