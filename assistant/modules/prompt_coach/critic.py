"""
Critic
======
Generate critique comparing original prompt to structured version.
Extracts lessons learned for future prompt engineering.
"""

from .models import PromptTemplate, Critique, Lesson
from .system_prompts import CRITIC_PROMPT
from .llm_client import call_llm, is_configured


def generate_critique(original_prompt: str, template: PromptTemplate) -> Critique:
    """
    Generate a critique of the original prompt with lessons learned.

    Args:
        original_prompt: The user's original brain-dump
        template: The filled/structured template

    Returns:
        Critique with score, strengths, weaknesses, and lessons
    """
    if not is_configured():
        return _create_fallback_critique(original_prompt, template)

    # Build context for the LLM
    template_formatted = _format_template(template)

    prompt = f"""Original prompt:
---
{original_prompt}
---

Structured version:
---
{template_formatted}
---

Please critique the original prompt and provide lessons learned."""

    result = call_llm(
        system_prompt=CRITIC_PROMPT,
        user_message=prompt,
    )

    if "error" in result:
        print(f"⚠️ Critic error: {result['error']}")
        return _create_fallback_critique(original_prompt, template)

    return _parse_critique(result)


def _format_template(template: PromptTemplate) -> str:
    """Format template sections for display"""
    sections = [
        ("CONTEXT", template.context.content),
        ("CONSTRAINTS", template.constraints.content),
        ("INPUTS", template.inputs.content),
        ("TASK", template.task.content),
        ("EVALUATION", template.evaluation.content),
        ("OUTPUT_FORMAT", template.output_format.content),
    ]

    lines = []
    for name, content in sections:
        if content:
            lines.append(f"## {name}\n{content}")

    return "\n\n".join(lines)


def _parse_critique(result: dict) -> Critique:
    """Parse LLM response into Critique object"""
    lessons = []
    for lesson_data in result.get("lessons", []):
        lessons.append(
            Lesson(
                title=lesson_data.get("title", ""),
                explanation=lesson_data.get("explanation", ""),
                example_before=lesson_data.get("example_before"),
                example_after=lesson_data.get("example_after"),
            )
        )

    return Critique(
        overall_score=result.get("overall_score", 5),
        strengths=result.get("strengths", []),
        weaknesses=result.get("weaknesses", []),
        lessons=lessons,
    )


def _create_fallback_critique(original_prompt: str, template: PromptTemplate) -> Critique:
    """
    Generate basic critique when LLM is not available.
    Uses simple heuristics to identify common issues.
    """
    strengths = []
    weaknesses = []
    lessons = []

    # Analyze original prompt
    prompt_length = len(original_prompt)
    missing_count = len(template.get_missing_sections())

    # Length analysis
    if prompt_length < 50:
        weaknesses.append("Prompt is very short - likely missing important context")
        lessons.append(
            Lesson(
                title="Add more context",
                explanation="Short prompts force the AI to make assumptions. Include background, constraints, and expected output format.",
            )
        )
    elif prompt_length > 500:
        strengths.append("Prompt is detailed and provides substantial information")

    # Structure analysis
    if missing_count == 0:
        strengths.append("All template sections are covered")
    elif missing_count <= 2:
        weaknesses.append(f"{missing_count} section(s) missing from the prompt")
    else:
        weaknesses.append(f"Prompt is missing {missing_count} of 6 key sections")
        lessons.append(
            Lesson(
                title="Use the 6-section template",
                explanation="Structure your prompts with: Context, Constraints, Inputs, Task, Evaluation, Output Format",
            )
        )

    # Check for common issues
    lower = original_prompt.lower()

    if "help me" in lower and "with" not in lower:
        weaknesses.append("Vague request - 'help me' without specifics")
        lessons.append(
            Lesson(
                title="Be specific about what you want",
                explanation="Instead of 'help me with X', say 'Do Y to achieve Z'",
                example_before="Help me with my code",
                example_after="Review this Python function for bugs and suggest improvements",
            )
        )

    if not any(word in lower for word in ["format", "output", "return", "give me", "provide"]):
        weaknesses.append("No clear output format specified")
        lessons.append(
            Lesson(
                title="Specify the output format",
                explanation="Tell the AI exactly how you want the response formatted",
                example_before="Write about dogs",
                example_after="Write a 3-paragraph essay about dogs with headers",
            )
        )

    # Default strength if none found
    if not strengths:
        strengths.append("You're using a prompt coach to improve - that's a great start!")

    # Calculate score
    score = 5
    score += len(strengths)
    score -= len(weaknesses)
    score = max(1, min(10, score))

    return Critique(
        overall_score=score,
        strengths=strengths,
        weaknesses=weaknesses,
        lessons=lessons,
    )
