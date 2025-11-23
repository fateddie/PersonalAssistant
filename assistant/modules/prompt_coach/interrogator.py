"""
Interrogator
============
Generate clarifying questions for missing/unclear template sections.
Uses LLM to create targeted, prioritized questions.
"""

from typing import List
from .models import PromptTemplate, ClarifyingQuestion, SectionStatus
from .system_prompts import INTERROGATOR_PROMPT
from .llm_client import call_llm, is_configured


def generate_questions(template: PromptTemplate) -> List[ClarifyingQuestion]:
    """
    Generate clarifying questions for gaps in the template.

    Args:
        template: The partially-filled prompt template

    Returns:
        List of prioritized clarifying questions (max 5)
    """
    # Check if there are any gaps
    missing_sections = template.get_missing_sections()
    if not missing_sections:
        return []  # Template is complete, no questions needed

    if not is_configured():
        # Return basic questions if LLM not available
        return _create_fallback_questions(template, missing_sections)

    # Build context about current template state
    template_summary = _summarize_template(template)

    # Call LLM to generate questions
    result = call_llm(
        system_prompt=INTERROGATOR_PROMPT,
        user_message=f"Generate clarifying questions for this template:\n\n{template_summary}",
    )

    if "error" in result:
        print(f"⚠️ Interrogator error: {result['error']}")
        return _create_fallback_questions(template, missing_sections)

    # Parse questions from response
    return _parse_questions(result)


def _summarize_template(template: PromptTemplate) -> str:
    """Create a summary of the template for the LLM"""
    sections = [
        ("CONTEXT", template.context),
        ("CONSTRAINTS", template.constraints),
        ("INPUTS", template.inputs),
        ("TASK", template.task),
        ("EVALUATION", template.evaluation),
        ("OUTPUT_FORMAT", template.output_format),
    ]

    lines = []
    for name, section in sections:
        status = section.status.value.upper()
        content = section.content if section.content else "[empty]"
        notes = f" (Note: {section.notes})" if section.notes else ""
        lines.append(f"{name} [{status}]: {content}{notes}")

    return "\n".join(lines)


def _parse_questions(result: dict) -> List[ClarifyingQuestion]:
    """Parse LLM response into ClarifyingQuestion list"""
    questions = []

    raw_questions = result.get("questions", [])
    for i, q_data in enumerate(raw_questions[:5]):  # Max 5 questions
        question = ClarifyingQuestion(
            id=q_data.get("id", f"q{i+1}"),
            section=q_data.get("section", "task"),
            question=q_data.get("question", ""),
            priority=q_data.get("priority", 2),
        )
        if question.question:  # Only add if there's actual question text
            questions.append(question)

    # Sort by priority (1 = most important)
    questions.sort(key=lambda q: q.priority)

    return questions


def _create_fallback_questions(
    template: PromptTemplate, missing_sections: List[str]
) -> List[ClarifyingQuestion]:
    """
    Generate basic questions when LLM is not available.
    Uses predefined questions for each section type.
    """
    section_questions = {
        "context": "What background information should I know about this situation?",
        "constraints": "Are there any requirements, limitations, or things to avoid?",
        "inputs": "What specific data or information should I work with?",
        "task": "What exactly do you want me to do? What's the end goal?",
        "evaluation": "How will you know if the output is good? What makes it successful?",
        "output_format": "What format should the output be in? (e.g., bullet points, code, essay)",
    }

    questions = []
    for i, section in enumerate(missing_sections[:5]):
        question_text = section_questions.get(section, f"Can you tell me more about the {section}?")
        questions.append(
            ClarifyingQuestion(
                id=f"q{i+1}",
                section=section,
                question=question_text,
                priority=1 if section == "task" else 2,
            )
        )

    return questions
