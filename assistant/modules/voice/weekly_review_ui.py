"""
Weekly Review UI (Phase 3.5 Week 3)
===================================
GTD-style weekly review interface.
"""

import streamlit as st
from datetime import date, timedelta

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from assistant.modules.behavioural_intelligence.bil_weekly_review import (
    get_week_stats,
    get_incomplete_items,
    get_wins_this_week,
    get_streak_summary,
    save_weekly_review,
    get_last_weekly_review,
)


# Custom CSS
REVIEW_CSS = """
<style>
.review-header {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
    padding: 1.5rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 1rem;
}
.stat-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    color: #1f2937;
}
.stat-number {
    font-size: 2rem;
    font-weight: bold;
    color: #4f46e5;
}
.stat-label {
    font-size: 0.85rem;
    color: #6b7280;
}
.win-card {
    background: #f0fdf4;
    border-left: 4px solid #10b981;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border-radius: 0 8px 8px 0;
    color: #1f2937;
}
.incomplete-card {
    background: #fef2f2;
    border-left: 4px solid #ef4444;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border-radius: 0 8px 8px 0;
    color: #1f2937;
}
.section-header {
    background: #f1f5f9;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    margin: 1rem 0 0.5rem 0;
    font-weight: 600;
    color: #1f2937;
}
</style>
"""


def render_weekly_review():
    """Render the weekly review interface."""
    st.markdown(REVIEW_CSS, unsafe_allow_html=True)

    # Header
    today = date.today()
    week_start = today - timedelta(days=today.weekday() + 1)
    week_end = week_start + timedelta(days=6)

    st.markdown(
        f"""<div class="review-header">
        <h2 style="margin:0;">Weekly Review</h2>
        <p style="margin:0.5rem 0 0 0; opacity:0.9;">
            Week of {week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}
        </p>
        </div>""",
        unsafe_allow_html=True,
    )

    # Check for existing review
    last_review = get_last_weekly_review()
    if last_review and last_review["week_start"] == week_start.isoformat():
        st.success("Weekly review completed for this week!")
        with st.expander("View this week's review"):
            st.markdown("**Wins:**")
            for win in last_review["wins"]:
                st.markdown(f"- {win}")
            st.markdown("**Lessons:**")
            for lesson in last_review["lessons"]:
                st.markdown(f"- {lesson}")
            st.markdown(f"**Next week focus:** {last_review['next_week_focus']}")
        st.markdown("---")

    # Stats section
    st.markdown('<div class="section-header">This Week\'s Stats</div>', unsafe_allow_html=True)
    stats = get_week_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""<div class="stat-card">
            <div class="stat-number">{stats['tasks_completed']}</div>
            <div class="stat-label">Tasks Done</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        habit_pct = (
            int(stats["habits_completed"] / stats["habits_total"] * 100)
            if stats["habits_total"] > 0
            else 0
        )
        st.markdown(
            f"""<div class="stat-card">
            <div class="stat-number">{habit_pct}%</div>
            <div class="stat-label">Habit Rate</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""<div class="stat-card">
            <div class="stat-number">{stats['evening_plans_completed']}</div>
            <div class="stat-label">Evening Plans</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""<div class="stat-card">
            <div class="stat-number">{stats['brain_dump_items_processed']}</div>
            <div class="stat-label">Inbox Cleared</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # Wins section
    st.markdown('<div class="section-header">Wins This Week</div>', unsafe_allow_html=True)
    wins = get_wins_this_week()

    if wins:
        for win in wins[:10]:
            type_emoji = {"task": "", "goal": "", "deadline": ""}.get(win["type"], "")
            st.markdown(
                f"""<div class="win-card">
                {type_emoji} {win['title']}
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.info("No completed items this week yet.")

    # Incomplete items
    st.markdown('<div class="section-header">Items Needing Attention</div>', unsafe_allow_html=True)
    incomplete = get_incomplete_items()

    if incomplete["overdue_tasks"]:
        st.markdown("**Overdue Tasks:**")
        for item in incomplete["overdue_tasks"][:5]:
            st.markdown(
                f"""<div class="incomplete-card">
                {item['title']} (due: {item['date']})
                </div>""",
                unsafe_allow_html=True,
            )

    if incomplete["stale_goals"]:
        st.markdown("**Stale Goals (no progress in 2 weeks):**")
        for item in incomplete["stale_goals"][:5]:
            st.markdown(
                f"""<div class="incomplete-card">
                {item['title']}
                </div>""",
                unsafe_allow_html=True,
            )

    if incomplete["unprocessed_thoughts"]:
        st.warning(f"{len(incomplete['unprocessed_thoughts'])} items in Brain Dump inbox")

    if not any([incomplete["overdue_tasks"], incomplete["stale_goals"]]):
        st.success("All caught up!")

    # Streaks
    st.markdown('<div class="section-header">Streak Summary</div>', unsafe_allow_html=True)
    streaks = get_streak_summary()

    if streaks:
        cols = st.columns(min(len(streaks), 4))
        for i, streak in enumerate(streaks[:4]):
            with cols[i]:
                st.metric(
                    streak["activity"],
                    f"{streak['current_streak']} days",
                    delta=f"Best: {streak['longest_streak']}",
                )
    else:
        st.info("No streaks recorded yet.")

    # Review form
    st.markdown("---")
    st.markdown('<div class="section-header">Complete Your Review</div>', unsafe_allow_html=True)

    with st.form("weekly_review_form"):
        st.markdown("**What were your wins this week?**")
        win1 = st.text_input("Win 1", key="win1", placeholder="Completed project milestone...")
        win2 = st.text_input("Win 2", key="win2", placeholder="Maintained exercise streak...")
        win3 = st.text_input("Win 3", key="win3", placeholder="Had productive 1:1 meeting...")

        st.markdown("**What did you learn?**")
        lesson1 = st.text_input(
            "Lesson 1", key="lesson1", placeholder="Time blocking works better in morning..."
        )
        lesson2 = st.text_input(
            "Lesson 2", key="lesson2", placeholder="Need more breaks during deep work..."
        )

        st.markdown("**What's your main focus for next week?**")
        next_focus = st.text_input(
            "Next week focus",
            key="next_focus",
            placeholder="Ship feature X by Wednesday",
        )

        obstacles = st.text_area(
            "What obstacles do you anticipate?",
            key="obstacles",
            height=80,
            placeholder="Back-to-back meetings on Monday...",
        )

        if st.form_submit_button(
            "Complete Weekly Review", type="primary", use_container_width=True
        ):
            wins_list = [w for w in [win1, win2, win3] if w.strip()]
            lessons_list = [l for l in [lesson1, lesson2] if l.strip()]

            if not wins_list:
                st.error("Please enter at least one win.")
            elif not next_focus.strip():
                st.error("Please enter your focus for next week.")
            else:
                save_weekly_review(
                    wins=wins_list,
                    lessons=lessons_list,
                    next_week_focus=next_focus.strip(),
                    obstacles_anticipated=obstacles.strip() if obstacles else None,
                )
                st.success("Weekly review completed!")
                st.balloons()
                st.rerun()
