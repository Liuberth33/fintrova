import base64
import html
from pathlib import Path

import streamlit as st

import db
from agent import ask
from voice_component import ptt_mic

db.init_db()

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
    st.session_state.messages = db.load_messages()

with st.sidebar:
    st.caption(f"💬 {len(st.session_state.messages)} mensajes guardados")
    if st.button("🗑️ Nueva conversación"):
        db.clear_messages()
        st.session_state.messages = []
        st.rerun()


def render_news(news: list[dict]) -> None:
    if not news:
        return
    with st.expander(f"📰 Noticias relacionadas ({len(news)})"):
        for article in news:
            st.markdown(f"**[{article['title']}]({article['link']})**")
            st.caption(f"{article['source']} · {article['date']}")


def render_user_message(text: str, image_b64: str | None = None) -> None:
    image_html = (
        f'<img src="data:image/png;base64,{image_b64}" style="max-width:100%;border-radius:8px;margin-bottom:0.5rem;display:block;">'
        if image_b64
        else ""
    )
    st.markdown(f'<div class="user-message">{image_html}{html.escape(text)}</div>', unsafe_allow_html=True)


for message in st.session_state.messages:
    if message["role"] == "user":
        render_user_message(message["content"])
        continue
    with st.chat_message("assistant", avatar=LOGO_MARK):
        st.markdown(message["content"])
        render_news(message.get("news", []))

# Micrófono push-to-talk (mantener presionado para hablar, soltar para
# enviar) — componente propio en components/ptt_mic, ver voice_component.py.
# El navegador necesita saber de antemano en qué idioma escuchar, así que
# hace falta elegirlo antes de grabar (a diferencia del texto, donde el
# idioma de la pregunta se detecta después, ver
# agent._reply_language_directive). Solo funciona en navegadores basados en
# Chromium (Chrome/Edge); Firefox y Safari no implementan esta API.
mic_col, lang_col = st.columns([1, 4])
with lang_col:
    voice_lang_label = st.selectbox(
        "Idioma de voz", ["🇪🇸 Español", "🇺🇸 English"],
        label_visibility="collapsed", key="voice_lang",
    )
with mic_col:
    voice_text = ptt_mic(
        language="es-ES" if "Español" in voice_lang_label else "en-US",
        key="mic_input",
    )

submission = st.chat_input(
    "¿Cómo está el EUR/USD hoy? ¿Hay señal de compra en Apple?",
    accept_file=True,
    file_type=["png", "jpg", "jpeg"],
)

if submission or voice_text:
    image = None
    image_b64 = None

    if submission:
        question = submission.text or "Analiza este gráfico."
        if submission.files:
            uploaded = submission.files[0]
            image_bytes = uploaded.getvalue()
            image_b64 = base64.b64encode(image_bytes).decode()
            image = {"media_type": uploaded.type or "image/png", "data": image_b64}
    else:
        question = voice_text

    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]

    # La imagen no se persiste en la base de datos ni en el historial que
    # se le pasa al agente en turnos futuros (solo aplica al turno actual,
    # ver docstring de agent.ask) — evita inflar tokens/almacenamiento.
    st.session_state.messages.append({"role": "user", "content": question, "news": []})
    db.save_message("user", question, [])
    render_user_message(question, image_b64=image_b64)

    # Bubble con la gema animada mientras el agente trabaja. La duración real
    # de ask() es impredecible (depende de cuántas tools llame), así que el
    # GIF corre en loop en vez de intentar sincronizarlo con la respuesta.
    thinking = st.empty()
    with thinking.container():
        with st.chat_message("assistant", avatar=LOGO_THINKING):
            st.markdown("*Consultando mercado...*")

    try:
        result = ask(question, history=history, image=image)
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
    db.save_message("assistant", result["text"], result["news"])
