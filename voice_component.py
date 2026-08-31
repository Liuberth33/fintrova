from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

_COMPONENT_DIR = Path(__file__).parent / "components" / "ptt_mic"
_ptt_mic = components.declare_component("ptt_mic", path=str(_COMPONENT_DIR))


def ptt_mic(language: str = "es-ES", key: str | None = None) -> str | None:
    """Botón de micrófono "mantén presionado para hablar" (push-to-talk),
    implementado como componente Streamlit propio (ver components/ptt_mic)
    porque ningún paquete existente soportaba ese patrón de interacción —
    solo click-para-iniciar/click-para-detener. Usa la Web Speech API
    nativa del navegador (sin backend de transcripción propio).

    Devuelve el texto transcrito solo la primera vez que llega (se
    deduplica por `id` en session_state, igual que hace un chat_input real
    para no reprocesar la misma pregunta en cada rerun de Streamlit)."""
    state_key = f"_ptt_mic_last_id_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = 0

    value = _ptt_mic(language=language, key=key, default=None)
    if not value:
        return None

    if value["id"] <= st.session_state[state_key]:
        return None

    st.session_state[state_key] = value["id"]
    return value["text"]
