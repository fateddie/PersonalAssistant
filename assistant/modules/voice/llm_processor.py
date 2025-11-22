"""
LLM Processor for Conversational AI
====================================
Uses OpenAI's function calling to extract structured data from natural language.
"""

import json
from typing import Dict, List, Optional

from llm_config import client, is_configured, OPENAI_MODEL
from llm_functions import SYSTEM_PROMPT, FUNCTIONS
from llm_handlers import process_function_call


# Re-export is_configured for backward compatibility
__all__ = ['process_with_llm', 'is_configured']


def process_with_llm(
    message: str,
    conversation_history: List[Dict],
    pending_context: Optional[Dict] = None
) -> Dict:
    """
    Process user message using OpenAI LLM with function calling.

    Args:
        message: Current user message
        conversation_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
        pending_context: Any pending action context (e.g., partial goal data)

    Returns:
        Dict with keys: action, response_text, pending_data, needs_confirmation, view
    """
    if not is_configured():
        return {
            'action': 'llm_not_configured',
            'response_text': "LLM not configured. Please set OPENAI_API_KEY in .env",
            'needs_confirmation': False,
            'pending_data': None,
            'view': None
        }

    # Build messages for API call
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history (last 10 messages for context)
    for msg in conversation_history[-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add pending context if any
    if pending_context:
        context_msg = f"[Context: User is in the middle of creating something. Data collected so far: {json.dumps(pending_context)}]"
        messages.append({"role": "system", "content": context_msg})

    # Add current message
    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=[{"type": "function", "function": f} for f in FUNCTIONS],
            tool_choice="auto",
            temperature=0.7,
            max_tokens=500
        )

        assistant_message = response.choices[0].message

        # Check if there's a function call
        if assistant_message.tool_calls:
            tool_call = assistant_message.tool_calls[0]
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            return process_function_call(function_name, function_args, assistant_message.content)

        # No function call - just a conversational response
        return {
            'action': 'conversation',
            'response_text': assistant_message.content or "I'm not sure how to help with that. Try asking me to create a goal, show your schedule, or check emails.",
            'needs_confirmation': False,
            'pending_data': None,
            'view': None
        }

    except Exception as e:
        print(f"OpenAI API error: {e}")
        return {
            'action': 'error',
            'response_text': "Sorry, I encountered an error. Please try again.",
            'needs_confirmation': False,
            'pending_data': None,
            'view': None
        }
