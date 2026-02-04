from __future__ import annotations

from typing import Iterable


def generate_llm_draft(lead_summary: str | None, context_docs: Iterable[str] | None = None) -> str:
    """Temporary stub for draft generation until LLM integration is wired."""
    summary = (lead_summary or "").strip()
    doc_hint = ""
    if context_docs:
        count = len(list(context_docs))
        doc_hint = f"\n\nContext docs reviewed: {count}"

    if summary:
        return (
            "Hi there,\n\n"
            "Thanks for reaching out. I reviewed your request and put together next steps below.\n\n"
            f"Summary I captured: {summary}\n\n"
            "If this looks right, I can send a proposed plan and timeline.\n"
            "Best,\nClientOps AI"
            f"{doc_hint}"
        )

    return (
        "Hi there,\n\n"
        "Thanks for reaching out. Can you share a bit more about your goal and tools?\n\n"
        "Best,\nClientOps AI"
        f"{doc_hint}"
    )
