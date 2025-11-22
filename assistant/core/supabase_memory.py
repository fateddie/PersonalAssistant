"""
Supabase Long-Term Memory for AskSharon.ai
===========================================
Connects personal tasks to ManagementTeam projects using
shared Supabase pgvector semantic memory layer.

Features:
- Store tasks with semantic embeddings
- Find related business projects
- Link tasks to projects
- Cross-system intelligence

Author: AskSharon.ai
Last Updated: 2025-11-12
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, date
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
load_dotenv(PROJECT_ROOT / "config" / ".env")

try:
    from supabase import create_client, Client
    from openai import OpenAI
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    # Define stub types when imports fail
    Client = None
    OpenAI = None
    print("⚠️  Warning: supabase or openai not installed")
    print("   Install with: pip install supabase openai")

# Initialize clients (lazy loading)
_supabase_client = None
_openai_client = None


def _get_supabase_client() -> Client:
    """Get or create Supabase client (anon key for user-level access)"""
    global _supabase_client

    if not DEPENDENCIES_AVAILABLE:
        raise ImportError("supabase package not installed")

    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")  # Use anon key for RLS

        if not supabase_url or not supabase_key:
            raise ValueError(
                "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_ANON_KEY in config/.env"
            )

        _supabase_client = create_client(supabase_url, supabase_key)
        print("✅ AskSharon connected to Supabase")

    return _supabase_client


def _get_openai_client() -> OpenAI:
    """Get or create OpenAI client"""
    global _openai_client

    if not DEPENDENCIES_AVAILABLE:
        raise ImportError("openai package not installed")

    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY in config/.env")

        _openai_client = OpenAI(api_key=api_key)

    return _openai_client


def generate_embedding(text: str) -> List[float]:
    """
    Generate OpenAI embedding for semantic search.

    Args:
        text: Text to embed

    Returns:
        1536-dimensional embedding vector
    """
    client = _get_openai_client()

    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )

    return response.data[0].embedding


def store_task_with_context(
    title: str,
    description: str = "",
    urgency: int = 3,
    importance: int = 3,
    effort: int = 3,
    project_reference: Optional[str] = None,
    due_date: Optional[date] = None
) -> int:
    """
    Store task with semantic memory for cross-system intelligence.

    Args:
        title: Task title
        description: Detailed description
        urgency: 1-5 (RICE scoring)
        importance: 1-5 (RICE scoring)
        effort: 1-5 (RICE scoring)
        project_reference: ManagementTeam project name (optional)
        due_date: Optional due date

    Returns:
        memory_id: ID in long_term_memory table

    Example:
        >>> memory_id = store_task_with_context(
        ...     title="Build AI Receptionist MVP",
        ...     description="Create working prototype",
        ...     urgency=5,
        ...     importance=5,
        ...     effort=4,
        ...     project_reference="AI_Receptionist"
        ... )
    """
    supabase = _get_supabase_client()

    # Create semantic content for embedding
    content = f"Task: {title}\nDescription: {description}"
    if project_reference:
        content += f"\nProject: {project_reference}"

    embedding = generate_embedding(content)

    # Prepare metadata
    metadata = {
        "urgency": urgency,
        "importance": importance,
        "effort": effort,
        "rice_score": (urgency * importance) / effort if effort > 0 else 0
    }

    # Store in long_term_memory
    memory_result = supabase.table("long_term_memory").insert({
        "content": content,
        "embedding": embedding,
        "source_system": "asksharon",
        "entity_type": "task",
        "entity_id": title,
        "user_id": "rob",
        "metadata": metadata
    }).execute()

    if not memory_result.data:
        raise Exception("Failed to store memory in Supabase")

    memory_id = memory_result.data[0]["id"]

    # Store in user_tasks table
    task_data = {
        "title": title,
        "description": description,
        "urgency": urgency,
        "importance": importance,
        "effort": effort,
        "project_reference": project_reference,
        "memory_id": memory_id
    }

    if due_date:
        task_data["due_date"] = due_date.isoformat()

    supabase.table("user_tasks").insert(task_data).execute()

    print(f"✅ Task stored: {title} (Memory ID: {memory_id})")
    return memory_id


def find_related_business_projects(
    task_description: str,
    limit: int = 5,
    min_similarity: float = 0.7
) -> List[Dict]:
    """
    Search ManagementTeam projects related to this task.

    Args:
        task_description: Natural language description
        limit: Maximum results
        min_similarity: Minimum cosine similarity threshold

    Returns:
        List of related project decisions from ManagementTeam

    Example:
        >>> projects = find_related_business_projects("dental clinic automation")
        >>> for p in projects:
        ...     print(f"{p['similarity']:.2f} - {p['metadata']['project']}")
    """
    supabase = _get_supabase_client()
    query_embedding = generate_embedding(task_description)

    result = supabase.rpc(
        "search_memory",
        {
            "query_embedding": query_embedding,
            "match_threshold": min_similarity,
            "match_count": limit,
            "filter_source_system": "management_team",
            "filter_entity_type": "project_decision"
        }
    ).execute()

    return result.data if result.data else []


def get_tasks_for_project(project_name: str, include_completed: bool = False) -> List[Dict]:
    """
    Get all AskSharon tasks linked to a ManagementTeam project.

    Args:
        project_name: ManagementTeam project name
        include_completed: Include completed tasks

    Returns:
        List of task records
    """
    supabase = _get_supabase_client()

    query = supabase.table("user_tasks")\
        .select("*")\
        .eq("project_reference", project_name)

    if not include_completed:
        query = query.eq("completed", False)

    result = query.order("urgency", desc=True).execute()
    return result.data if result.data else []


def get_my_active_tasks(limit: int = 20) -> List[Dict]:
    """
    Get user's active tasks sorted by RICE score.

    Args:
        limit: Maximum tasks to return

    Returns:
        List of active tasks
    """
    supabase = _get_supabase_client()

    result = supabase.table("user_tasks")\
        .select("*")\
        .eq("completed", False)\
        .order("urgency", desc=True)\
        .limit(limit)\
        .execute()

    return result.data if result.data else []


def complete_task(task_id: int) -> bool:
    """
    Mark task as completed.

    Args:
        task_id: Task ID

    Returns:
        True if successful
    """
    supabase = _get_supabase_client()

    result = supabase.table("user_tasks")\
        .update({
            "completed": True,
            "completed_at": datetime.now().isoformat()
        })\
        .eq("id", task_id)\
        .execute()

    if result.data:
        print(f"✅ Task {task_id} completed")
        return True
    return False


def link_task_to_project(task_id: int, project_name: str, relationship: str = "implements") -> int:
    """
    Create explicit link between AskSharon task and ManagementTeam project.

    Args:
        task_id: AskSharon task ID
        project_name: ManagementTeam project name
        relationship: 'implements', 'related_to', 'depends_on'

    Returns:
        link_id: ID in memory_links table
    """
    supabase = _get_supabase_client()

    # Get memory IDs
    task_memory = supabase.table("user_tasks")\
        .select("memory_id")\
        .eq("id", task_id)\
        .execute()

    project_memory = supabase.table("project_decisions")\
        .select("memory_id")\
        .eq("project_name", project_name)\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()

    if not task_memory.data or not project_memory.data:
        raise ValueError(f"Task {task_id} or project '{project_name}' not found")

    # Create link
    link_result = supabase.table("memory_links").insert({
        "memory_id_1": task_memory.data[0]["memory_id"],
        "memory_id_2": project_memory.data[0]["memory_id"],
        "relationship_type": relationship,
        "confidence": 0.9
    }).execute()

    link_id = link_result.data[0]["id"]
    print(f"✅ Linked task {task_id} → project '{project_name}'")
    return link_id


def get_project_context(project_name: str) -> Dict[str, Any]:
    """
    Get comprehensive context about a ManagementTeam project.

    Args:
        project_name: Project name

    Returns:
        Dictionary with project status, tasks, and related info
    """
    supabase = _get_supabase_client()

    # Get project decision
    project = supabase.table("project_decisions")\
        .select("*")\
        .eq("project_name", project_name)\
        .order("created_at", desc=True)\
        .limit(1)\
        .execute()

    if not project.data:
        return {"error": f"Project '{project_name}' not found"}

    # Get linked tasks
    tasks = get_tasks_for_project(project_name, include_completed=True)

    return {
        "project": project.data[0],
        "tasks": {
            "total": len(tasks),
            "pending": len([t for t in tasks if not t["completed"]]),
            "completed": len([t for t in tasks if t["completed"]]),
            "list": tasks
        }
    }


def search_my_memories(query: str, limit: int = 10) -> List[Dict]:
    """
    Semantic search across all personal memories (tasks, goals, etc).

    Args:
        query: Natural language query
        limit: Maximum results

    Returns:
        List of relevant memories
    """
    supabase = _get_supabase_client()
    query_embedding = generate_embedding(query)

    result = supabase.rpc(
        "search_memory",
        {
            "query_embedding": query_embedding,
            "match_threshold": 0.6,
            "match_count": limit,
            "filter_source_system": "asksharon",
            "filter_entity_type": None
        }
    ).execute()

    return result.data if result.data else []


# CLI entry point moved to supabase_cli.py
if __name__ == "__main__":
    from .supabase_cli import main
    main()
