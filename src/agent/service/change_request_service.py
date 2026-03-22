from src.agent.editing.code_editor import CodeEditor
from src.agent.editing.patcher import apply_full_file_update
from src.agent.editing.validators import validate_python_code, validate_target_file_exists
from src.agent.rag.code_retriever import CodeRetriever
from src.agent.rag.retriever import Retriever
from src.agent.rag.vector_store import VectorStore


class ChangeRequestService:
    def __init__(self):
        self.store = VectorStore()
        self.rules_retriever = Retriever(self.store)
        self.code_retriever = CodeRetriever(self.store)
        self.editor = CodeEditor()

    def process_change_request(self, user_request: str, dry_run: bool = True) -> dict:
        rules_context = self.rules_retriever.get_context(user_request)
        code_context = self.code_retriever.get_context(user_request)

        proposal = self.editor.propose_edit(
            user_request=user_request,
            rules_context=rules_context,
            code_context=code_context,
        )

        validate_target_file_exists(proposal.target_file)
        clean_code = validate_python_code(proposal.updated_code)

        diff = apply_full_file_update(
            target_file=proposal.target_file,
            updated_code=clean_code,
            dry_run=dry_run,
        )

        return {
            "target_file": proposal.target_file,
            "change_summary": proposal.change_summary,
            "diff": diff,
            "dry_run": dry_run,
        }