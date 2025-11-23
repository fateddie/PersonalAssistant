"""
Template Extractor
==================
Parse a brain-dump prompt into the 6-section template structure.
Uses LLM to identify and categorize prompt elements.
"""

from .models import PromptTemplate, TemplateSection, SectionStatus
from .system_prompts import EXTRACTOR_PROMPT
from .llm_client import call_llm, is_configured


def extract_template(brain_dump: str) -> PromptTemplate:
    """
    Extract structured template from a brain-dump prompt.

    Args:
        brain_dump: The user's messy, unstructured prompt

    Returns:
        PromptTemplate with sections filled, missing, or marked unclear
    """
    if not is_configured():
        # Return empty template if LLM not available
        return _create_fallback_template(brain_dump)

    # Call LLM to analyze the prompt
    result = call_llm(
        system_prompt=EXTRACTOR_PROMPT,
        user_message=f"Analyze this prompt and extract into the 6-section template:\n\n{brain_dump}",
    )

    if "error" in result:
        print(f"⚠️ Extractor error: {result['error']}")
        return _create_fallback_template(brain_dump)

    # Parse LLM response into PromptTemplate
    return _parse_extraction_result(result)


def _parse_extraction_result(result: dict) -> PromptTemplate:
    """Parse LLM JSON response into PromptTemplate"""
    template = PromptTemplate()

    section_names = ["context", "constraints", "inputs", "task", "evaluation", "output_format"]

    for name in section_names:
        if name in result:
            section_data = result[name]
            status = _parse_status(section_data.get("status", "missing"))
            section = TemplateSection(
                content=section_data.get("content", ""),
                status=status,
                notes=section_data.get("notes"),
            )
            setattr(template, name, section)

    return template


def _parse_status(status_str: str) -> SectionStatus:
    """Convert status string to enum"""
    status_str = status_str.lower().strip()
    if status_str == "filled":
        return SectionStatus.FILLED
    elif status_str == "unclear":
        return SectionStatus.UNCLEAR
    else:
        return SectionStatus.MISSING


def _create_fallback_template(brain_dump: str) -> PromptTemplate:
    """
    Create a basic template when LLM is not available.
    Uses simple heuristics to guess at structure.
    """
    template = PromptTemplate()

    # Simple heuristic: put the whole thing in TASK if it looks like a command
    lower = brain_dump.lower()

    # Check for common task indicators
    task_indicators = ["write", "create", "generate", "help me", "make", "build", "analyze"]
    has_task = any(indicator in lower for indicator in task_indicators)

    if has_task:
        template.task = TemplateSection(
            content=brain_dump,
            status=SectionStatus.UNCLEAR,
            notes="Extracted from brain-dump - needs clarification",
        )
    else:
        # If no clear task, mark everything as missing
        template.task = TemplateSection(
            status=SectionStatus.MISSING,
            notes="No clear task identified in the prompt",
        )

    return template
