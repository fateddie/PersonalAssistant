"""
Discipline UI Components (Phase 3.5)
====================================
Streamlit UI for evening planning, morning display, and discipline tracking.
"""

import streamlit as st
from datetime import date, timedelta

# Import from behavioural_intelligence module
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from assistant.modules.behavioural_intelligence.bil_daily_reflection import (
    save_evening_plan,
    save_morning_fallback,
    get_today_plan,
    get_tomorrow_plan,
    get_recent_reflections,
)
from assistant.modules.behavioural_intelligence.bil_rituals import (
    check_needs_evening_planning,
    check_needs_morning_fallback,
    get_evening_planning_context,
    get_morning_display_data,
    on_plan_completed,
)
from assistant.modules.behavioural_intelligence.bil_streaks import (
    get_all_streaks,
    get_at_risk_streaks,
)
from eisenhower_ui import render_eisenhower_matrix


# Custom CSS for discipline UI
DISCIPLINE_CSS = """
<style>
.discipline-header {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    padding: 1.5rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 1rem;
}
.priority-card {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
    color: #1f2937;
}
.priority-number {
    display: inline-block;
    width: 28px;
    height: 28px;
    background: #10b981;
    color: white;
    border-radius: 50%;
    text-align: center;
    line-height: 28px;
    font-weight: bold;
    margin-right: 0.5rem;
}
.streak-badge {
    background: #fef3c7;
    border: 1px solid #fcd34d;
    border-radius: 20px;
    padding: 0.25rem 0.75rem;
    font-size: 0.85rem;
    display: block;
    margin-bottom: 0.5rem;
    color: #1f2937;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.streak-active { background: #dcfce7; border-color: #86efac; color: #166534; }
.streak-at-risk { background: #fee2e2; border-color: #fca5a5; color: #991b1b; }
.plan-mode-toggle {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
}
</style>
"""


def render_discipline_tab():
    """Main entry point for discipline tab."""
    st.markdown(DISCIPLINE_CSS, unsafe_allow_html=True)

    # Initialize session state
    if "discipline_mode" not in st.session_state:
        st.session_state.discipline_mode = "today"  # "today", "plan_tomorrow", or "matrix"

    # Header
    st.markdown(
        """<div class="discipline-header">
        <h2 style="margin:0;">Proactive Discipline</h2>
        <p style="margin:0.5rem 0 0 0; opacity:0.9;">Plan tomorrow, execute today</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # Mode toggle
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("Today's Plan", use_container_width=True):
            st.session_state.discipline_mode = "today"
            st.rerun()
    with col2:
        if st.button("Plan Tomorrow", use_container_width=True):
            st.session_state.discipline_mode = "plan_tomorrow"
            st.rerun()
    with col3:
        if st.button("Matrix", use_container_width=True):
            st.session_state.discipline_mode = "matrix"
            st.rerun()

    st.markdown("---")

    # Render based on mode
    if st.session_state.discipline_mode == "today":
        _render_today_view()
    elif st.session_state.discipline_mode == "plan_tomorrow":
        _render_evening_planning()
    elif st.session_state.discipline_mode == "matrix":
        render_eisenhower_matrix()

    # Sidebar: Streaks
    _render_streaks_sidebar()


def _render_today_view():
    """Display today's plan and status."""
    morning_data = get_morning_display_data()

    if not morning_data["has_plan"]:
        st.warning("No plan for today. Create one now!")

        # Quick morning fallback form
        st.subheader("Quick Morning Plan")

        priority1 = st.text_input(
            "Priority 1", key="morning_p1", placeholder="Most important task..."
        )
        priority2 = st.text_input("Priority 2", key="morning_p2", placeholder="Second priority...")
        priority3 = st.text_input("Priority 3", key="morning_p3", placeholder="Third priority...")
        one_great = st.text_input(
            "One thing to make today great",
            key="morning_great",
            placeholder="e.g., Complete project proposal",
        )

        if st.button("Save Morning Plan", type="primary", use_container_width=True):
            priorities = [p for p in [priority1, priority2, priority3] if p.strip()]
            if priorities and one_great.strip():
                save_morning_fallback(
                    plan_for_date=date.today(),
                    top_priorities=priorities,
                    one_thing_great=one_great.strip(),
                )
                st.success("Morning plan saved!")
                st.rerun()
            else:
                st.error("Please enter at least one priority and one thing to make today great.")
        return

    # Display today's plan
    plan = morning_data["plan"]

    if morning_data["is_fallback"]:
        st.info("Created via morning fallback")

    st.subheader("Top 3 Priorities")
    for i, priority in enumerate(morning_data["priorities"], 1):
        st.markdown(
            f"""<div class="priority-card">
            <span class="priority-number">{i}</span> {priority}
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    st.subheader("One Thing to Make Today Great")
    st.markdown(f"**{morning_data['one_thing_great']}**")

    # Show reflection from yesterday if available
    if plan.get("what_went_well"):
        with st.expander("Yesterday's Reflection"):
            st.markdown(f"**What went well:** {plan.get('what_went_well', 'N/A')}")
            st.markdown(f"**What got in the way:** {plan.get('what_got_in_way', 'N/A')}")
            if plan.get("one_thing_learned"):
                st.markdown(f"**Key learning:** {plan.get('one_thing_learned')}")


def _render_evening_planning():
    """Evening planning form."""
    context = get_evening_planning_context()
    tomorrow = context["target_date"]

    # Check if plan already exists
    existing_plan = get_tomorrow_plan()
    if existing_plan and existing_plan.get("evening_completed"):
        st.success(f"You already have a plan for {tomorrow.strftime('%A, %B %d')}!")

        # Show existing plan
        st.subheader("Your Plan")
        for i, p in enumerate(existing_plan.get("top_priorities", []), 1):
            st.markdown(f"{i}. {p}")
        st.markdown(f"**One thing great:** {existing_plan.get('one_thing_great', '')}")

        if st.button("Edit Plan"):
            # Allow re-editing
            pass
        else:
            return

    st.subheader(f"Plan for {tomorrow.strftime('%A, %B %d')}")

    # Streak info
    streak = context["streak_info"]
    if streak["current"] > 0:
        st.markdown(
            f"""<span class="streak-badge streak-active">
            Evening Planning Streak: {streak['current']} days
            </span>""",
            unsafe_allow_html=True,
        )

    # Reflection on today
    st.markdown("### Reflect on Today")

    what_went_well = st.text_area(
        "What went well today?",
        key="evening_well",
        height=80,
        placeholder="Celebrate your wins, big or small...",
    )

    what_got_in_way = st.text_area(
        "What got in the way?",
        key="evening_blockers",
        height=80,
        placeholder="Identify blockers to avoid tomorrow...",
    )

    one_thing_learned = st.text_input(
        "One thing you learned today",
        key="evening_learned",
        placeholder="Optional: Key insight or lesson...",
    )

    st.markdown("---")

    # Tomorrow's plan
    st.markdown("### Plan Tomorrow")

    # Show suggestions if available
    if context["suggested_priorities"]:
        with st.expander("Suggested from incomplete tasks"):
            for task in context["suggested_priorities"]:
                st.markdown(f"- {task}")

    priority1 = st.text_input(
        "Priority 1 (Most Important)",
        key="evening_p1",
        placeholder="What MUST get done tomorrow?",
    )
    priority2 = st.text_input(
        "Priority 2",
        key="evening_p2",
        placeholder="Second most important...",
    )
    priority3 = st.text_input(
        "Priority 3",
        key="evening_p3",
        placeholder="Third priority...",
    )

    one_great = st.text_input(
        "One thing to make tomorrow great",
        key="evening_great",
        placeholder="e.g., Ship feature X, Run 5km, Deep work session",
    )

    st.markdown("---")

    # Submit
    if st.button("Save Evening Plan", type="primary", use_container_width=True):
        priorities = [p for p in [priority1, priority2, priority3] if p.strip()]

        if not priorities:
            st.error("Please enter at least one priority.")
            return

        if not one_great.strip():
            st.error("Please enter one thing to make tomorrow great.")
            return

        # Save the plan
        save_evening_plan(
            plan_for_date=tomorrow,
            top_priorities=priorities,
            one_thing_great=one_great.strip(),
            what_went_well=what_went_well.strip() if what_went_well else None,
            what_got_in_way=what_got_in_way.strip() if what_got_in_way else None,
            one_thing_learned=one_thing_learned.strip() if one_thing_learned else None,
        )

        # Update streak
        on_plan_completed("evening")

        st.success("Evening plan saved! You're set for tomorrow.")
        st.balloons()
        st.rerun()


def _render_streaks_sidebar():
    """Render streak information in sidebar."""
    with st.sidebar:
        st.markdown("### Streaks")

        streaks = get_all_streaks()
        at_risk = get_at_risk_streaks()
        at_risk_activities = {s["activity"] for s in at_risk}

        for streak in streaks:
            activity = streak["activity"]
            current = streak["current_streak"]
            longest = streak["longest_streak"]

            if activity in at_risk_activities:
                badge_class = "streak-at-risk"
                icon = "Warning"
            elif current > 0:
                badge_class = "streak-active"
                icon = ""
            else:
                badge_class = ""
                icon = ""

            st.markdown(
                f"""<div class="streak-badge {badge_class}">
                {activity}: {current} days (best: {longest})
                </div>""",
                unsafe_allow_html=True,
            )

        if not streaks:
            st.markdown("No streaks yet. Start planning!")
