"""
Conversational AI Module
========================
Multi-turn conversation workflows for task and appointment creation.

Patterns:
- Slot-filling: Collect required fields through dialog
- OpenAI extraction: Parse natural language ("tomorrow" → "2025-11-16")
- State management: Track conversation progress

Usage:
    workflow = TaskWorkflow()
    while not workflow.is_complete():
        question = workflow.get_next_question()
        user_response = get_user_input()
        workflow.process_response(user_response)

    task_data = workflow.to_dict()
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from openai import OpenAI
from dotenv import load_dotenv

# Load environment
load_dotenv("config/.env")


class TaskWorkflow:
    """
    Multi-turn conversation workflow for task creation.

    Required fields:
    - title: str
    - urgency: int (1-5)
    - importance: int (1-5)

    Optional fields:
    - deadline: str (ISO date)
    - project: str
    - category: str
    - notes: str
    - tags: str
    - context: str
    """

    def __init__(self):
        self.fields = {
            'title': None,
            'urgency': None,
            'importance': None,
            'effort': 3,  # Default to medium effort
            'deadline': None,
            'project': None,
            'category': None,
            'notes': None,
            'tags': None,
            'context': None
        }
        self.category_asked = False  # Track if we've asked about category
        self.project_asked = False  # Track if we've asked about project
        self.additional_offered = False  # Track if we've offered additional fields
        self.upfront_extraction_done = False  # Track if we've done upfront extraction
        self.recurring_pattern = None  # Store detected recurring pattern
        self.understood_fields = []  # Track what fields were extracted from initial message
        self.confirmation_asked = False  # Track if we've asked for confirmation
        self.user_confirmed = False  # Track if user confirmed the task
        self.suggestion_pending = None  # Track if a suggestion is waiting for response
        self.user_wants_goal = False  # Track if user wants to create a goal instead
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def extract_all_fields(self, user_input: str) -> Dict[str, Any]:
        """
        Extract ALL possible fields from initial message using OpenAI.

        This is the Phase 1 improvement: Parse the entire message upfront
        instead of asking for each field sequentially.

        Extracts:
        - title: What is the task?
        - deadline: When is it due?
        - priority: urgency/importance indicators
        - category: personal/business/learning/health
        - project: Which project (if business)
        - duration: How long will it take?
        - recurring: Is this a recurring task? (days of week, frequency)
        - notes/tags/context: Additional metadata

        Returns:
            {
                "extracted": {field: value, ...},
                "missing": [field1, field2, ...],
                "recurring_pattern": {...} or None,
                "suggestion": str (e.g., "This looks like a recurring task - would you like to create a goal instead?")
            }
        """
        if not self.client:
            # Fallback: Just extract title
            print("⚠️  No OpenAI client, using minimal extraction")
            self.fields['title'] = user_input.strip()
            self.understood_fields.append('title')
            return {
                "extracted": {"title": user_input.strip()},
                "missing": ["deadline", "priority"],
                "recurring_pattern": None,
                "suggestion": None
            }

        try:
            today = datetime.now().strftime("%Y-%m-%d")
            day_of_week = datetime.now().strftime("%A")

            print(f"🔍 Extracting all fields from: '{user_input}'")

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"""Today is {today} ({day_of_week}). Extract ALL possible task fields from user input.

Return a JSON object with these fields (omit if not mentioned):

**Required fields:**
- title: str - What is the task? (REQUIRED - extract even if vague)
- urgency: int (1-5) - How urgent? 5=ASAP, 3=medium, 1=no rush
- importance: int (1-5) - How important? 5=critical to goals, 3=medium, 1=low priority

**Optional fields:**
- deadline: str (YYYY-MM-DD) - When is it due?
- category: str - "personal", "business", "learning", or "health"
- project: str - Which project/area? (only if category is business)
- duration: int - How long will it take (in minutes)?
- notes: str - Any additional context
- tags: str - Keywords (comma-separated)
- context: str - Where/when can this be done?

**Recurring pattern detection:**
- recurring_days: list[str] - ["monday", "tuesday", "friday"] if recurring
- recurring_frequency: str - "daily", "weekly", "weekdays", etc.
- recurring_duration: int - Duration per session (minutes)

**Priority mapping guidelines:**
- "critical", "urgent and important", "ASAP" → urgency=5, importance=5
- "urgent", "soon", "immediately" → urgency=5, importance=3
- "important", "key", "strategic" → urgency=3, importance=5
- "low", "minor", "not urgent" → urgency=2, importance=2

**Examples:**

Input: "learn AI MOOC monday tuesday thursday friday 1 hour each day"
Output: {{
  "title": "Learn AI MOOC",
  "category": "learning",
  "recurring_days": ["monday", "tuesday", "thursday", "friday"],
  "recurring_frequency": "weekly",
  "recurring_duration": 60,
  "importance": 4,
  "urgency": 2
}}

Input: "create ideal customer profile for AI call receptionist, close of business Monday"
Output: {{
  "title": "Create ideal customer profile for AI call receptionist",
  "deadline": "2025-11-18",
  "category": "business",
  "project": "AI call receptionist",
  "urgency": 4,
  "importance": 4
}}

Input: "buy groceries tomorrow"
Output: {{
  "title": "Buy groceries",
  "deadline": "2025-11-16",
  "category": "personal",
  "urgency": 3,
  "importance": 2
}}

Return ONLY valid JSON."""
                    },
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
                temperature=0,
                max_tokens=300
            )

            result = response.choices[0].message.content.strip()
            print(f"✓ OpenAI extraction result: {result}")

            # Parse JSON
            extracted = json.loads(result)

            # Update fields with extracted values
            understood = []
            for field, value in extracted.items():
                if field in self.fields and value is not None:
                    self.fields[field] = value
                    understood.append(field)
                elif field == "recurring_days":
                    self.recurring_pattern = {
                        "days": value,
                        "frequency": extracted.get("recurring_frequency", "weekly"),
                        "duration": extracted.get("recurring_duration", 60)
                    }
                    understood.append("recurring_pattern")

            self.understood_fields = understood
            self.upfront_extraction_done = True

            # Determine what's still missing (required fields only)
            missing = []
            if not self.fields['title']:
                missing.append("title")
            if self.fields['urgency'] is None or self.fields['importance'] is None:
                missing.append("priority")
            # deadline is optional, don't add to missing

            # Generate suggestion
            suggestion = None
            if self.recurring_pattern:
                days_str = ", ".join(self.recurring_pattern["days"])
                suggestion = f"📅 I detected a recurring pattern ({days_str}). This might work better as a **Goal** with automatic calendar blocking. Would you like me to create a goal instead? (Reply 'yes' or 'no, just add the task')"

            return {
                "extracted": extracted,
                "missing": missing,
                "recurring_pattern": self.recurring_pattern,
                "suggestion": suggestion
            }

        except Exception as e:
            print(f"⚠️  OpenAI extraction error: {e}, using fallback")
            # Fallback: Just extract title
            self.fields['title'] = user_input.strip()
            self.understood_fields.append('title')
            self.upfront_extraction_done = True
            return {
                "extracted": {"title": user_input.strip()},
                "missing": ["deadline", "priority"],
                "recurring_pattern": None,
                "suggestion": None
            }

    def get_acknowledgment_message(self) -> str:
        """
        Generate acknowledgment of what was understood from initial message.

        Example: "✅ Got it! I understand you want to learn AI MOOC on Monday, Tuesday, Thursday, Friday for 1 hour each day. This is a learning task."
        """
        if not self.understood_fields:
            return None

        parts = []

        # Title
        if 'title' in self.understood_fields and self.fields['title']:
            parts.append(f"**{self.fields['title']}**")

        # Recurring pattern
        if self.recurring_pattern:
            days_str = ", ".join(self.recurring_pattern["days"])
            duration_str = f"{self.recurring_pattern['duration']} minutes" if self.recurring_pattern['duration'] != 60 else "1 hour"
            parts.append(f"on {days_str} for {duration_str} each session")

        # Deadline
        if 'deadline' in self.understood_fields and self.fields['deadline']:
            date_obj = datetime.fromisoformat(self.fields['deadline'])
            date_str = date_obj.strftime("%A, %B %d")
            parts.append(f"due {date_str}")

        # Category
        if 'category' in self.understood_fields and self.fields['category']:
            parts.append(f"({self.fields['category']} task)")

        # Project
        if 'project' in self.understood_fields and self.fields['project']:
            parts.append(f"for {self.fields['project']}")

        if not parts:
            return None

        message = "✅ Got it! I understand you want to " + " ".join(parts)
        return message

    def get_confirmation_question(self) -> str:
        """
        Generate confirmation question showing what was collected.

        Returns a summary of all collected fields and asks user to confirm.
        """
        summary_parts = []

        # Task title
        if self.fields['title']:
            summary_parts.append(f"**Task:** {self.fields['title']}")

        # Deadline
        if self.fields.get('deadline'):
            date_obj = datetime.fromisoformat(self.fields['deadline'])
            date_str = date_obj.strftime("%A, %B %d")
            summary_parts.append(f"**Due:** {date_str}")

        # Priority
        if self.fields['urgency'] and self.fields['importance']:
            quadrant = self._calculate_quadrant()
            summary_parts.append(f"**Priority:** {self._quadrant_description(quadrant)}")

        # Category
        if self.fields.get('category'):
            summary_parts.append(f"**Category:** {self.fields['category']}")

        # Project
        if self.fields.get('project'):
            summary_parts.append(f"**Project:** {self.fields['project']}")

        # Recurring pattern
        if self.recurring_pattern:
            days_str = ", ".join(self.recurring_pattern["days"])
            duration_str = f"{self.recurring_pattern['duration']} minutes" if self.recurring_pattern['duration'] != 60 else "1 hour"
            summary_parts.append(f"**Recurring:** {days_str} for {duration_str} each session")

        # Notes/Tags/Context
        metadata_parts = []
        if self.fields.get('notes'):
            metadata_parts.append(f"**Notes:** {self.fields['notes']}")
        if self.fields.get('tags'):
            metadata_parts.append(f"**Tags:** {self.fields['tags']}")
        if self.fields.get('context'):
            metadata_parts.append(f"**Context:** {self.fields['context']}")

        # Build final message
        summary = "\n".join(summary_parts)
        if metadata_parts:
            summary += "\n" + "\n".join(metadata_parts)

        confirmation_msg = f"""📋 Here's what I've got:

{summary}

**Is this correct?**
- Reply **'yes'** to create the task
- Reply **'change [field]'** to modify something (e.g., 'change deadline')
- Or tell me what to add/change"""

        return confirmation_msg

    def get_next_question(self) -> Optional[str]:
        """Return the next question to ask user, or None if all fields collected."""
        if not self.fields['title']:
            return "What task would you like to add?"

        if not self.fields['deadline']:
            return "When should it be complete? (e.g., 'tomorrow', 'Friday', 'Nov 20', or 'skip' to skip)"

        if self.fields['urgency'] is None or self.fields['importance'] is None:
            return "How would you describe the priority?\n- Type 'critical' if it's both urgent AND important\n- Type 'urgent' if it needs to be done soon\n- Type 'important' if it's key to your goals but not time-sensitive\n- Type 'low' if it's neither urgent nor important"

        # Ask about category (personal/business)
        if not self.category_asked:
            return "Is this a personal or business task?\n- Type 'personal' for personal tasks\n- Type 'business' (or 'work') for work-related tasks\n- Type 'learning' for educational tasks\n- Type 'health' for health/fitness tasks"

        # Ask about project (if business)
        if not self.project_asked:
            if self.fields.get('category') in ['business', 'work']:
                return "What project or area is this related to? (e.g., 'AskSharon', 'Marketing', 'Sales')\nOr type 'skip' if not applicable."
            else:
                # Skip project question for non-business tasks
                self.project_asked = True
                # Continue to next question

        # After category/project, offer additional fields
        if not self.additional_offered:
            return "Would you like to add any additional details?\n- **Notes**: Any additional context\n- **Tags**: Keywords for filtering (comma-separated)\n- **Context**: Where/when can this be done?\n\nType the details or 'done' to finish."

        # After all fields collected, ask for confirmation
        if not self.confirmation_asked:
            return self.get_confirmation_question()

        return None  # All fields collected and confirmed

    def is_complete(self) -> bool:
        """Check if all required fields are collected AND user has confirmed."""
        fields_complete = all([
            self.fields['title'],
            self.fields['urgency'] is not None,
            self.fields['importance'] is not None
        ])

        return fields_complete and self.user_confirmed

    def process_response(self, user_response: str) -> Dict[str, Any]:
        """
        Process user response and extract field value.

        Returns:
            {"field": str, "value": any, "extracted": bool, "error": Optional[str], "acknowledgment": Optional[str], "suggestion": Optional[str]}
        """
        if not self.fields['title'] and not self.upfront_extraction_done:
            # Phase 1: Upfront extraction of ALL fields from initial message
            extraction_result = self.extract_all_fields(user_response)

            # Generate acknowledgment message
            acknowledgment = self.get_acknowledgment_message()

            # If there's a suggestion (e.g., create goal instead), mark it as pending
            if extraction_result["suggestion"]:
                self.suggestion_pending = extraction_result["suggestion"]

            return {
                "field": "initial_extraction",
                "value": extraction_result["extracted"],
                "extracted": True,
                "acknowledgment": acknowledgment,
                "suggestion": extraction_result["suggestion"],
                "missing": extraction_result["missing"]
            }

        # Handle response to suggestion (if one is pending)
        elif self.suggestion_pending and not self.user_wants_goal:
            user_input_lower = user_response.strip().lower()

            # Check if user wants to create a goal instead
            if any(word in user_input_lower for word in ['yes', 'y', 'goal', 'recurring', 'sure', 'ok', 'okay']):
                self.user_wants_goal = True
                self.suggestion_pending = None
                return {
                    "field": "goal_confirmation",
                    "value": "user_wants_goal",
                    "extracted": True,
                    "create_goal": True  # Signal to main.py to create a goal
                }

            # User wants to continue with task instead
            elif any(word in user_input_lower for word in ['no', 'task', 'just', 'add']):
                self.suggestion_pending = None
                # Continue to next question (deadline, priority, etc.)
                return {
                    "field": "goal_declined",
                    "value": "continue_with_task",
                    "extracted": True
                }

            # Unclear response - assume they want to continue with task
            else:
                self.suggestion_pending = None
                return {
                    "field": "goal_declined",
                    "value": "continue_with_task",
                    "extracted": True
                }

        elif not self.fields['deadline']:
            # Allow skipping deadline
            if user_response.strip().lower() == 'skip':
                self.fields['deadline'] = None
                return {"field": "deadline", "value": "skipped", "extracted": True}

            # Extract deadline with AI
            deadline = self._extract_deadline(user_response)
            if deadline:
                self.fields['deadline'] = deadline
                return {"field": "deadline", "value": deadline, "extracted": True}
            else:
                return {"field": "deadline", "value": None, "extracted": False, "error": "Could not parse date. Try 'tomorrow', 'Friday', 'Nov 20', or 'skip'"}

        elif self.fields['urgency'] is None or self.fields['importance'] is None:
            # Extract urgency + importance from priority description
            priority = self._extract_priority(user_response)
            if priority:
                self.fields['urgency'] = priority['urgency']
                self.fields['importance'] = priority['importance']
                return {"field": "priority", "value": priority, "extracted": True}
            else:
                return {"field": "priority", "value": None, "extracted": False, "error": "Could not determine priority. Try 'critical', 'urgent', 'important', or 'low'"}

        elif not self.category_asked:
            # Extract category
            self.category_asked = True
            category = self._extract_category(user_response)
            if category:
                self.fields['category'] = category
                return {"field": "category", "value": category, "extracted": True}
            else:
                # Default to 'personal' if unclear
                self.fields['category'] = 'personal'
                return {"field": "category", "value": "personal (default)", "extracted": True}

        elif not self.project_asked:
            # Extract project (only for business tasks)
            self.project_asked = True

            if self.fields.get('category') in ['business', 'work']:
                if user_response.strip().lower() in ['skip', 'none', 'n/a']:
                    self.fields['project'] = None
                    return {"field": "project", "value": "skipped", "extracted": True}
                else:
                    self.fields['project'] = user_response.strip()
                    return {"field": "project", "value": self.fields['project'], "extracted": True}
            else:
                # Not a business task, skip project
                return {"field": "project", "value": "skipped (not business)", "extracted": True}

        elif not self.additional_offered:
            # Collect additional metadata (notes, tags, context)
            self.additional_offered = True

            # Check if user wants to skip
            if user_response.strip().lower() in ['done', 'skip', 'no', 'finish']:
                return {"field": "additional", "value": "skipped", "extracted": True}

            # Extract additional fields with OpenAI
            additional = self._extract_additional_fields(user_response)
            if additional:
                self.fields.update(additional)
                return {"field": "additional", "value": additional, "extracted": True}
            else:
                # Even if extraction fails, mark as done
                return {"field": "additional", "value": "skipped", "extracted": True}

        elif not self.confirmation_asked:
            # Handle confirmation response
            self.confirmation_asked = True

            user_input_lower = user_response.strip().lower()

            # Check for confirmation
            if user_input_lower in ['yes', 'y', 'correct', 'looks good', 'perfect', 'confirm', 'ok', 'okay']:
                self.user_confirmed = True
                return {"field": "confirmation", "value": "confirmed", "extracted": True}

            # Check for changes requested
            elif any(word in user_input_lower for word in ['change', 'update', 'modify', 'fix']):
                # User wants to change something - extract what field they want to change
                # For now, just tell them to specify what field
                return {
                    "field": "confirmation",
                    "value": "change_requested",
                    "extracted": False,
                    "error": "Which field would you like to change? (deadline, priority, category, project, notes, tags, or context)"
                }

            # User wants to add more info
            else:
                # Try to extract additional fields from their response
                additional = self._extract_additional_fields(user_response)
                if additional:
                    self.fields.update(additional)
                    # After updating, ask confirmation again
                    self.confirmation_asked = False
                    return {"field": "additional_update", "value": additional, "extracted": True}
                else:
                    # Assume they're confirming
                    self.user_confirmed = True
                    return {"field": "confirmation", "value": "assumed_confirmed", "extracted": True}

        return {"extracted": False, "error": "Unknown field"}

    def _extract_deadline(self, user_input: str) -> Optional[str]:
        """
        Extract deadline from natural language using OpenAI.

        Examples:
        - "tomorrow" → "2025-11-16"
        - "Friday" → "2025-11-17"
        - "in 3 days" → "2025-11-18"

        Returns:
            ISO date string (YYYY-MM-DD) or None
        """
        if not self.client:
            # Fallback: Simple keyword matching
            print(f"🔍 No OpenAI client, using fallback for: {user_input}")
            return self._extract_deadline_fallback(user_input)

        try:
            today = datetime.now().strftime("%Y-%m-%d")
            day_of_week = datetime.now().strftime("%A")

            print(f"🔍 Extracting deadline from: '{user_input}' (Today: {today}, {day_of_week})")

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"Today is {today} ({day_of_week}). Extract the deadline date from user input. Return ONLY the ISO date (YYYY-MM-DD) or 'null' if unclear. Examples: 'Monday' → next Monday's date, 'tomorrow' → {(datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')}, 'end of week' → next Friday."
                    },
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
                temperature=0,
                max_tokens=20
            )

            result = response.choices[0].message.content.strip().strip('"')
            print(f"✓ OpenAI returned: '{result}'")

            # Validate ISO date format
            if result and result != 'null':
                try:
                    datetime.fromisoformat(result)
                    print(f"✓ Valid ISO date: {result}")
                    return result
                except ValueError:
                    print(f"⚠️  Invalid date format from OpenAI: {result}, trying fallback")
                    pass

            # OpenAI returned null or invalid, try fallback
            print(f"⚠️  OpenAI couldn't parse, trying fallback")
            return self._extract_deadline_fallback(user_input)

        except Exception as e:
            print(f"⚠️  OpenAI extraction error: {e}, using fallback")
            return self._extract_deadline_fallback(user_input)

    def _extract_deadline_fallback(self, user_input: str) -> Optional[str]:
        """Fallback deadline extraction without OpenAI."""
        today = datetime.now()
        input_lower = user_input.lower().strip()

        print(f"🔍 Fallback parsing: '{input_lower}'")

        # Common typos and patterns
        # Handle "tomorrow" typos (tomrrow, tomorow, tommorrow, etc.)
        import re
        if re.search(r't[o0]m[o0a]?r+[o0]w', input_lower):
            print(f"✓ Matched 'tomorrow' (with typo)")
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")

        # Exact matches
        if input_lower in ["today", "now", "tonight", "end of day", "eod"]:
            print(f"✓ Matched 'today'")
            return today.strftime("%Y-%m-%d")
        elif input_lower in ["tomorrow", "tmrw", "tmr"]:
            print(f"✓ Matched 'tomorrow'")
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "next week" in input_lower or "1 week" in input_lower:
            print(f"✓ Matched 'next week'")
            return (today + timedelta(days=7)).strftime("%Y-%m-%d")
        elif "end of week" in input_lower or "this friday" in input_lower:
            # Find next Friday
            current_weekday = today.weekday()
            days_ahead = (4 - current_weekday) % 7  # Friday = 4
            if days_ahead == 0:
                days_ahead = 7
            print(f"✓ Matched 'end of week' (Friday)")
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

        # Day of week patterns (including "close of business", "end of day", etc.)
        days_of_week = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6,
            # Common abbreviations
            "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6
        }

        for day_name, target_weekday in days_of_week.items():
            if day_name in input_lower:
                current_weekday = today.weekday()
                days_ahead = (target_weekday - current_weekday) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next occurrence
                result = (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
                print(f"✓ Matched day '{day_name}' → {result}")
                return result

        # Relative days: "in 2 days", "in 3 days"
        if match := re.search(r'in\s+(\d+)\s+days?', input_lower):
            num_days = int(match.group(1))
            result = (today + timedelta(days=num_days)).strftime("%Y-%m-%d")
            print(f"✓ Matched 'in {num_days} days' → {result}")
            return result

        print(f"⚠️  No fallback pattern matched")
        return None

    def _extract_priority(self, user_input: str) -> Optional[Dict[str, int]]:
        """
        Extract urgency + importance from priority description.

        Mapping:
        - "critical" / "both" → urgency=5, importance=5
        - "urgent" → urgency=5, importance=3
        - "important" → urgency=3, importance=5
        - "low" / "neither" → urgency=2, importance=2

        Returns:
            {"urgency": int, "importance": int} or None
        """
        input_lower = user_input.lower().strip()

        # Critical (Quadrant I)
        if any(word in input_lower for word in ["critical", "both", "urgent and important", "asap"]):
            return {"urgency": 5, "importance": 5}

        # Urgent (Quadrant I or III)
        elif any(word in input_lower for word in ["urgent", "asap", "soon", "immediately"]):
            return {"urgency": 5, "importance": 3}

        # Important (Quadrant II)
        elif any(word in input_lower for word in ["important", "key", "strategic", "goal"]):
            return {"urgency": 3, "importance": 5}

        # Low (Quadrant IV)
        elif any(word in input_lower for word in ["low", "minor", "neither", "not urgent", "not important"]):
            return {"urgency": 2, "importance": 2}

        # Default: Medium
        elif any(word in input_lower for word in ["medium", "moderate", "normal"]):
            return {"urgency": 3, "importance": 3}

        return None

    def _extract_category(self, user_input: str) -> Optional[str]:
        """
        Extract category from user response.

        Categories: personal, business/work, learning, health

        Returns:
            Category string or None
        """
        input_lower = user_input.lower().strip()

        # Direct matches
        if any(word in input_lower for word in ["business", "work", "professional", "job"]):
            return "business"
        elif any(word in input_lower for word in ["personal", "private", "home"]):
            return "personal"
        elif any(word in input_lower for word in ["learning", "education", "study", "course", "training"]):
            return "learning"
        elif any(word in input_lower for word in ["health", "fitness", "exercise", "workout", "medical"]):
            return "health"

        return None

    def _extract_additional_fields(self, user_input: str) -> Optional[Dict[str, str]]:
        """
        Extract additional fields from natural language using OpenAI.

        Fields: notes, tags, context (NOT project/category - those are asked separately)

        Examples:
        - "notes: need to review with team, tags: urgent, marketing"
        - "context: when I have 2 hours free, tags: deep-work"

        Returns:
            {"notes": str, "tags": str, "context": str} or None
        """
        if not self.client:
            # Fallback: Simple keyword extraction
            return self._extract_additional_fallback(user_input)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Extract task additional fields from user input. Return a JSON object with these optional fields:
- notes: Any additional context or details
- tags: Keywords for filtering (comma-separated)
- context: Where/when can this be done?

Return ONLY valid JSON. If a field is not mentioned, omit it. Example:
{"notes": "Review with team", "tags": "urgent, marketing", "context": "Office, 2pm meeting"}"""
                    },
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
                temperature=0,
                max_tokens=150
            )

            result = response.choices[0].message.content.strip()

            # Parse JSON
            import json
            additional = json.loads(result)

            # Validate fields (only notes, tags, context)
            valid_fields = {'notes', 'tags', 'context'}
            filtered = {k: v for k, v in additional.items() if k in valid_fields and v}

            return filtered if filtered else None

        except Exception as e:
            print(f"⚠️  OpenAI additional fields extraction error: {e}")
            return self._extract_additional_fallback(user_input)

    def _extract_additional_fallback(self, user_input: str) -> Optional[Dict[str, str]]:
        """Fallback additional fields extraction without OpenAI using simple keyword matching."""
        import re

        additional = {}
        input_lower = user_input.lower()

        # Pattern: "notes: X" or "note: X"
        if match := re.search(r'notes?[:\s]+([^,\n]+)', input_lower):
            additional['notes'] = match.group(1).strip()

        # Pattern: "tags: X, Y, Z"
        if match := re.search(r'tags?[:\s]+([^,\n]+)', input_lower):
            additional['tags'] = match.group(1).strip()

        # Pattern: "context: X" or "when: X"
        if match := re.search(r'(?:context|when)[:\s]+([^,\n]+)', input_lower):
            additional['context'] = match.group(1).strip()

        return additional if additional else None

    def to_dict(self) -> Dict[str, Any]:
        """Return task data for API submission."""
        return {
            "title": self.fields['title'],
            "urgency": self.fields['urgency'],
            "importance": self.fields['importance'],
            "effort": self.fields['effort'],
            "deadline": self.fields['deadline'],
            "project": self.fields['project'],
            "category": self.fields['category'],
            "notes": self.fields['notes'],
            "tags": self.fields['tags'],
            "context": self.fields['context']
        }

    def get_summary(self) -> str:
        """Return human-readable summary of collected fields."""
        quadrant = self._calculate_quadrant()
        deadline_str = self.fields.get('deadline') or 'No deadline'

        summary = f"""✓ Task created: {self.fields['title']}
Due: {deadline_str}
Priority: Quadrant {quadrant} ({self._quadrant_description(quadrant)})
Urgency: {self.fields['urgency']}/5, Importance: {self.fields['importance']}/5"""

        # Add metadata if present
        metadata_parts = []
        if self.fields.get('project'):
            metadata_parts.append(f"Project: {self.fields['project']}")
        if self.fields.get('category'):
            metadata_parts.append(f"Category: {self.fields['category']}")
        if self.fields.get('tags'):
            metadata_parts.append(f"Tags: {self.fields['tags']}")
        if self.fields.get('context'):
            metadata_parts.append(f"Context: {self.fields['context']}")
        if self.fields.get('notes'):
            metadata_parts.append(f"Notes: {self.fields['notes']}")

        if metadata_parts:
            summary += "\n\n" + "\n".join(metadata_parts)

        return summary

    def _calculate_quadrant(self) -> str:
        """Calculate Eisenhower quadrant based on urgency + importance."""
        u = self.fields.get('urgency', 3)
        i = self.fields.get('importance', 3)

        if u >= 4 and i >= 4:
            return "I"  # Urgent & Important
        elif u < 4 and i >= 4:
            return "II"  # Not Urgent, Important
        elif u >= 4 and i < 4:
            return "III"  # Urgent, Not Important
        else:
            return "IV"  # Not Urgent, Not Important

    def _quadrant_description(self, quadrant: str) -> str:
        """Return description of Eisenhower quadrant."""
        descriptions = {
            "I": "Urgent & Important - Do First",
            "II": "Not Urgent, Important - Schedule",
            "III": "Urgent, Not Important - Delegate",
            "IV": "Not Urgent, Not Important - Eliminate"
        }
        return descriptions.get(quadrant, "Unknown")


class AppointmentWorkflow:
    """
    Multi-turn conversation workflow for appointment/meeting creation.

    Required fields:
    - title: str
    - date: str (ISO date)
    - time: str (HH:MM format)

    Optional fields:
    - duration: int (minutes, default 60)
    - location: str
    - description: str
    - attendees: str
    """

    def __init__(self):
        self.fields = {
            'title': None,
            'date': None,
            'time': None,
            'duration': 60,  # Default 1 hour
            'location': None,
            'description': None,
            'attendees': None
        }
        self.duration_confirmed = False
        self.optional_offered = False  # Track if we've asked about optional fields
        self.confirmation_asked = False  # Track if we've asked for confirmation
        self.user_confirmed = False  # Track if user confirmed the appointment
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def get_next_question(self) -> Optional[str]:
        """Return the next question to ask user."""
        if not self.fields['title']:
            return "What's the meeting or appointment about?"

        if not self.fields['date']:
            return "When should it be? (e.g., 'tomorrow', 'Friday', 'Nov 20')"

        if not self.fields['time']:
            return "What time? (e.g., '2pm', '14:00', '10:30am')"

        if not self.duration_confirmed:
            return "How long should it be? (e.g., '30 minutes', '1 hour', '2 hours')\nOr press Enter to use default: 1 hour"

        # After required fields, offer optional details
        if not self.optional_offered:
            return "Would you like to add any additional details?\n- **Location**: Where is this meeting?\n- **Description**: Additional notes\n- **Attendees**: Who else will attend?\n\nType the details or 'done' to finish."

        # After all fields collected, ask for confirmation
        if not self.confirmation_asked:
            return self.get_confirmation_question()

        return None  # All fields collected and confirmed

    def get_confirmation_question(self) -> str:
        """Generate confirmation question showing what was collected."""
        summary_parts = []

        # Appointment title
        if self.fields['title']:
            summary_parts.append(f"**Meeting:** {self.fields['title']}")

        # Date and time
        if self.fields.get('date') and self.fields.get('time'):
            date_obj = datetime.fromisoformat(self.fields['date'])
            date_str = date_obj.strftime("%A, %B %d")
            time_obj = datetime.strptime(self.fields['time'], "%H:%M")
            time_str = time_obj.strftime("%I:%M %p").lstrip('0')
            summary_parts.append(f"**When:** {date_str} at {time_str}")

        # Duration
        if self.fields['duration']:
            duration_str = f"{self.fields['duration']} minutes" if self.fields['duration'] != 60 else "1 hour"
            summary_parts.append(f"**Duration:** {duration_str}")

        # Location
        if self.fields.get('location'):
            summary_parts.append(f"**Location:** {self.fields['location']}")

        # Description
        if self.fields.get('description'):
            summary_parts.append(f"**Description:** {self.fields['description']}")

        # Attendees
        if self.fields.get('attendees'):
            summary_parts.append(f"**Attendees:** {self.fields['attendees']}")

        # Build final message
        summary = "\n".join(summary_parts)

        confirmation_msg = f"""📅 Here's what I've got:

{summary}

**Is this correct?**
- Reply **'yes'** to add to calendar
- Reply **'change [field]'** to modify something
- Or tell me what to add/change"""

        return confirmation_msg

    def is_complete(self) -> bool:
        """Check if all required fields are collected AND user has confirmed."""
        fields_complete = all([
            self.fields['title'],
            self.fields['date'],
            self.fields['time'],
            self.fields['duration'] is not None
        ])

        return fields_complete and self.user_confirmed

    def process_response(self, user_response: str) -> Dict[str, Any]:
        """Process user response and extract field value."""
        if not self.fields['title']:
            self.fields['title'] = user_response.strip()
            return {"field": "title", "value": self.fields['title'], "extracted": True}

        elif not self.fields['date']:
            date = self._extract_date(user_response)
            if date:
                self.fields['date'] = date
                return {"field": "date", "value": date, "extracted": True}
            else:
                return {"field": "date", "value": None, "extracted": False, "error": "Could not parse date"}

        elif not self.fields['time']:
            time = self._extract_time(user_response)
            if time:
                self.fields['time'] = time
                return {"field": "time", "value": time, "extracted": True}
            else:
                return {"field": "time", "value": None, "extracted": False, "error": "Could not parse time. Try '2pm' or '14:00'"}

        elif not self.duration_confirmed:
            if user_response.strip() == "":
                # User pressed Enter → keep default
                self.duration_confirmed = True
                return {"field": "duration", "value": 60, "extracted": True}
            else:
                duration = self._extract_duration(user_response)
                if duration:
                    self.fields['duration'] = duration
                    self.duration_confirmed = True
                    return {"field": "duration", "value": duration, "extracted": True}
                else:
                    return {"field": "duration", "value": None, "extracted": False, "error": "Could not parse duration"}

        elif not self.optional_offered:
            # Collect optional fields (location, description, attendees)
            self.optional_offered = True

            # Check if user wants to skip
            if user_response.strip().lower() in ['done', 'skip', 'no', 'finish']:
                return {"field": "optional", "value": "skipped", "extracted": True}

            # Extract optional fields with OpenAI
            optional = self._extract_optional_fields(user_response)
            if optional:
                self.fields.update(optional)
                return {"field": "optional", "value": optional, "extracted": True}
            else:
                # Even if extraction fails, mark as done
                return {"field": "optional", "value": "skipped", "extracted": True}

        elif not self.confirmation_asked:
            # Handle confirmation response
            self.confirmation_asked = True

            user_input_lower = user_response.strip().lower()

            # Check for confirmation
            if user_input_lower in ['yes', 'y', 'correct', 'looks good', 'perfect', 'confirm', 'ok', 'okay']:
                self.user_confirmed = True
                return {"field": "confirmation", "value": "confirmed", "extracted": True}

            # Check for changes requested
            elif any(word in user_input_lower for word in ['change', 'update', 'modify', 'fix']):
                return {
                    "field": "confirmation",
                    "value": "change_requested",
                    "extracted": False,
                    "error": "Which field would you like to change? (date, time, duration, location, description, or attendees)"
                }

            # User wants to add more info
            else:
                # Try to extract additional fields from their response
                additional = self._extract_optional_fields(user_response)
                if additional:
                    self.fields.update(additional)
                    # After updating, ask confirmation again
                    self.confirmation_asked = False
                    return {"field": "additional_update", "value": additional, "extracted": True}
                else:
                    # Assume they're confirming
                    self.user_confirmed = True
                    return {"field": "confirmation", "value": "assumed_confirmed", "extracted": True}

        return {"extracted": False, "error": "Unknown field"}

    def _extract_date(self, user_input: str) -> Optional[str]:
        """Extract date using same logic as TaskWorkflow."""
        workflow = TaskWorkflow()
        return workflow._extract_deadline(user_input)

    def _extract_time(self, user_input: str) -> Optional[str]:
        """
        Extract time from natural language.

        Examples:
        - "2pm" → "14:00"
        - "10:30am" → "10:30"
        - "14:00" → "14:00"

        Returns:
            HH:MM format string or None
        """
        import re

        input_lower = user_input.lower().strip()

        # Pattern 1: "2pm", "10am"
        match = re.search(r'(\d{1,2})(am|pm)', input_lower)
        if match:
            hour = int(match.group(1))
            period = match.group(2)

            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0

            return f"{hour:02d}:00"

        # Pattern 2: "10:30am", "2:45pm"
        match = re.search(r'(\d{1,2}):(\d{2})(am|pm)', input_lower)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            period = match.group(3)

            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0

            return f"{hour:02d}:{minute:02d}"

        # Pattern 3: "14:00", "09:30"
        match = re.search(r'(\d{1,2}):(\d{2})', input_lower)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))

            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"

        return None

    def _extract_duration(self, user_input: str) -> Optional[int]:
        """
        Extract duration in minutes.

        Examples:
        - "30 minutes" → 30
        - "1 hour" → 60
        - "2 hours" → 120
        - "90 min" → 90

        Returns:
            Duration in minutes or None
        """
        import re

        input_lower = user_input.lower().strip()

        # Pattern: "X hours"
        match = re.search(r'(\d+\.?\d*)\s*(hour|hr|hrs|hours)', input_lower)
        if match:
            hours = float(match.group(1))
            return int(hours * 60)

        # Pattern: "X minutes"
        match = re.search(r'(\d+)\s*(minute|min|mins|minutes)', input_lower)
        if match:
            return int(match.group(1))

        # Just a number (assume minutes)
        match = re.search(r'^(\d+)$', input_lower)
        if match:
            return int(match.group(1))

        return None

    def _extract_optional_fields(self, user_input: str) -> Optional[Dict[str, str]]:
        """
        Extract optional fields (location, description, attendees) from natural language.

        Examples:
        - "location: Conference Room B, description: Quarterly review"
        - "at the office, discussing project roadmap with John and Sarah"

        Returns:
            {"location": str, "description": str, "attendees": str} or None
        """
        if not self.client:
            # Fallback: Simple keyword extraction
            return self._extract_optional_fallback(user_input)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """Extract appointment optional fields from user input. Return a JSON object with these optional fields:
- location: Where is the meeting/appointment?
- description: Additional notes or purpose
- attendees: Who else will attend? (names, comma-separated)

Return ONLY valid JSON. If a field is not mentioned, omit it. Example:
{"location": "Conference Room B", "description": "Quarterly review", "attendees": "John, Sarah"}"""
                    },
                    {
                        "role": "user",
                        "content": user_input
                    }
                ],
                temperature=0,
                max_tokens=150
            )

            result = response.choices[0].message.content.strip()

            # Parse JSON
            import json
            optional = json.loads(result)

            # Validate fields
            valid_fields = {'location', 'description', 'attendees'}
            filtered = {k: v for k, v in optional.items() if k in valid_fields and v}

            return filtered if filtered else None

        except Exception as e:
            print(f"⚠️  OpenAI optional fields extraction error: {e}")
            return self._extract_optional_fallback(user_input)

    def _extract_optional_fallback(self, user_input: str) -> Optional[Dict[str, str]]:
        """Fallback optional fields extraction without OpenAI using simple keyword matching."""
        import re

        optional = {}
        input_lower = user_input.lower()

        # Pattern: "location: X" or "at X"
        if match := re.search(r'location[:\s]+([^,\n]+)', input_lower):
            optional['location'] = match.group(1).strip()
        elif match := re.search(r'\bat\s+([^,\n]+)', input_lower):
            optional['location'] = match.group(1).strip()

        # Pattern: "description: X" or "about X"
        if match := re.search(r'description[:\s]+([^,\n]+)', input_lower):
            optional['description'] = match.group(1).strip()
        elif match := re.search(r'(?:about|discussing|regarding)[:\s]+([^,\n]+)', input_lower):
            optional['description'] = match.group(1).strip()

        # Pattern: "attendees: X" or "with X"
        if match := re.search(r'attendees?[:\s]+([^,\n]+)', input_lower):
            optional['attendees'] = match.group(1).strip()
        elif match := re.search(r'with\s+([^,\n]+)', input_lower):
            optional['attendees'] = match.group(1).strip()

        return optional if optional else None

    def to_calendar_event(self) -> Dict[str, Any]:
        """Return event data for Google Calendar API submission."""
        # Combine date + time into ISO datetime
        start_datetime = f"{self.fields['date']}T{self.fields['time']}:00"

        # Calculate end time
        start = datetime.fromisoformat(start_datetime)
        end = start + timedelta(minutes=self.fields['duration'])
        end_datetime = end.isoformat()

        event = {
            "summary": self.fields['title'],
            "start_time": start_datetime,
            "end_time": end_datetime
        }

        # Add optional fields if present
        if self.fields.get('location'):
            event['location'] = self.fields['location']
        if self.fields.get('description'):
            event['description'] = self.fields['description']
        if self.fields.get('attendees'):
            event['attendees'] = self.fields['attendees']

        return event

    def get_summary(self) -> str:
        """Return human-readable summary of appointment."""
        date_obj = datetime.fromisoformat(self.fields['date'])
        date_str = date_obj.strftime("%A, %B %d")  # "Friday, November 17"

        # Convert 24h time to 12h AM/PM
        time_obj = datetime.strptime(self.fields['time'], "%H:%M")
        time_str = time_obj.strftime("%I:%M %p").lstrip('0')  # "2:00 PM"

        duration_str = f"{self.fields['duration']} minutes" if self.fields['duration'] != 60 else "1 hour"

        summary = f"""✅ Added to Google Calendar:
📅 {self.fields['title']}
📆 {date_str} at {time_str}
⏱ {duration_str}"""

        # Add optional fields if present
        if self.fields.get('location'):
            summary += f"\n📍 {self.fields['location']}"
        if self.fields.get('description'):
            summary += f"\n📝 {self.fields['description']}"
        if self.fields.get('attendees'):
            summary += f"\n👥 {self.fields['attendees']}"

        return summary


class GoalWorkflow:
    """
    Multi-turn conversation workflow for goal creation from recurring patterns.

    Required fields:
    - name: str (goal name)
    - target_per_week: int (how many times per week)

    Optional fields:
    - days: list[str] (which days - from recurring pattern)
    - duration: int (minutes per session)
    - notes: str
    """

    def __init__(self):
        self.fields = {
            'name': None,
            'target_per_week': None,
            'days': None,  # List of days from recurring pattern
            'duration': 60,  # Default 1 hour
            'notes': None
        }
        self.recurring_pattern = None  # Store detected recurring pattern
        self.confirmation_asked = False  # Track if we've asked for confirmation
        self.user_confirmed = False  # Track if user confirmed the goal
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def set_from_task_workflow(self, task_workflow):
        """
        Initialize goal from a TaskWorkflow that detected a recurring pattern.

        Args:
            task_workflow: TaskWorkflow instance with recurring_pattern set
        """
        if task_workflow.recurring_pattern:
            self.recurring_pattern = task_workflow.recurring_pattern
            self.fields['name'] = task_workflow.fields['title']
            self.fields['days'] = task_workflow.recurring_pattern['days']
            self.fields['duration'] = task_workflow.recurring_pattern.get('duration', 60)
            self.fields['target_per_week'] = len(task_workflow.recurring_pattern['days'])

            # Copy notes if present
            if task_workflow.fields.get('notes'):
                self.fields['notes'] = task_workflow.fields['notes']

    def get_confirmation_question(self) -> str:
        """Generate confirmation question showing what was collected."""
        summary_parts = []

        # Goal name
        if self.fields['name']:
            summary_parts.append(f"**Goal:** {self.fields['name']}")

        # Target per week
        if self.fields['target_per_week']:
            summary_parts.append(f"**Target:** {self.fields['target_per_week']}x per week")

        # Recurring days
        if self.fields.get('days'):
            days_str = ", ".join(self.fields['days'])
            summary_parts.append(f"**Days:** {days_str}")

        # Duration
        if self.fields['duration']:
            duration_str = f"{self.fields['duration']} minutes" if self.fields['duration'] != 60 else "1 hour"
            summary_parts.append(f"**Duration:** {duration_str} per session")

        # Notes
        if self.fields.get('notes'):
            summary_parts.append(f"**Notes:** {self.fields['notes']}")

        # Build final message
        summary = "\n".join(summary_parts)

        confirmation_msg = f"""🎯 Here's your goal:

{summary}

**Is this correct?**
- Reply **'yes'** to create the goal
- Reply **'change [field]'** to modify something
- Or tell me what to add/change"""

        return confirmation_msg

    def is_complete(self) -> bool:
        """Check if all required fields are collected AND user has confirmed."""
        fields_complete = all([
            self.fields['name'],
            self.fields['target_per_week'] is not None
        ])

        return fields_complete and self.user_confirmed

    def process_response(self, user_response: str) -> Dict[str, Any]:
        """Process user response (mainly for confirmation)."""
        if not self.confirmation_asked:
            # Handle confirmation response
            self.confirmation_asked = True

            user_input_lower = user_response.strip().lower()

            # Check for confirmation
            if user_input_lower in ['yes', 'y', 'correct', 'looks good', 'perfect', 'confirm', 'ok', 'okay']:
                self.user_confirmed = True
                return {"field": "confirmation", "value": "confirmed", "extracted": True}

            # Check for changes requested
            elif any(word in user_input_lower for word in ['change', 'update', 'modify', 'fix']):
                return {
                    "field": "confirmation",
                    "value": "change_requested",
                    "extracted": False,
                    "error": "Which field would you like to change? (name, target, days, duration, or notes)"
                }

            # User wants to add notes
            else:
                # Try to extract notes
                if user_response.strip():
                    self.fields['notes'] = user_response.strip()
                    # After updating, ask confirmation again
                    self.confirmation_asked = False
                    return {"field": "notes_added", "value": user_response.strip(), "extracted": True}
                else:
                    # Assume they're confirming
                    self.user_confirmed = True
                    return {"field": "confirmation", "value": "assumed_confirmed", "extracted": True}

        return {"extracted": False, "error": "Unknown field"}

    def to_goal_data(self) -> Dict[str, Any]:
        """Return goal data for API submission."""
        return {
            "name": self.fields['name'],
            "target_per_week": self.fields['target_per_week']
        }

    def get_summary(self) -> str:
        """Return human-readable summary of created goal."""
        days_str = ", ".join(self.fields['days']) if self.fields.get('days') else "weekly"
        duration_str = f"{self.fields['duration']} minutes" if self.fields['duration'] != 60 else "1 hour"

        summary = f"""✅ **Goal Created: {self.fields['name']}**

🎯 **Target:** {self.fields['target_per_week']}x per week ({days_str})
⏱ **Duration:** {duration_str} per session
📊 **Progress:** 0/{self.fields['target_per_week']} (0%)"""

        if self.fields.get('notes'):
            summary += f"\n📝 **Notes:** {self.fields['notes']}"

        summary += f"""

This goal will track your weekly progress. Log a session by saying "did {self.fields['name'].lower()}" after each session!

**Note:** Calendar integration for automatic time blocking is coming in Phase 2."""

        return summary
