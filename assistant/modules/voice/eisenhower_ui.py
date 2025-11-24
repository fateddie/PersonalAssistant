"""
Eisenhower Matrix UI (Phase 3.5)
================================
2x2 grid visualization for task prioritization.
"""

import streamlit as st

# Import from behavioural_intelligence module
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from assistant.modules.behavioural_intelligence.bil_eisenhower import (
    get_tasks_by_quadrant,
    get_quadrant_info,
    update_task_quadrant,
    auto_classify_unclassified,
    QUADRANT_INFO,
)


# CSS for Eisenhower Matrix
EISENHOWER_CSS = """
<style>
.matrix-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
    margin-top: 1rem;
}
.quadrant {
    border-radius: 8px;
    padding: 1rem;
    min-height: 200px;
}
.quadrant-I { background: #fef2f2; border: 2px solid #ef4444; }
.quadrant-II { background: #f0fdf4; border: 2px solid #10b981; }
.quadrant-III { background: #fffbeb; border: 2px solid #f59e0b; }
.quadrant-IV { background: #f9fafb; border: 2px solid #6b7280; }
.quadrant-header {
    font-weight: bold;
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    color: #1f2937;
}
.quadrant-task {
    background: white;
    border-radius: 4px;
    padding: 0.5rem;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    color: #374151;
    box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}
.quadrant-empty {
    color: #9ca3af;
    font-style: italic;
    font-size: 0.85rem;
}
.matrix-legend {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}
.legend-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
    color: #1f2937;
}
.legend-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}
</style>
"""


def render_eisenhower_matrix():
    """Render the Eisenhower Matrix view."""
    st.markdown(EISENHOWER_CSS, unsafe_allow_html=True)

    st.markdown("### Eisenhower Matrix")
    st.markdown("*Prioritize tasks by urgency and importance*")

    # Auto-classify button
    col1, col2, col3 = st.columns([2, 2, 4])
    with col1:
        if st.button("Auto-Classify", help="Classify unassigned tasks based on priority"):
            count = auto_classify_unclassified()
            if count > 0:
                st.success(f"Classified {count} tasks")
                st.rerun()
            else:
                st.info("All tasks already classified")

    # Legend
    st.markdown(
        """
    <div class="matrix-legend">
        <div class="legend-item"><div class="legend-dot" style="background:#ef4444;"></div>Q1: Do First</div>
        <div class="legend-item"><div class="legend-dot" style="background:#10b981;"></div>Q2: Schedule</div>
        <div class="legend-item"><div class="legend-dot" style="background:#f59e0b;"></div>Q3: Delegate</div>
        <div class="legend-item"><div class="legend-dot" style="background:#6b7280;"></div>Q4: Eliminate</div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Get tasks
    tasks_by_quadrant = get_tasks_by_quadrant()

    # Render 2x2 grid using Streamlit columns
    st.markdown("---")

    # Labels row
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("**URGENT**")
    with col_right:
        st.markdown("**NOT URGENT**")

    # Top row: Important
    st.markdown("##### IMPORTANT")
    col_q1, col_q2 = st.columns(2)

    with col_q1:
        _render_quadrant("I", tasks_by_quadrant["I"])

    with col_q2:
        _render_quadrant("II", tasks_by_quadrant["II"])

    # Bottom row: Not Important
    st.markdown("##### NOT IMPORTANT")
    col_q3, col_q4 = st.columns(2)

    with col_q3:
        _render_quadrant("III", tasks_by_quadrant["III"])

    with col_q4:
        _render_quadrant("IV", tasks_by_quadrant["IV"])


def _render_quadrant(quadrant: str, tasks: list):
    """Render a single quadrant with its tasks."""
    info = QUADRANT_INFO[quadrant]

    # Quadrant container
    st.markdown(
        f"""<div class="quadrant quadrant-{quadrant}">
        <div class="quadrant-header" style="color:{info['color']};">
            Q{quadrant}: {info['name']}
        </div>
        <div style="font-size:0.75rem; color:#6b7280; margin-bottom:0.5rem;">
            {info['action']}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if tasks:
        for task in tasks[:5]:  # Limit to 5 per quadrant for display
            task_type_emoji = {
                "task": "",
                "goal": "",
                "deadline": "",
            }.get(task["type"], "")

            st.markdown(
                f"""<div class="quadrant-task">
                {task_type_emoji} {task['title']}
                </div>""",
                unsafe_allow_html=True,
            )

        if len(tasks) > 5:
            st.markdown(
                f"""<div class="quadrant-empty">
                +{len(tasks) - 5} more...
                </div>""",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """<div class="quadrant-empty">
            No tasks in this quadrant
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def render_quick_classify_widget():
    """
    Render a widget to quickly classify a task.
    For use in task detail views.
    """
    st.markdown("**Eisenhower Quadrant:**")
    quadrant = st.selectbox(
        "Select quadrant",
        options=["I", "II", "III", "IV"],
        format_func=lambda q: f"Q{q}: {QUADRANT_INFO[q]['name']}",
        key="quick_classify_quadrant",
        label_visibility="collapsed",
    )
    return quadrant
