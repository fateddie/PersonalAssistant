"""
Prompt Coach UI Components
==========================
Streamlit UI for the prompt coaching flow.
Improved UX with better guidance, progress indicators, and visual polish.
"""

import streamlit as st

# Import from prompt_coach module
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from assistant.modules.prompt_coach.extractor import extract_template
from assistant.modules.prompt_coach.interrogator import generate_questions
from assistant.modules.prompt_coach.critic import generate_critique
from assistant.modules.prompt_coach.database import save_session, get_saved_sessions
from assistant.modules.prompt_coach.models import SectionStatus

# Custom CSS for coach UI
COACH_CSS = """
<style>
.coach-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.5rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 1rem;
}
.score-badge {
    font-size: 2rem;
    font-weight: bold;
    padding: 0.5rem 1rem;
    border-radius: 50px;
    display: inline-block;
}
.score-high { background: #10b981; color: white; }
.score-mid { background: #f59e0b; color: white; }
.score-low { background: #ef4444; color: white; }
.section-card {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
}
.section-filled { border-left: 4px solid #10b981; }
.section-unclear { border-left: 4px solid #f59e0b; }
.section-missing { border-left: 4px solid #ef4444; }
.question-card {
    background: #f8fafc;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 1rem;
    border-left: 4px solid #667eea;
}
.progress-step {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    margin-right: 0.5rem;
    font-size: 0.85rem;
}
.step-active { background: #667eea; color: white; }
.step-done { background: #10b981; color: white; }
.step-pending { background: #e5e7eb; color: #6b7280; }
</style>
"""

EXAMPLE_PROMPT = """help me write a python script that processes some files and does something with the data, needs to be fast"""

TEMPLATE_HELP = """
**The 6-Section Template:**
1. **Context** - Background info (who you are, what project)
2. **Constraints** - Requirements & limitations
3. **Inputs** - Data or information provided
4. **Task** - What exactly should be done
5. **Evaluation** - How to measure success
6. **Output Format** - Expected response format
"""


def render_coach_tab():
    """Main entry point for the Coach tab"""
    st.markdown(COACH_CSS, unsafe_allow_html=True)

    # Initialize session state
    _init_session_state()

    # Progress indicator
    _render_progress_bar()

    st.markdown("---")

    # Render current stage
    stage = st.session_state.coach_stage
    if stage == "input":
        _render_input_stage()
    elif stage == "questions":
        _render_questions_stage()
    elif stage == "result":
        _render_result_stage()


def _init_session_state():
    """Initialize all session state variables"""
    defaults = {
        "coach_stage": "input",
        "coach_template": None,
        "coach_questions": [],
        "coach_original": "",
        "coach_critique": None,
        "coach_answers": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_progress_bar():
    """Show progress through the coaching flow"""
    stage = st.session_state.coach_stage
    stages = [("input", "1. Input"), ("questions", "2. Clarify"), ("result", "3. Result")]

    cols = st.columns([1, 1, 1, 2])
    for i, (stage_id, label) in enumerate(stages):
        with cols[i]:
            if stage_id == stage:
                st.markdown(f"**🔵 {label}**")
            elif stages.index((stage_id, label)) < stages.index(
                next((s for s in stages if s[0] == stage), stages[0])
            ):
                st.markdown(f"✅ {label}")
            else:
                st.markdown(f"⚪ {label}")


def _render_input_stage():
    """Stage 1: User enters brain-dump prompt"""
    st.markdown("### 🎓 Prompt Coach")
    st.markdown("*Transform your messy prompt into a well-structured one*")

    # Help section
    with st.expander("ℹ️ What makes a good prompt?", expanded=False):
        st.markdown(TEMPLATE_HELP)

    # Input area
    st.markdown("**Paste your prompt below:**")

    brain_dump = st.text_area(
        "Your prompt",
        height=150,
        placeholder=EXAMPLE_PROMPT,
        key="coach_input",
        label_visibility="collapsed",
    )

    # Character count
    if brain_dump:
        st.caption(f"📝 {len(brain_dump)} characters")

    # Action buttons
    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        analyze_btn = st.button(
            "🚀 Analyze My Prompt",
            type="primary",
            disabled=not brain_dump or len(brain_dump) < 10,
            use_container_width=True,
        )

    with col2:
        if st.button("📝 Use Example", use_container_width=True):
            st.session_state.coach_input = EXAMPLE_PROMPT
            st.rerun()

    if analyze_btn:
        with st.spinner("🔍 Analyzing your prompt..."):
            template = extract_template(brain_dump)
            st.session_state.coach_template = template
            st.session_state.coach_original = brain_dump

            questions = generate_questions(template)
            st.session_state.coach_questions = questions

            if questions:
                st.session_state.coach_stage = "questions"
            else:
                critique = generate_critique(brain_dump, template)
                st.session_state.coach_critique = critique
                st.session_state.coach_stage = "result"

            st.rerun()

    # Saved prompts at bottom
    st.markdown("---")
    with st.expander("📚 Your Saved Prompts", expanded=False):
        _render_saved_prompts()


def _render_questions_stage():
    """Stage 2: Ask clarifying questions"""
    template = st.session_state.coach_template
    questions = st.session_state.coach_questions

    st.markdown("### 🔍 Let's Fill the Gaps")

    # Template status overview
    st.markdown("**Current template status:**")
    _render_template_cards(template)

    st.markdown("---")

    # Questions
    num_questions = len(questions)
    st.markdown(f"### ❓ {num_questions} Question{'s' if num_questions != 1 else ''} to Clarify")

    for i, q in enumerate(questions):
        section_label = q.section.replace("_", " ").title()

        # Use Streamlit container instead of raw HTML to avoid overlay issues
        with st.container():
            st.markdown(f"**Q{i+1}. [{section_label}]** {q.question}")

            # Use only key= (no value=) to let Streamlit manage widget state
            answer_key = f"coach_answer_{q.id}"
            st.text_area(
                f"Answer {i+1}",
                key=answer_key,
                height=80,
                placeholder="Your answer...",
                label_visibility="collapsed",
            )
        st.markdown("")

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 2, 3])

    with col1:
        submit_btn = st.button("✅ Submit Answers", type="primary", use_container_width=True)

    with col2:
        skip_btn = st.button("⏭️ Skip & Finish", use_container_width=True)

    with col3:
        if st.button("🔙 Start Over", use_container_width=True):
            _reset_coach_state()
            st.rerun()

    if submit_btn:
        # Combine original with answers from session state widget keys
        combined = st.session_state.coach_original + "\n\nAdditional context:\n"
        for q in questions:
            answer_key = f"coach_answer_{q.id}"
            answer_value = st.session_state.get(answer_key, "")
            if answer_value:
                combined += f"Q: {q.question}\nA: {answer_value}\n\n"

        # Clear old answer keys from session state before generating new questions
        for q in questions:
            answer_key = f"coach_answer_{q.id}"
            if answer_key in st.session_state:
                del st.session_state[answer_key]

        with st.spinner("🔄 Processing your answers..."):
            template = extract_template(combined)
            st.session_state.coach_template = template

            new_questions = generate_questions(template)

            if new_questions and len(new_questions) > 0:
                st.session_state.coach_questions = new_questions
            else:
                critique = generate_critique(st.session_state.coach_original, template)
                st.session_state.coach_critique = critique
                st.session_state.coach_stage = "result"

            st.rerun()

    if skip_btn:
        with st.spinner("🎯 Generating your improved prompt..."):
            critique = generate_critique(st.session_state.coach_original, template)
            st.session_state.coach_critique = critique
            st.session_state.coach_stage = "result"
            st.rerun()


def _render_result_stage():
    """Stage 3: Show final prompt and critique"""
    template = st.session_state.coach_template
    critique = st.session_state.coach_critique
    original = st.session_state.coach_original

    final_prompt = _build_final_prompt(template)

    # Score header
    score = critique.overall_score if critique else 5
    if score >= 7:
        score_class = "score-high"
        score_emoji = "🎉"
        score_msg = "Great prompt!"
    elif score >= 4:
        score_class = "score-mid"
        score_emoji = "👍"
        score_msg = "Good start, room to improve"
    else:
        score_class = "score-low"
        score_emoji = "💪"
        score_msg = "Let's work on this"

    st.markdown(
        f"""
        <div style="text-align: center; padding: 1rem;">
            <div class="score-badge {score_class}">{score}/10</div>
            <p style="margin-top: 0.5rem;">{score_emoji} {score_msg}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Two columns: Original vs Improved
    st.markdown("### 📊 Comparison")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**❌ Original:**")
        st.code(original, language=None)

    with col2:
        st.markdown("**✅ Improved:**")
        st.code(final_prompt, language="markdown")

    # Critique sections
    st.markdown("---")

    if critique:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### ✅ Strengths")
            for s in critique.strengths:
                st.success(s)

        with col2:
            st.markdown("### ⚠️ Areas to Improve")
            for w in critique.weaknesses:
                st.warning(w)

        # Lessons
        if critique.lessons:
            st.markdown("---")
            st.markdown("### 📚 Lessons Learned")

            for lesson in critique.lessons:
                with st.expander(f"📖 {lesson.title}", expanded=False):
                    st.markdown(lesson.explanation)
                    if lesson.example_before and lesson.example_after:
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Before:**")
                            st.code(lesson.example_before, language=None)
                        with col2:
                            st.markdown("**After:**")
                            st.code(lesson.example_after, language=None)

    # Actions
    st.markdown("---")
    st.markdown("### 💾 Save & Continue")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        template_name = st.text_input(
            "Name your prompt (optional)",
            placeholder="e.g., Python File Processor",
            label_visibility="collapsed",
        )

    with col2:
        if st.button("💾 Save", type="primary", use_container_width=True):
            lessons = [l.title for l in critique.lessons] if critique else []
            save_session(
                original_prompt=original,
                final_prompt=final_prompt,
                overall_score=score,
                lessons=lessons,
                template_name=template_name if template_name else None,
            )
            st.success("✅ Saved to library!")

    with col3:
        if st.button("🔄 New Prompt", use_container_width=True):
            _reset_coach_state()
            st.rerun()


def _render_template_cards(template):
    """Show template sections as cards with status"""
    sections = [
        ("Context", template.context, "Who you are, background info"),
        ("Constraints", template.constraints, "Requirements, limitations"),
        ("Inputs", template.inputs, "Data provided"),
        ("Task", template.task, "What to do"),
        ("Evaluation", template.evaluation, "Success criteria"),
        ("Output", template.output_format, "Response format"),
    ]

    cols = st.columns(3)
    for i, (name, section, hint) in enumerate(sections):
        with cols[i % 3]:
            if section.status == SectionStatus.FILLED:
                st.markdown(f"✅ **{name}**")
            elif section.status == SectionStatus.UNCLEAR:
                st.markdown(f"🟡 **{name}**")
            else:
                st.markdown(f"❌ **{name}**")


def _render_saved_prompts():
    """Show previously saved prompts"""
    sessions = get_saved_sessions(limit=10)

    if not sessions:
        st.info("No saved prompts yet. Complete a session to save one!")
        return

    for session in sessions:
        name = session.get("template_name") or "Unnamed"
        score = session.get("overall_score", "?")
        created = str(session.get("created_at", ""))[:10]

        with st.expander(f"📄 {name} ({score}/10) - {created}"):
            st.code(session.get("final_prompt", ""), language="markdown")


def _build_final_prompt(template) -> str:
    """Build the final prompt string from template sections"""
    sections = []

    if template.context.content:
        sections.append(f"## CONTEXT\n{template.context.content}")
    if template.constraints.content:
        sections.append(f"## CONSTRAINTS\n{template.constraints.content}")
    if template.inputs.content:
        sections.append(f"## INPUTS\n{template.inputs.content}")
    if template.task.content:
        sections.append(f"## TASK\n{template.task.content}")
    if template.evaluation.content:
        sections.append(f"## EVALUATION\n{template.evaluation.content}")
    if template.output_format.content:
        sections.append(f"## OUTPUT FORMAT\n{template.output_format.content}")

    return "\n\n".join(sections) if sections else "No content extracted"


def _reset_coach_state():
    """Reset all coach session state"""
    st.session_state.coach_stage = "input"
    st.session_state.coach_template = None
    st.session_state.coach_questions = []
    st.session_state.coach_original = ""
    st.session_state.coach_critique = None
    st.session_state.coach_answers = {}
