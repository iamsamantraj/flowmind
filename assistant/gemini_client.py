from groq import Groq
from django.conf import settings

client = Groq(api_key=settings.GROQ_API_KEY)


def ask_gemini(prompt: str) -> str:
    """Single prompt — used by notes, tasks, goals"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        if '429' in error_msg:
            return "⚠️ AI quota limit reached. Please wait a minute and try again."
        return f"⚠️ AI Error: {error_msg}"


def chat_with_history(messages: list, system_prompt: str = None) -> str:
    """Multi-turn chat with full conversation history"""
    try:
        formatted = []
        if system_prompt:
            formatted.append({"role": "system", "content": system_prompt})
        for msg in messages:
            formatted.append({"role": msg['role'], "content": msg['content']})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=formatted,
            max_tokens=1500,
        )
        return response.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        if '429' in error_msg:
            return "⚠️ AI quota limit reached. Please wait a minute and try again."
        return f"⚠️ AI Error: {error_msg}"