"""
UI Styles
=========
Streamlit CSS styling for the voice UI.
"""

CUSTOM_CSS = """
<style>
    .item-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
        background: white;
    }
    .item-title {
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 0.25rem;
    }
    .item-meta {
        color: #666;
        font-size: 0.9rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: 500;
        margin-right: 0.5rem;
    }
    .badge-appointment { background: #e3f2fd; color: #1976d2; }
    .badge-meeting { background: #f3e5f5; color: #7b1fa2; }
    .badge-task { background: #fff3e0; color: #f57c00; }
    .badge-goal { background: #e8f5e9; color: #388e3c; }
    .badge-upcoming { background: #e0f2f1; color: #00897b; }
    .badge-in_progress { background: #fff9c4; color: #f57f17; }
    .badge-done { background: #c8e6c9; color: #2e7d32; }
    .badge-high { background: #ffebee; color: #c62828; }
    .badge-med { background: #fff3e0; color: #ef6c00; }
    .badge-low { background: #f1f8e9; color: #689f38; }
</style>
"""
