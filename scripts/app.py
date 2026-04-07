import streamlit as st
import json
from src.agent.editing.chains import Chains
from langchain_core.messages import AIMessage, HumanMessage
import time
import mlflow

def parse_and_display(raw:str) -> str:
    try:
        parsed = json.loads(raw)
        file_path = parsed.get("file", "arquivo desconhecido")
        code = parsed.get("updated_code", "")

        st.markdown(f"**Arquivo gerado:** `{file_path}`")
        st.code(code, language="python")
        
        return f"Arquivo `{file_path}` atualizado com sucesso."
    except (json.JSONDecodeError, KeyError):
        st.markdown(raw)
        return raw 


if __name__ == "__main__":
    st.set_page_config(page_title="Rule AI", page_icon="🤖")
    st.title("Executando Rule AI 🤖")

    # Chain mantida no session_state — evita recriar a cada rerun
    if "agent" not in st.session_state:
        st.session_state.agent = Chains().edit_chain()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            AIMessage(content="Olá! Como posso ajudar você hoje?")
        ]

    # Renderiza histórico
    for message in st.session_state.chat_history:
        if isinstance(message, AIMessage):
            with st.chat_message("AI"):
                # Tenta re-renderizar código se a mensagem contiver JSON
                try:
                    parsed = json.loads(message.content)
                    if "updated_code" in parsed:
                        st.markdown(f"**Arquivo:** `{parsed.get('file', '')}`")
                        st.code(parsed["updated_code"], language="python")
                    else:
                        st.write(message.content)
                except (json.JSONDecodeError, TypeError):
                    st.write(message.content)

        elif isinstance(message, HumanMessage):
            with st.chat_message("Human"):
                st.write(message.content)

    user_query = st.chat_input("Digite sua mensagem")

    if user_query:
        st.session_state.chat_history.append(HumanMessage(content=user_query))

        with st.chat_message("Human"):
            st.markdown(user_query)

        with st.chat_message("AI"):
            with st.spinner("Gerando código..."):
                start = time.time()
                result = st.session_state.agent.invoke({"input": user_query})
                end = time.time()

            summary = parse_and_display(result)
            st.caption(f"⏱️ {end - start:.1f}s")

        # Salva o JSON bruto no histórico para re-renderizar corretamente
        st.session_state.chat_history.append(AIMessage(content=result))