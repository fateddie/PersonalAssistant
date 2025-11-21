"""
Quick API Test
==============
Tests the unified Assistant API
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from assistant.modules.voice.api_client import AssistantAPIClient

# Initialize client (API should be running on port 8002)
client = AssistantAPIClient(base_url="http://localhost:8002")

print("=" * 60)
print("TESTING ASSISTANT API")
print("=" * 60)

# Test 1: Health check
print("\n1. Health Check")
print("-" * 60)
health = client.health_check()
print(f"Status: {health['status']}")
print(f"Version: {health['version']}")

# Test 2: Get stats
print("\n2. Dashboard Stats")
print("-" * 60)
stats = client.get_stats()
print(f"Total items by type:")
for item_type, count in stats['count_by_type'].items():
    print(f"  {item_type}: {count}")

print(f"\nToday's items: {stats['today']['total']}")
for item_type, count in stats['today']['by_type'].items():
    print(f"  {item_type}: {count}")

# Test 3: List items (with filters)
print("\n3. List Items (filtered)")
print("-" * 60)

# Get tasks
result = client.list_items(type=["task"], limit=5)
print(f"\nTasks ({result['total']} total):")
for item in result['items'][:3]:
    print(f"  - {item['title']} ({item['status']})")

# Get today's upcoming items
from datetime import date
today = date.today()
result = client.list_items(
    date_from=today,
    date_to=today,
    status="upcoming",
    limit=10
)
print(f"\nToday's upcoming items ({result['total']} total):")
for item in result['items'][:5]:
    time_str = item['start_time'] or "no time"
    print(f"  - {time_str}: {item['title']} ({item['type']})")

# Test 4: Get single item
print("\n4. Get Single Item")
print("-" * 60)
if result['items']:
    first_item = result['items'][0]
    item = client.get_item(first_item['id'])
    print(f"ID: {item['id']}")
    print(f"Title: {item['title']}")
    print(f"Type: {item['type']}")
    print(f"Status: {item['status']}")
    if item['participants']:
        print(f"Participants: {', '.join(item['participants'])}")

# Test 5: Create new item
print("\n5. Create New Item")
print("-" * 60)
new_item = client.create_item({
    "type": "task",
    "title": "Test API integration",
    "description": "Verify API client works correctly",
    "date": str(today),
    "status": "upcoming",
    "source": "manual",
    "priority": "high"
})
print(f"Created item: {new_item['id']}")
print(f"  Title: {new_item['title']}")
print(f"  Priority: {new_item['priority']}")

# Test 6: Update item
print("\n6. Update Item")
print("-" * 60)
updated = client.update_item(new_item['id'], {
    "status": "done",
    "description": "API integration test completed successfully!"
})
print(f"Updated item: {updated['id']}")
print(f"  Status: {updated['status']}")
print(f"  Description: {updated['description']}")

# Test 7: Delete item
print("\n7. Delete Item")
print("-" * 60)
client.delete_item(new_item['id'])
print(f"Deleted item: {new_item['id']}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✅")
print("=" * 60)
