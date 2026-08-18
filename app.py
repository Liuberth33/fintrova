import base64
import html
from pathlib import Path

import streamlit as st

from agent import ask

ASSETS_DIR = Path(__file__).parent / "assets"
LOGO = str(ASSETS_DIR / "logo.png")
LOGO_MARK = str(ASSETS_DIR / "logo_cropped.png")
LOGO_THINKING = str(ASSETS_DIR / "logo_thinking.gif")

st.set_page_config(page_title="Fintrova", page_icon=LOGO)

_logo_b64 = base64.b64encode((ASSETS_DIR / "logo_cropped.png").read_bytes()).decode()

st.markdown(
    f"""
    <style>
    .user-message {{
        background: var(--secondary-background-color);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0 1rem auto;
        max-width: 80%;
        width: fit-content;
    }}
    .app-header {{
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 0.25rem;
        margin-bottom: 1rem;
    }}
    .app-header img {{
        width: 64px;
        margin-bottom: 0.25rem;
    }}
    .app-header h1 {{
        margin: 0;
    }}
    </style>
    <div class="app-header">
        <img src="data:image/png;base64,{_logo_b64}" alt="Fintrova">
        <h1>Fintrova</h1>
        <p>Tu analista financiero personal — precios, noticias y análisis técnico en tiempo real.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []


def render_news(news: list[dict]) -> None:
    if not news:
        return
    with st.expander(f"📰 Noticias relacionadas ({len(news)})"):
        for article in news:
            st.markdown(f"**[{article['title']}]({article['link']})**")
            st.caption(f"{article['source']} · {article['date']}")


def render_user_message(text: str) -> None:
    st.markdown(f'<div class="user-message">{html.escape(text)}</div>', unsafe_allow_html=True)


for message in st.session_state.messages:
    if message["role"] == "user":
        render_user_message(message["content"])
        continue
    with st.chat_message("assistant", avatar=LOGO_MARK):
        st.markdown(message["content"])
        render_news(message.get("news", []))

question = st.chat_input("¿Cómo está el EUR/USD hoy? ¿Hay señal de compra en Apple?")

if question:
    st.session_state.messages.append({"role": "user", "content": question, "news": []})
    render_user_message(question)

    # Bubble con la gema animada mientras el agente trabaja. La duración real
    # de ask() es impredecible (depende de cuántas tools llame), así que el
    # GIF corre en loop en vez de intentar sincronizarlo con la respuesta.
    thinking = st.empty()
    with thinking.container():
        with st.chat_message("assistant", avatar=LOGO_THINKING):
            st.markdown("*Consultando mercado...*")

    try:
        result = ask(question)
    except Exception:
        result = {
            "text": "Algo falló de forma inesperada procesando tu pregunta. Intenta de nuevo en un momento.",
            "news": [],
        }

    # Se reemplaza la bubble animada por una estática ya con la respuesta real.
    thinking.empty()
    with st.chat_message("assistant", avatar=LOGO_MARK):
        st.markdown(result["text"])
        render_news(result["news"])
    st.session_state.messages.append({"role": "assistant", "content": result["text"], "news": result["news"]})
