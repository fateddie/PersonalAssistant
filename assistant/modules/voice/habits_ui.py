"""
Habits & Planning UI (Phase 3.5 Week 3)
=======================================
UI for habit stacking, If-Then planning, and GTD brain dump.
"""

import streamlit as st
from datetime import date

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from assistant.modules.behavioural_intelligence.bil_habits import (
    create_habit_chain,
    get_habit_chains,
    get_todays_habits,
    record_habit_completion,
    delete_habit_chain,
    create_if_then_plan,
    get_if_then_plans,
    record_if_then_usage,
    get_suggested_if_then_plans,
    save_brain_dump,
    get_unprocessed_thoughts,
    mark_thought_processed,
    convert_thought_to_task,
)


# Custom CSS
HABITS_CSS = """
<style>
.habit-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    color: #1f2937;
}
.habit-card-completed {
    background: #f0fdf4;
    border-color: #86efac;
}
.habit-trigger {
    color: #6b7280;
    font-size: 0.85rem;
}
.habit-arrow {
    color: #10b981;
    font-weight: bold;
    margin: 0 0.5rem;
}
.habit-action {
    font-weight: 600;
    color: #1f2937;
}
.if-then-card {
    background: #fffbeb;
    border: 1px solid #fcd34d;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    color: #1f2937;
}
.if-clause {
    color: #b45309;
    font-style: italic;
}
.then-clause {
    color: #047857;
    font-weight: 600;
}
.thought-card {
    background: #f5f3ff;
    border: 1px solid #c4b5fd;
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    color: #1f2937;
}
.stats-badge {
    display: inline-block;
    background: #e5e7eb;
    border-radius: 12px;
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    color: #4b5563;
    margin-left: 0.5rem;
}
</style>
"""


def render_habits_tab():
    """Main entry point for habits tab."""
    st.markdown(HABITS_CSS, unsafe_allow_html=True)

    # Sub-navigation
    if "habits_view" not in st.session_state:
        st.session_state.habits_view = "stacking"

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Habit Stacking", use_container_width=True):
            st.session_state.habits_view = "stacking"
            st.rerun()
    with col2:
        if st.button("If-Then Plans", use_container_width=True):
            st.session_state.habits_view = "if_then"
            st.rerun()
    with col3:
        if st.button("Brain Dump", use_container_width=True):
            st.session_state.habits_view = "brain_dump"
            st.rerun()

    st.markdown("---")

    if st.session_state.habits_view == "stacking":
        _render_habit_stacking()
    elif st.session_state.habits_view == "if_then":
        _render_if_then_planning()
    elif st.session_state.habits_view == "brain_dump":
        _render_brain_dump()


def _render_habit_stacking():
    """Render habit stacking view."""
    st.markdown("### Habit Stacking")
    st.markdown("*After [existing habit], I will [new habit]*")

    # Today's habits
    st.subheader("Today's Habits")
    habits = get_todays_habits()

    if not habits:
        st.info("No habit chains created yet. Create your first one below!")
    else:
        for habit in habits:
            completed = habit.get("completed_today")
            card_class = "habit-card-completed" if completed else "habit-card"

            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(
                    f"""<div class="{card_class}">
                    <span class="habit-trigger">After {habit['trigger_habit']}</span>
                    <span class="habit-arrow">→</span>
                    <span class="habit-action">{habit['new_habit']}</span>
                    <span class="stats-badge">{habit['success_count']}/{habit['total_attempts']} done</span>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with col2:
                if completed is None:
                    if st.button("✓ Done", key=f"habit_done_{habit['id']}"):
                        record_habit_completion(habit["id"], completed=True)
                        st.rerun()
                    if st.button("✗ Skip", key=f"habit_skip_{habit['id']}"):
                        record_habit_completion(habit["id"], completed=False)
                        st.rerun()
                elif completed:
                    st.success("Done!")
                else:
                    st.warning("Skipped")

    # Create new habit chain
    st.markdown("---")
    st.subheader("Create Habit Chain")

    with st.form("new_habit_chain"):
        trigger = st.text_input(
            "After I...",
            placeholder="e.g., finish my morning coffee",
        )
        new_habit = st.text_input(
            "I will...",
            placeholder="e.g., write in my journal for 5 minutes",
        )
        time_of_day = st.selectbox(
            "Time of day",
            options=["morning", "afternoon", "evening"],
        )

        if st.form_submit_button("Create Habit Chain", type="primary"):
            if trigger.strip() and new_habit.strip():
                create_habit_chain(
                    trigger_habit=trigger.strip(),
                    new_habit=new_habit.strip(),
                    time_of_day=time_of_day,
                )
                st.success("Habit chain created!")
                st.rerun()
            else:
                st.error("Please fill in both fields.")


def _render_if_then_planning():
    """Render If-Then planning view."""
    st.markdown("### If-Then Planning")
    st.markdown("*Implementation intentions for handling obstacles*")

    # Existing plans
    plans = get_if_then_plans()

    if plans:
        st.subheader("Your If-Then Plans")
        for plan in plans:
            st.markdown(
                f"""<div class="if-then-card">
                <span class="if-clause">If {plan['if_situation']}</span>,
                <span class="then-clause">then I will {plan['then_action']}</span>
                <span class="stats-badge">{plan['category']}</span>
                <span class="stats-badge">Used {plan['times_used']}x</span>
                </div>""",
                unsafe_allow_html=True,
            )

    # Suggestions
    st.markdown("---")
    st.subheader("Suggested Plans")

    suggestions = get_suggested_if_then_plans()
    categories = list(set(s["category"] for s in suggestions))

    selected_category = st.selectbox("Filter by category", ["all"] + categories)

    for suggestion in suggestions:
        if selected_category != "all" and suggestion["category"] != selected_category:
            continue

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(
                f"""<div class="if-then-card">
                <span class="if-clause">If {suggestion['if_situation']}</span>,
                <span class="then-clause">then I will {suggestion['then_action']}</span>
                <span class="stats-badge">{suggestion['category']}</span>
                </div>""",
                unsafe_allow_html=True,
            )
        with col2:
            if st.button("Add", key=f"add_ifthen_{hash(suggestion['if_situation'])}"):
                create_if_then_plan(
                    if_situation=suggestion["if_situation"],
                    then_action=suggestion["then_action"],
                    category=suggestion["category"],
                )
                st.success("Added!")
                st.rerun()

    # Custom plan
    st.markdown("---")
    st.subheader("Create Custom Plan")

    with st.form("new_if_then"):
        if_situation = st.text_input(
            "If...",
            placeholder="e.g., I feel like checking my phone during deep work",
        )
        then_action = st.text_input(
            "Then I will...",
            placeholder="e.g., put it in another room and set a timer",
        )
        category = st.selectbox(
            "Category",
            options=["procrastination", "distraction", "emotion", "energy", "general"],
        )

        if st.form_submit_button("Create Plan", type="primary"):
            if if_situation.strip() and then_action.strip():
                create_if_then_plan(
                    if_situation=if_situation.strip(),
                    then_action=then_action.strip(),
                    category=category,
                )
                st.success("Plan created!")
                st.rerun()
            else:
                st.error("Please fill in both fields.")


def _render_brain_dump():
    """Render GTD brain dump view."""
    st.markdown("### Brain Dump")
    st.markdown("*Get everything out of your head*")

    # Quick capture
    st.subheader("Quick Capture")
    st.markdown("Enter one thought per line. Press submit when done.")

    thoughts_input = st.text_area(
        "What's on your mind?",
        height=200,
        placeholder="Buy groceries\nCall dentist\nFinish report by Friday\nIdea: new feature for app\n...",
        key="brain_dump_input",
    )

    if st.button("Capture All", type="primary", use_container_width=True):
        if thoughts_input.strip():
            items = thoughts_input.strip().split("\n")
            count = save_brain_dump(items)
            st.success(f"Captured {count} items!")
            # Clear the input
            st.session_state.brain_dump_input = ""
            st.rerun()
        else:
            st.warning("Enter at least one thought.")

    # Process inbox
    st.markdown("---")
    st.subheader("Process Inbox")

    unprocessed = get_unprocessed_thoughts()

    if not unprocessed:
        st.success("Inbox clear! Nothing to process.")
    else:
        st.info(f"{len(unprocessed)} items to process")

        for thought in unprocessed[:10]:  # Show max 10 at a time
            st.markdown(
                f"""<div class="thought-card">
                {thought['content']}
                </div>""",
                unsafe_allow_html=True,
            )

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("→ Task", key=f"to_task_{thought['id']}"):
                    convert_thought_to_task(
                        thought["id"],
                        title=thought["content"],
                        priority="med",
                    )
                    st.success("Converted to task!")
                    st.rerun()
            with col2:
                if st.button("→ Later", key=f"to_later_{thought['id']}"):
                    mark_thought_processed(thought["id"], action_taken="deferred")
                    st.rerun()
            with col3:
                if st.button("→ Done", key=f"already_done_{thought['id']}"):
                    mark_thought_processed(thought["id"], action_taken="already_done")
                    st.rerun()
            with col4:
                if st.button("Delete", key=f"delete_{thought['id']}"):
                    mark_thought_processed(thought["id"], action_taken="deleted")
                    st.rerun()

            st.markdown("---")
