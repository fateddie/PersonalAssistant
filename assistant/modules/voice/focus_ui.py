"""
Focus & Mindset UI (Phase 3.5 Week 4)
=====================================
UI for Pomodoro timer, CBT thought logs, and energy tracking.
"""

import streamlit as st
from datetime import datetime

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from assistant.modules.behavioural_intelligence.bil_pomodoro import (
    start_pomodoro,
    complete_pomodoro,
    cancel_pomodoro,
    record_interruption,
    get_active_pomodoro,
    get_todays_pomodoros,
    get_pomodoro_stats,
    suggest_break_type,
    POMODORO_DURATION,
)
from assistant.modules.behavioural_intelligence.bil_cbt import (
    create_thought_log,
    update_thought_log,
    get_thought_logs,
    get_distortion_list,
    get_distortion_stats,
    suggest_reframe,
    get_quick_challenges,
    COGNITIVE_DISTORTIONS,
)
from assistant.modules.behavioural_intelligence.bil_energy import (
    record_energy,
    get_todays_energy,
    get_energy_history,
    get_energy_patterns,
    get_energy_recommendations,
    ENERGY_LABELS,
)


# Custom CSS
FOCUS_CSS = """
<style>
.pomodoro-timer {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    padding: 2rem;
    border-radius: 12px;
    color: white;
    text-align: center;
}
.pomodoro-time {
    font-size: 3rem;
    font-weight: bold;
    font-family: monospace;
}
.pomodoro-status {
    font-size: 1rem;
    opacity: 0.9;
    margin-top: 0.5rem;
}
.break-timer {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}
.thought-card {
    background: #fffbeb;
    border: 1px solid #fcd34d;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    color: #1f2937;
}
.thought-complete {
    background: #f0fdf4;
    border-color: #86efac;
}
.distortion-tag {
    display: inline-block;
    background: #fef3c7;
    border-radius: 12px;
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    color: #92400e;
}
.energy-bar {
    height: 20px;
    background: #e5e7eb;
    border-radius: 10px;
    overflow: hidden;
}
.energy-fill {
    height: 100%;
    border-radius: 10px;
}
.energy-1 { background: #ef4444; }
.energy-2 { background: #f97316; }
.energy-3 { background: #eab308; }
.energy-4 { background: #84cc16; }
.energy-5 { background: #22c55e; }
.stat-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    color: #1f2937;
}
.stat-number {
    font-size: 1.5rem;
    font-weight: bold;
    color: #4f46e5;
}
</style>
"""


def render_focus_tab():
    """Main entry point for focus/mindset tab."""
    st.markdown(FOCUS_CSS, unsafe_allow_html=True)

    # Sub-navigation
    if "focus_view" not in st.session_state:
        st.session_state.focus_view = "pomodoro"

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Pomodoro", use_container_width=True):
            st.session_state.focus_view = "pomodoro"
            st.rerun()
    with col2:
        if st.button("Thought Log", use_container_width=True):
            st.session_state.focus_view = "cbt"
            st.rerun()
    with col3:
        if st.button("Energy", use_container_width=True):
            st.session_state.focus_view = "energy"
            st.rerun()

    st.markdown("---")

    if st.session_state.focus_view == "pomodoro":
        _render_pomodoro()
    elif st.session_state.focus_view == "cbt":
        _render_cbt()
    elif st.session_state.focus_view == "energy":
        _render_energy()


def _render_pomodoro():
    """Render Pomodoro timer view."""
    st.markdown("### Pomodoro Timer")

    # Check for active session
    active = get_active_pomodoro()

    if active:
        # Timer display
        remaining = active["remaining_minutes"]
        minutes = int(remaining)
        seconds = int((remaining - minutes) * 60)

        timer_class = "pomodoro-timer"
        if active["is_complete"]:
            timer_class += " break-timer"

        st.markdown(
            f"""<div class="{timer_class}">
            <div class="pomodoro-time">{minutes:02d}:{seconds:02d}</div>
            <div class="pomodoro-status">
                {'Session complete!' if active['is_complete'] else 'Focus time...'}
            </div>
            <div style="margin-top:0.5rem;">Interruptions: {active['interruptions']}</div>
            </div>""",
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            if active["is_complete"]:
                if st.button("Complete", type="primary", use_container_width=True):
                    notes = st.session_state.get("pomodoro_notes", "")
                    complete_pomodoro(active["id"], notes)
                    break_info = suggest_break_type()
                    st.success(break_info["message"])
                    st.rerun()
            else:
                if st.button("Record Interruption", use_container_width=True):
                    count = record_interruption(active["id"])
                    st.warning(f"Interruption #{count} recorded")
                    st.rerun()
        with col2:
            if st.button("Cancel Session", use_container_width=True):
                cancel_pomodoro(active["id"])
                st.info("Session cancelled")
                st.rerun()
        with col3:
            if active["is_complete"]:
                st.text_input("Notes", key="pomodoro_notes", placeholder="What did you accomplish?")

    else:
        # Start new session
        st.markdown("Ready to focus?")

        col1, col2 = st.columns([2, 1])
        with col1:
            duration = st.slider("Duration (minutes)", 15, 60, POMODORO_DURATION)
        with col2:
            if st.button("Start Pomodoro", type="primary", use_container_width=True):
                session_id = start_pomodoro(duration_minutes=duration)
                st.success("Pomodoro started! Focus time.")
                st.rerun()

    # Today's sessions
    st.markdown("---")
    st.subheader("Today's Sessions")

    sessions = get_todays_pomodoros()
    if sessions:
        for session in sessions[:5]:
            status = "Completed" if session["completed"] else "Abandoned"
            st.markdown(
                f"- **{session['task_title'] or 'Focus session'}** - {session['duration_minutes']}min ({status})"
            )
    else:
        st.info("No sessions today yet.")

    # Stats
    st.markdown("---")
    st.subheader("This Week's Stats")

    stats = get_pomodoro_stats(days=7)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"""<div class="stat-card">
            <div class="stat-number">{stats['completed']}</div>
            <div>Completed</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class="stat-card">
            <div class="stat-number">{stats['total_focus_hours']}h</div>
            <div>Focus Time</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""<div class="stat-card">
            <div class="stat-number">{stats['avg_interruptions']}</div>
            <div>Avg Interruptions</div>
            </div>""",
            unsafe_allow_html=True,
        )


def _render_cbt():
    """Render CBT thought log view."""
    st.markdown("### Thought Log")
    st.markdown("*Challenge unhelpful thoughts*")

    # Quick challenges
    with st.expander("Quick Thought Challenges"):
        challenges = get_quick_challenges()
        for c in challenges:
            st.markdown(f"- {c['question']}")

    # New thought log
    st.subheader("Log a Thought")

    with st.form("new_thought_log"):
        situation = st.text_input(
            "What triggered this thought?",
            placeholder="e.g., About to present to the team",
        )
        automatic_thought = st.text_area(
            "What automatic thought came up?",
            placeholder="e.g., I'm going to mess this up and everyone will judge me",
            height=80,
        )

        distortions = get_distortion_list()
        distortion_options = ["None"] + [d["name"] for d in distortions]
        selected_distortion = st.selectbox(
            "What cognitive distortion might this be?",
            options=distortion_options,
            help="Common thinking patterns that aren't helpful",
        )

        # Show distortion info
        if selected_distortion != "None":
            for d in distortions:
                if d["name"] == selected_distortion:
                    st.info(f"**{d['name']}**: {d['description']}\n\nExample: *{d['example']}*")
                    break

        st.markdown("---")
        st.markdown("**Challenge the thought:**")

        evidence_for = st.text_input(
            "Evidence supporting the thought",
            placeholder="What facts support this?",
        )
        evidence_against = st.text_input(
            "Evidence against the thought",
            placeholder="What facts contradict this?",
        )
        reframe = st.text_area(
            "A more balanced thought",
            placeholder="e.g., I've prepared well and some nervousness is normal",
            height=60,
        )

        if st.form_submit_button("Save Thought Log", type="primary"):
            if situation.strip() and automatic_thought.strip():
                distortion_key = None
                if selected_distortion != "None":
                    for d in distortions:
                        if d["name"] == selected_distortion:
                            distortion_key = d["key"]
                            break

                create_thought_log(
                    situation=situation.strip(),
                    automatic_thought=automatic_thought.strip(),
                    cognitive_distortion=distortion_key,
                    evidence_for=evidence_for.strip() if evidence_for else None,
                    evidence_against=evidence_against.strip() if evidence_against else None,
                    reframe=reframe.strip() if reframe else None,
                )
                st.success("Thought logged!")
                st.rerun()
            else:
                st.error("Please enter the situation and automatic thought.")

    # Recent logs
    st.markdown("---")
    st.subheader("Recent Thought Logs")

    logs = get_thought_logs(days=7)
    if logs:
        for log in logs[:5]:
            card_class = "thought-card thought-complete" if log["is_complete"] else "thought-card"
            distortion_html = ""
            if log["cognitive_distortion"]:
                distortion_name = COGNITIVE_DISTORTIONS.get(log["cognitive_distortion"], {}).get(
                    "name", log["cognitive_distortion"]
                )
                distortion_html = f'<span class="distortion-tag">{distortion_name}</span>'

            st.markdown(
                f"""<div class="{card_class}">
                <strong>Situation:</strong> {log['situation']}<br>
                <strong>Thought:</strong> {log['automatic_thought']}<br>
                {distortion_html}
                {f"<br><strong>Reframe:</strong> {log['reframe']}" if log['reframe'] else ""}
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.info("No thought logs yet. Start journaling!")

    # Distortion patterns
    st.markdown("---")
    st.subheader("Your Patterns")

    stats = get_distortion_stats(days=30)
    if stats:
        st.markdown("Most common thought patterns:")
        for distortion, count in list(stats.items())[:3]:
            name = COGNITIVE_DISTORTIONS.get(distortion, {}).get("name", distortion)
            st.markdown(f"- **{name}**: {count} occurrences")
    else:
        st.info("Log more thoughts to see patterns.")


def _render_energy():
    """Render energy tracking view."""
    st.markdown("### Energy Tracking")
    st.markdown("*Track your energy to optimize your day*")

    # Today's energy
    st.subheader("How's your energy right now?")

    current = get_todays_energy()
    now = datetime.now()
    time_period = "am" if now.hour < 12 else "pm"

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Morning Energy**")
        am_level = st.slider(
            "AM Energy",
            1,
            5,
            value=current["am"] or 3,
            key="energy_am_slider",
            label_visibility="collapsed",
        )
        st.markdown(f"*{ENERGY_LABELS[am_level]}*")

        if time_period == "am":
            if st.button("Save AM Energy", use_container_width=True):
                record_energy(am_level, "am")
                st.success("AM energy recorded!")
                st.rerun()

    with col2:
        st.markdown("**Afternoon Energy**")
        pm_level = st.slider(
            "PM Energy",
            1,
            5,
            value=current["pm"] or 3,
            key="energy_pm_slider",
            label_visibility="collapsed",
        )
        st.markdown(f"*{ENERGY_LABELS[pm_level]}*")

        if time_period == "pm":
            if st.button("Save PM Energy", use_container_width=True):
                record_energy(pm_level, "pm")
                st.success("PM energy recorded!")
                st.rerun()

    # Energy history visualization
    st.markdown("---")
    st.subheader("Recent Energy Levels")

    history = get_energy_history(days=7)
    if history:
        for day in history:
            st.markdown(f"**{day['date']}**")
            col1, col2 = st.columns(2)
            with col1:
                if day["am"]:
                    st.markdown(
                        f"""<div class="energy-bar">
                        <div class="energy-fill energy-{day['am']}" style="width:{day['am']*20}%;"></div>
                        </div>
                        <small>AM: {ENERGY_LABELS[day['am']]}</small>""",
                        unsafe_allow_html=True,
                    )
            with col2:
                if day["pm"]:
                    st.markdown(
                        f"""<div class="energy-bar">
                        <div class="energy-fill energy-{day['pm']}" style="width:{day['pm']*20}%;"></div>
                        </div>
                        <small>PM: {ENERGY_LABELS[day['pm']]}</small>""",
                        unsafe_allow_html=True,
                    )
    else:
        st.info("Start tracking to see your energy history.")

    # Patterns & recommendations
    st.markdown("---")
    st.subheader("Insights")

    patterns = get_energy_patterns()
    recommendations = get_energy_recommendations()

    if patterns["avg_am"] or patterns["avg_pm"]:
        col1, col2 = st.columns(2)
        with col1:
            if patterns["avg_am"]:
                st.metric("Avg Morning Energy", f"{patterns['avg_am']}/5")
        with col2:
            if patterns["avg_pm"]:
                st.metric("Avg Afternoon Energy", f"{patterns['avg_pm']}/5")

        if patterns["best_day"]:
            st.markdown(f"**Best day:** {patterns['best_day']}")

    st.markdown("**Recommendations:**")
    for rec in recommendations:
        st.markdown(f"- {rec}")
