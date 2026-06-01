"""
Dataset de avaliação do agente.

Cobertura mínima (intencionalmente pequeno para facilitar iteração):
- Casos de override (regras por marca/cargo)
- Casos de intercorrência (bônus por matrícula)

Cada item do dataset tem:
- inputs: o que é passado para o grafo (chaves devem bater com os kwargs
  esperados pela predict_fn)
- expectations: o que esperamos validar com os scorers
- tags: categorização livre para agrupar na UI do MLflow
"""
EVAL_DATASET = [
    # --- Intercorrência: bônus fixo por matrícula ---
    {
        "inputs": {
            "user_request": (
                "Os funcionários MATRIC-227, MATRIC-139 e MATRIC-400 receberam "
                "um bônus fixo de R$20.000 por tempo de casa, a ser acrescido "
                "na base de cálculo de vendas para efeito de comissionamento "
                "em abril de 2025."
            ),
        },
        "expectations": {
            "expected_type": "intercorrencia",
            "max_iterations": 6,
        },
        "tags": {"category": "intercorrencia", "subtype": "bonus_fixo"},
    },
    # --- Override: percentual por marca/cargo ---
    {
        "inputs": {
            "user_request": (
                "O percentual de comissão da marca 10 no cargo 300 deve subir "
                "para 1,75% durante o mês de abril de 2025."
            ),
        },
        "expectations": {
            "expected_type": "override",
            "max_iterations": 6,
        },
        "tags": {"category": "override", "subtype": "perc_override"},
    },
    # --- Override: redirecionamento de marca ---
    {
        "inputs": {
            "user_request": (
                "Durante abril de 2025, todos os cargos da marca 10 devem usar "
                "o percentual de comissão da marca 20."
            ),
        },
        "expectations": {
            "expected_type": "override",
            "max_iterations": 6,
        },
        "tags": {"category": "override", "subtype": "marca_override"},
    },
    # --- Intercorrência: admissão com bônus ---
    {
        "inputs": {
            "user_request": (
                "O funcionário MATRIC-500 foi admitido em março de 2025 e "
                "recebe bônus de admissão de R$5.000 para o mês de abril/2025."
            ),
        },
        "expectations": {
            "expected_type": "intercorrencia",
            "max_iterations": 6,
        },
        "tags": {"category": "intercorrencia", "subtype": "admissao_bonus"},
    },
    # --- Override: acréscimo percentual com vigência curta ---
    {
        "inputs": {
            "user_request": (
                "Aplicar acréscimo de 0,5% (perc_adicional) na comissão da "
                "marca 10, cargo 300, somente nos 15 primeiros dias de abril/2025."
            ),
        },
        "expectations": {
            "expected_type": "override",
            "max_iterations": 6,
        },
        "tags": {"category": "override", "subtype": "perc_adicional"},
    },
    # --- Rate override: percentual absoluto por loja ---
    {
        "inputs": {
            "user_request": (
                "Todos os funcionarios da loja 75 recebem 6% de comissao "
                "em julho de 2025."
            ),
        },
        "expectations": {
            "expected_type": "rate_override",
            "max_iterations": 6,
        },
        "tags": {"category": "rate_override", "subtype": "store_absolute"},
    },
    # --- Rate override: adicional por matricula ---
    {
        "inputs": {
            "user_request": (
                "O funcionario MATRIC-123 recebe mais 1% de comissao "
                "em julho de 2025."
            ),
        },
        "expectations": {
            "expected_type": "rate_override",
            "max_iterations": 6,
        },
        "tags": {"category": "rate_override", "subtype": "employee_additive"},
    },
]
