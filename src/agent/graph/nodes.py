import json
from langchain.messages import SystemMessage, AIMessage, ToolMessage
from langgraph.prebuilt import ToolNode
from pydantic import ValidationError

from src.agent.graph.state import State
from src.agent.graph.code_generator import CodeGeneratorModels 
from src.agent.prompts.prompt_builder import build_edit_prompt
from src.agent.tools.rag_code_tool import buscar_regras_negocio
from src.agent.tools.rag_rules_tool import buscar_trecho_codigo
from src.agent.prompts.system_promt import SYSTEM_PROMPT
from src.agent.models.outputs import RespostaAgente

TOOLS = [
    buscar_regras_negocio,
    buscar_trecho_codigo,
]

def build_agent_node(provider: str = 'groq'):
    """
    Retorna o nó do agente ReAct com as tools vinculadas.
    O agente decide ciclicamente quais tools chamar antes de
    passar ao code_editor.
    """
    editor = CodeGeneratorModels()
    if provider == 'groq':
        llm = editor.ollama_model()
    else:
        llm = editor.ollama_model()
    llm_with_tools = llm.bind_tools(TOOLS)
    
    def agent_node(state: State) -> State:
        print("> Agent Node")    
        messages = state["messages"]
        
        if state.get('iteration', 0) == 0:
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
            
        response = llm_with_tools.invoke(messages)
        has_tool_calls = hasattr(response, 'tool_calls') and response.tool_calls
        content = (response.content or "") if hasattr(response, "content") else ""
        is_ready = content.strip() == "PRONTO_PARA_EDITAR"

        if not has_tool_calls and not is_ready:
            correction = SystemMessage(content=(
                "Você deve chamar uma tool para buscar contexto "
                "OU responder exatamente 'PRONTO_PARA_EDITAR'. "
                "Nenhuma outra resposta é aceita."
            ))
            return {
                "messages": [response, correction],
                "iteration": state.get("iteration", 0) + 1,
                "agent_blocked": False,
            }

        return {
            "messages": [response],
            "iteration": state.get('iteration', 0) + 1,
            "agent_blocked": False,
            "agent_errors": [],
        }
    
    return agent_node
    

def build_code_editor_node() -> State:
    """
    Nó especializado que recebe todo o contexto acumulado
    e gera o código Python final com a alteração.
    """
    editor = CodeGeneratorModels()
    llm = editor.ollama_model()
    prompt = build_edit_prompt()
    chain = prompt | llm
    
    def code_editor_node(state: State) -> State:
        print("> Code Editor Node")
        context = _extrair_contexto_das_mensagens(state["messages"])
        
        response = chain.invoke({
            "user_request": state["user_request"],
            "rules_context": context.get("rules", state.get('rules_context', '')),
            "code_context": context.get("code", state.get('code_context', '')),
        }) 
        
        generated = response.content if hasattr(response, 'content') else str(response)
        
        return {
            'raw_output': generated,
            'generated_code': generated,
            'messages': [AIMessage(content=f'Código gerado:{generated}\n')]
        }
        
    return code_editor_node


def build_review_node():
    """
    Valida o JSON gerado pelo code_editor contra o schema RespostaAgente.
    Popula review_errors no estado em caso de falha para retry ou escalação.
    """
    def review_node(state: State) -> State:
        print('> review node')
        raw = state.get("raw_output", "")
        errors: list[str] = []
        validated: RespostaAgente | None = None
        review_attempts = state.get("review_attempts", 0)
        
        # Verificar se ha conteudo
        if not raw.strip():
            errors.append("O modelo retornou uma resposta vazia")
            return {
                "review_errors": errors,
                "validated_output": None,
                "review_attempts": review_attempts + 1,
            }
        
        # Parse do JSON
        try:
            data = json.loads(_limpar_json(raw))
        except json.JSONDecodeError as e:
            errors.append(f"JSON inválido: {str(e)}")
            return {
                "review_errors": errors,
                "validated_output": None,
                "review_attempts": review_attempts + 1,
            }
        
        # Validacao do schema PyDantic
        try:
            validated = RespostaAgente.model_validate(data)
        except ValidationError as e:
            for err in e.errors():
                campo = " → ".join(str(c) for c in err["loc"])
                errors.append(f"Campo '{campo}': {err['msg']}")
            return {
                "review_errors": errors,
                "validated_output": None,
                "review_attempts": review_attempts + 1,
            }

        # Validacao de negocio adicionais 
        errors.extend(_validar_regras_negocio(validated))
        
        if errors:
            return {
                "review_errors": errors,
                "validated_output": None,
                "review_attempts": review_attempts + 1,
            }
        return {
            "review_errors": [],
            "validated_output": validated,
            "review_attempts": review_attempts,
        }
        
    return review_node

def _extrair_contexto_das_mensagens(messages: list) -> dict:
    context = {"rules": "", "code": ""}
    
    for msg in messages:
        if isinstance(msg, ToolMessage):
            name = msg.name or ""
            if "regra" in name or "rules" in name:
                context["rules"] += f"{msg.content}\n"
            elif "codigo" in name or "code" in name:
                context["code"] += f"{msg.content}\n"
            else:
                context["rules"] += f"{msg.content}\n"
    
    return context


def _limpar_json(raw: str) -> str:
    """Remove blocos markdown caso o modelo os inclua mesmo instruído a não."""
    raw = raw.strip()
    if "Codigo gerado:" in raw:
        raw = raw.split("Codigo gerado:", 1)[1].strip()
    if "Código gerado:" in raw:
        raw = raw.split("Código gerado:", 1)[1].strip()
    if raw.startswith("```"):
        linhas = raw.splitlines()
        raw = "\n".join(
            l for l in linhas
            if not l.strip().startswith("```")
        ).strip()
    # Mantem somente o bloco JSON entre o primeiro '{' e o ultimo '}'
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        raw = raw[start:end + 1]
    return raw


def _validar_regras_negocio(resposta: RespostaAgente) -> list[str]:
    """Validações de domínio que o Pydantic não consegue verificar sozinho."""
    errors: list[str] = []

    if resposta.tipo == "override" and resposta.override:
        ov = resposta.override

        for chave, perc in ov.perc_override.items():
            # Percentual suspeito: provavelmente veio como decimal (0.0175)
            if perc < 0.1:
                errors.append(
                    f"perc_override['{chave}'] = {perc} parece estar em formato "
                    f"decimal. O esperado é o valor absoluto, ex: 1.75"
                )
            if perc > 100:
                errors.append(
                    f"perc_override['{chave}'] = {perc} excede 100%. Verifique o valor."
                )

        # Vigência não pode ultrapassar 3 meses (regra de negócio)
        delta = (ov.data_fim - ov.data_inicio).days
        if delta > 92:
            errors.append(
                f"Vigência de {delta} dias excede o máximo permitido de 92 dias "
                f"para regras sazonais."
            )

    if resposta.tipo == "intercorrencia" and resposta.intercorrencias:
        for ic in resposta.intercorrencias:
            if ic.valor <= 0:
                errors.append(
                    f"Matrícula '{ic.matricula}': valor {ic.valor} deve ser positivo."
                )

    return errors


tools_node = ToolNode(TOOLS)
