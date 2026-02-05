from __future__ import annotations

from typing import Iterable

from core.config import settings


def _openai_client():
    if not settings.openai_api_key:
        return None
    try:
        from openai import OpenAI
    except Exception:
        return None
    return OpenAI(api_key=settings.openai_api_key)


def _generate_with_openai(system_prompt: str, user_prompt: str) -> str | None:
    client = _openai_client()
    if client is None:
        return None
    try:
        response = client.responses.create(
            model=settings.llm_model,
            input=[
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": user_prompt}],
                },
            ],
            max_output_tokens=300,
        )
        return response.output_text
    except Exception:
        return None


def generate_llm_draft(lead_summary: str | None, context_docs: Iterable[str] | None = None) -> str:
    summary = (lead_summary or "").strip()
    docs = "\n".join(context_docs) if context_docs else ""

    system_prompt = (
        "You are a senior ClientOps assistant. Draft a concise, friendly follow-up email that is clear, "
        "specific, and action-oriented. Keep it under 120 words. Include 1 short clarifying question and "
        "a suggested next step (call or requirements checklist). Avoid fluff."
    )
    user_prompt = f"Lead summary: {summary or 'No summary provided.'}\n\nContext:\n{docs}".strip()

    result = _generate_with_openai(system_prompt, user_prompt)
    if result:
        return result

    # Fallback if no LLM available
    if summary:
        return (
            "Hi there,\n\n"
            "Thanks for reaching out. I reviewed your request and put together next steps below.\n\n"
            f"Summary I captured: {summary}\n\n"
            "If this looks right, I can send a proposed plan and timeline.\n"
            "Best,\nClientOps AI"
        )

    return (
        "Hi there,\n\n"
        "Thanks for reaching out. Can you share a bit more about your goal and tools?\n\n"
        "Best,\nClientOps AI"
    )


def generate_llm_reply(message: str) -> str | None:
    system_prompt = (
        "You are a ClientOps chat assistant. Respond in 3-6 short sentences. Be clear and helpful. "
        "Ask exactly one clarifying question. If the user asks about services, list 3-5 service bullets "
        "and end with the clarifying question."
    )
    return _generate_with_openai(system_prompt, message)
