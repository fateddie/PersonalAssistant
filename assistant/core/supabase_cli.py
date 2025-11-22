#!/usr/bin/env python3
"""
Supabase Memory CLI
===================
Command-line interface for testing Supabase memory integration.
"""

import sys
import argparse

from .supabase_memory import (
    DEPENDENCIES_AVAILABLE,
    _get_supabase_client,
    generate_embedding,
    store_task_with_context,
    get_my_active_tasks,
    find_related_business_projects,
    link_task_to_project,
    get_project_context,
)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="AskSharon Supabase Memory CLI")
    parser.add_argument("command", choices=["add-task", "list", "search", "link", "project", "test"])
    parser.add_argument("--title", help="Task title")
    parser.add_argument("--description", default="", help="Task description")
    parser.add_argument("--urgency", type=int, default=3, help="Urgency (1-5)")
    parser.add_argument("--importance", type=int, default=3, help="Importance (1-5)")
    parser.add_argument("--effort", type=int, default=3, help="Effort (1-5)")
    parser.add_argument("--project", help="Project reference")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--task-id", type=int, help="Task ID")

    args = parser.parse_args()

    if args.command == "add-task":
        if not args.title:
            print("❌ --title required")
            sys.exit(1)

        memory_id = store_task_with_context(
            title=args.title,
            description=args.description,
            urgency=args.urgency,
            importance=args.importance,
            effort=args.effort,
            project_reference=args.project
        )
        print(f"Memory ID: {memory_id}")

    elif args.command == "list":
        tasks = get_my_active_tasks(limit=10)
        print(f"\n📋 Active Tasks ({len(tasks)}):\n")
        for task in tasks:
            print(f"  [{task['id']}] {task['title']}")
            print(f"      U:{task['urgency']} I:{task['importance']} E:{task['effort']}")
            if task.get('project_reference'):
                print(f"      Project: {task['project_reference']}")
            print()

    elif args.command == "search":
        if not args.query:
            print("❌ --query required")
            sys.exit(1)

        # Search business projects
        projects = find_related_business_projects(args.query)
        print(f"\n🔍 Related Business Projects ({len(projects)}):\n")
        for p in projects:
            print(f"  {p['similarity']:.2f} - {p['metadata'].get('project', 'N/A')}")
            print(f"           Decision: {p['metadata'].get('decision', 'N/A')}\n")

    elif args.command == "link":
        if not args.task_id or not args.project:
            print("❌ --task-id and --project required")
            sys.exit(1)

        link_id = link_task_to_project(args.task_id, args.project)
        print(f"Link ID: {link_id}")

    elif args.command == "project":
        if not args.project:
            print("❌ --project required")
            sys.exit(1)

        context = get_project_context(args.project)
        if "error" in context:
            print(f"❌ {context['error']}")
        else:
            print(f"\n📊 Project: {args.project}")
            print(f"   Status: {context['project']['decision']}")
            print(f"   Agent: {context['project']['agent_name']}")
            print(f"\n📋 Tasks:")
            print(f"   Total: {context['tasks']['total']}")
            print(f"   Pending: {context['tasks']['pending']}")
            print(f"   Completed: {context['tasks']['completed']}\n")

    elif args.command == "test":
        print("🧪 Testing AskSharon Supabase integration...")
        try:
            client = _get_supabase_client()
            print("✅ Supabase connected")

            print("🧪 Testing embedding generation...")
            embedding = generate_embedding("Test task")
            print(f"✅ Generated {len(embedding)}-dimensional embedding")

            print("\n✅ All tests passed!")
        except Exception as e:
            print(f"❌ Test failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
