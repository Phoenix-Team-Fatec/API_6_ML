import mlflow

def setup_observability(
    tracking_uri: str = "http://localhost:5000",
    experiment_name: str = "agent-json-generation"
) -> None:
    """
    Configura o MLflow para observar o agente.
 
    - Define o tracking_uri (servidor MLflow local).
    - Define/cria o experimento onde os traces serão armazenados.
    - Ativa o autolog do LangChain, que captura automaticamente:
        * Cada nó do grafo como um span.
        * Chamadas de LLM (Groq, Google, HuggingFace).
        * Tool calls (buscar_regras_negocio, buscar_trecho_codigo).
    """
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)
    mlflow.langchain.autolog()