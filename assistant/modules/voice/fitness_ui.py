"""
Fitness UI (Phase 4)
====================
Streamlit UI for workout sessions, exercise logging, and progress tracking.
"""

import streamlit as st
from datetime import datetime
import time

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from assistant.modules.fitness.workout_session import (
    get_exercises,
    get_exercise_by_name,
    get_workout_templates,
    get_workout_template,
    start_workout_session,
    end_workout_session,
    cancel_workout_session,
    log_exercise_set,
    get_session_logs,
    get_active_session,
    get_recent_sessions,
    get_weekly_stats,
    suggest_adjustment,
    RPE_GUIDELINES,
)

# Custom CSS
FITNESS_CSS = """
<style>
.fitness-header {
    background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
    padding: 1.5rem;
    border-radius: 10px;
    color: white;
    margin-bottom: 1rem;
}
.workout-card {
    background: #fff7ed;
    border: 1px solid #fdba74;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.75rem;
    color: #1f2937;
}
.exercise-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 0.5rem;
    color: #1f2937;
}
.exercise-active {
    background: #fef3c7;
    border-color: #fcd34d;
}
.timer-display {
    font-size: 3rem;
    font-weight: bold;
    font-family: monospace;
    text-align: center;
    padding: 1rem;
    background: #1f2937;
    color: #22c55e;
    border-radius: 8px;
    margin: 1rem 0;
}
.timer-rest {
    background: #065f46;
    color: #a7f3d0;
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
    font-size: 1.5rem;
    font-weight: bold;
    color: #f97316;
}
.rpe-scale {
    display: flex;
    gap: 0.25rem;
    margin: 0.5rem 0;
}
.rpe-item {
    flex: 1;
    text-align: center;
    padding: 0.25rem;
    border-radius: 4px;
    font-size: 0.75rem;
    cursor: pointer;
}
.set-log {
    background: #f0fdf4;
    border-left: 3px solid #22c55e;
    padding: 0.5rem;
    margin: 0.25rem 0;
    font-size: 0.9rem;
    color: #1f2937;
}
</style>
"""


def render_fitness_tab():
    """Main entry point for fitness tab."""
    st.markdown(FITNESS_CSS, unsafe_allow_html=True)

    # Initialize session state
    if "fitness_view" not in st.session_state:
        st.session_state.fitness_view = "dashboard"

    # Header
    st.markdown(
        """<div class="fitness-header">
        <h2 style="margin:0;">Fitness Tracker</h2>
        <p style="margin:0.5rem 0 0 0; opacity:0.9;">Train smarter, track progress</p>
        </div>""",
        unsafe_allow_html=True,
    )

    # Check for active session
    active = get_active_session()

    # Navigation
    if active:
        st.info(f"Workout in progress: {active['template_name'] or 'Custom'}")
        if st.button("Continue Workout", type="primary", use_container_width=True):
            st.session_state.fitness_view = "workout"
            st.rerun()

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Dashboard", use_container_width=True):
            st.session_state.fitness_view = "dashboard"
            st.rerun()
    with col2:
        if st.button("Start Workout", use_container_width=True):
            st.session_state.fitness_view = "start"
            st.rerun()
    with col3:
        if st.button("Exercises", use_container_width=True):
            st.session_state.fitness_view = "exercises"
            st.rerun()

    st.markdown("---")

    # Render based on view
    if st.session_state.fitness_view == "dashboard":
        _render_dashboard()
    elif st.session_state.fitness_view == "start":
        _render_start_workout()
    elif st.session_state.fitness_view == "workout":
        _render_active_workout()
    elif st.session_state.fitness_view == "exercises":
        _render_exercises()


def _render_dashboard():
    """Render fitness dashboard with stats."""
    st.subheader("This Week's Progress")

    stats = get_weekly_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""<div class="stat-card">
            <div class="stat-number">{stats['sessions']}</div>
            <div>Workouts</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""<div class="stat-card">
            <div class="stat-number">{stats['total_minutes']}</div>
            <div>Minutes</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""<div class="stat-card">
            <div class="stat-number">{stats['total_sets']}</div>
            <div>Sets</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""<div class="stat-card">
            <div class="stat-number">{stats['avg_rpe'] or '-'}</div>
            <div>Avg RPE</div>
            </div>""",
            unsafe_allow_html=True,
        )

    if stats["top_muscle_group"]:
        st.markdown(f"**Most trained:** {stats['top_muscle_group'].replace('_', ' ').title()}")

    # Recent sessions
    st.markdown("---")
    st.subheader("Recent Workouts")

    sessions = get_recent_sessions(7)
    if sessions:
        for session in sessions[:5]:
            status_emoji = {"completed": "", "cancelled": "", "in_progress": ""}.get(
                session["status"], ""
            )
            st.markdown(
                f"""<div class="workout-card">
                <strong>{status_emoji} {session['template_name']}</strong><br>
                <small>{session['started_at'][:10]} • {session['duration_minutes'] or '?'} min
                {f" • RPE {session['overall_rpe']}" if session['overall_rpe'] else ""}</small>
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.info("No recent workouts. Start your first one!")


def _render_start_workout():
    """Render workout template selection."""
    st.subheader("Start a Workout")

    templates = get_workout_templates()

    if templates:
        st.markdown("**Choose a template:**")
        for template in templates:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(
                    f"""<div class="workout-card">
                    <strong>{template['name']}</strong><br>
                    <small>{template['description']}</small><br>
                    <small>{template['duration_minutes']} min • {template['difficulty']}</small>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with col2:
                if st.button("Start", key=f"start_{template['id']}", use_container_width=True):
                    session_id = start_workout_session(template["id"])
                    st.session_state.active_session_id = session_id
                    st.session_state.current_exercise_idx = 0
                    st.session_state.current_set = 1
                    st.session_state.fitness_view = "workout"
                    st.rerun()

    st.markdown("---")
    st.markdown("**Or start a custom workout:**")
    if st.button("Start Custom Workout", use_container_width=True):
        session_id = start_workout_session()
        st.session_state.active_session_id = session_id
        st.session_state.fitness_view = "workout"
        st.rerun()


def _render_active_workout():
    """Render active workout session."""
    active = get_active_session()

    if not active:
        st.warning("No active workout session.")
        st.session_state.fitness_view = "dashboard"
        st.rerun()
        return

    session_id = active["id"]
    template = None
    exercises_plan = []

    if active["template_id"]:
        template = get_workout_template(active["template_id"])
        if template:
            exercises_plan = template.get("exercises", [])

    # Session header
    st.markdown(f"### {active['template_name'] or 'Custom Workout'}")
    st.markdown(f"**Elapsed:** {active['elapsed_minutes']:.0f} minutes")

    # Get logged sets
    logs = get_session_logs(session_id)

    # Guided workout view
    if exercises_plan:
        _render_guided_workout(session_id, exercises_plan, logs)
    else:
        _render_free_workout(session_id, logs)

    # End/Cancel buttons
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("End Workout", type="primary", use_container_width=True):
            st.session_state.show_end_form = True
    with col2:
        if st.button("Cancel Workout", use_container_width=True):
            cancel_workout_session(session_id)
            st.session_state.fitness_view = "dashboard"
            st.rerun()

    # End workout form
    if st.session_state.get("show_end_form"):
        with st.form("end_workout_form"):
            st.markdown("**Rate your workout:**")
            rpe = st.slider("Overall RPE (1-10)", 1, 10, 7)
            st.caption(RPE_GUIDELINES.get(rpe, ""))
            notes = st.text_area("Notes (optional)", height=80)

            if st.form_submit_button("Complete Workout"):
                end_workout_session(session_id, rpe, notes)
                suggestion = suggest_adjustment(rpe)
                st.success(f"Workout complete! {suggestion}")
                st.session_state.show_end_form = False
                st.session_state.fitness_view = "dashboard"
                time.sleep(2)
                st.rerun()


def _render_guided_workout(session_id: int, exercises_plan: list, logs: list):
    """Render guided workout with exercise list and timer."""

    # Initialize state
    if "current_exercise_idx" not in st.session_state:
        st.session_state.current_exercise_idx = 0
    if "current_set" not in st.session_state:
        st.session_state.current_set = 1

    # Current exercise
    idx = st.session_state.current_exercise_idx
    if idx >= len(exercises_plan):
        st.success("All exercises complete!")
        return

    current = exercises_plan[idx]
    exercise_data = get_exercise_by_name(current["exercise"])

    # Progress indicator
    st.progress((idx + 1) / len(exercises_plan))
    st.markdown(f"**Exercise {idx + 1} of {len(exercises_plan)}**")

    # Current exercise display
    st.markdown(
        f"""<div class="exercise-card exercise-active">
        <h3 style="margin:0;">{current['exercise']}</h3>
        <p style="margin:0.5rem 0;">
            {"Sets: " + str(current.get('sets', 1)) + " • " if current.get('sets') else ""}
            {"Reps: " + str(current.get('reps')) if current.get('reps') else ""}
            {"Duration: " + str(current.get('duration')) + "s" if current.get('duration') else ""}
        </p>
        <small>Rest: {current.get('rest', 30)}s between sets</small>
        </div>""",
        unsafe_allow_html=True,
    )

    # Set tracker
    total_sets = current.get("sets", 1)
    current_set = st.session_state.current_set

    st.markdown(f"**Set {current_set} of {total_sets}**")

    # Log set form
    with st.form(f"log_set_{idx}_{current_set}"):
        col1, col2 = st.columns(2)
        with col1:
            if current.get("reps"):
                reps = st.number_input("Reps completed", min_value=0, value=current.get("reps", 10))
            else:
                reps = None
        with col2:
            rpe = st.slider("RPE", 1, 10, 7)

        if st.form_submit_button("Log Set", use_container_width=True):
            if exercise_data:
                log_exercise_set(
                    session_id=session_id,
                    exercise_id=exercise_data["id"],
                    set_number=current_set,
                    reps=reps,
                    duration_seconds=current.get("duration"),
                    rpe=rpe,
                )

                if current_set >= total_sets:
                    st.session_state.current_exercise_idx += 1
                    st.session_state.current_set = 1
                else:
                    st.session_state.current_set += 1

                st.rerun()

    # Show completed sets
    exercise_logs = [
        log for log in logs if exercise_data and log["exercise_id"] == exercise_data["id"]
    ]
    if exercise_logs:
        st.markdown("**Completed sets:**")
        for log in exercise_logs:
            st.markdown(
                f"""<div class="set-log">
                Set {log['set_number']}: {log['reps'] or '-'} reps @ RPE {log['rpe'] or '-'}
                </div>""",
                unsafe_allow_html=True,
            )


def _render_free_workout(session_id: int, logs: list):
    """Render free-form workout logging."""
    st.subheader("Log Your Exercises")

    exercises = get_exercises()
    exercise_options = {ex["name"]: ex["id"] for ex in exercises}

    with st.form("log_exercise"):
        exercise_name = st.selectbox("Exercise", options=list(exercise_options.keys()))
        col1, col2, col3 = st.columns(3)
        with col1:
            set_number = st.number_input("Set #", min_value=1, value=1)
        with col2:
            reps = st.number_input("Reps", min_value=0, value=10)
        with col3:
            rpe = st.slider("RPE", 1, 10, 7)

        if st.form_submit_button("Log Set"):
            exercise_id = exercise_options[exercise_name]
            log_exercise_set(
                session_id=session_id,
                exercise_id=exercise_id,
                set_number=set_number,
                reps=reps,
                rpe=rpe,
            )
            st.success("Set logged!")
            st.rerun()

    # Show logged exercises
    if logs:
        st.markdown("---")
        st.markdown("**Logged sets:**")
        for log in logs:
            st.markdown(
                f"""<div class="set-log">
                {log['exercise_name']} - Set {log['set_number']}: {log['reps'] or '-'} reps @ RPE {log['rpe'] or '-'}
                </div>""",
                unsafe_allow_html=True,
            )


def _render_exercises():
    """Render exercise library."""
    st.subheader("Exercise Library")

    exercises = get_exercises()

    # Group by category
    categories = {}
    for ex in exercises:
        cat = ex["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ex)

    for category, exs in sorted(categories.items()):
        with st.expander(f"{category.title()} ({len(exs)} exercises)"):
            for ex in exs:
                st.markdown(
                    f"""<div class="exercise-card">
                    <strong>{ex['name']}</strong><br>
                    <small>{ex['muscle_group'].replace('_', ' ').title()} • {ex['equipment']}</small><br>
                    <small style="color:#6b7280;">{ex['description']}</small>
                    </div>""",
                    unsafe_allow_html=True,
                )
