"""Textos estáticos de la interfaz (headers, botones, placeholders) en
español e inglés. NO traduce contenido dinámico (mensajes del chat,
nombres de conversación, respuestas del agente) — eso ya se auto-detecta
por mensaje (ver agent._reply_language_directive), que es más flexible
que forzarlo a un solo idioma de interfaz."""

STRINGS = {
    "es": {
        "tagline": "Tu analista financiero personal — precios, noticias y análisis técnico en tiempo real.",
        "conversations_header": "💬 Conversaciones",
        "new_conversation": "➕ Nueva conversación",
        "chat_placeholder": "¿Cómo está el EUR/USD hoy? ¿Hay señal de compra en Apple?",
        "related_news": "📰 Noticias relacionadas ({n})",
        "thinking": "*Consultando mercado...*",
        "unexpected_error": "Algo falló de forma inesperada procesando tu pregunta. Intenta de nuevo en un momento.",
        "lang_selector_label": "Idioma / Language",
        "mic_hold_title": "Mantén presionado para hablar",
        "mic_unsupported": "🎙️ N/D",
        "mic_unsupported_title": "Tu navegador no soporta reconocimiento de voz (usa Chrome o Edge).",
    },
    "en": {
        "tagline": "Your personal financial analyst — real-time prices, news, and technical analysis.",
        "conversations_header": "💬 Conversations",
        "new_conversation": "➕ New conversation",
        "chat_placeholder": "How's EUR/USD doing today? Is there a buy signal on Apple?",
        "related_news": "📰 Related news ({n})",
        "thinking": "*Checking the market...*",
        "unexpected_error": "Something went wrong processing your question. Please try again in a moment.",
        "lang_selector_label": "Idioma / Language",
        "mic_hold_title": "Hold to talk",
        "mic_unsupported": "🎙️ N/A",
        "mic_unsupported_title": "Your browser doesn't support speech recognition (use Chrome or Edge).",
    },
}


def t(lang_code: str, key: str, **kwargs) -> str:
    text = STRINGS[lang_code][key]
    return text.format(**kwargs) if kwargs else text
