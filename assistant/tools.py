from notes.models import Note
from tasks.models import Task
from goals.models import Goal
import json


def create_note(user, title, content=''):
    note = Note.objects.create(user=user, title=title, content=content)
    return f"✅ Note created: '{note.title}'"


def create_task(user, title, description='', priority='medium', due_date=None, status='pending'):
    task = Task.objects.create(
        user=user,
        title=title,
        description=description,
        priority=priority,
        due_date=due_date if due_date else None,
        status=status
    )
    return f"✅ Task created: '{task.title}' | Priority: {task.priority} | Due: {task.due_date or 'Not set'}"


def create_goal(user, title, description='', category='personal', target_date=None, progress=0):
    goal = Goal.objects.create(
        user=user,
        title=title,
        description=description,
        category=category.lower() if category.lower() in ['personal','career','health','finance','learning','other'] else 'personal',
        status='active',
        progress=progress,
        target_date=target_date if target_date else None
    )
    return f"✅ Goal created: '{goal.title}' | Category: {goal.category} | Target: {goal.target_date or 'Not set'}"


def parse_and_execute_tool(user, ai_response: str):
    """
    Detect if AI response contains a tool call block and execute it.
    Returns (clean_response, tool_result)
    """
    if '```tool' not in ai_response:
        return ai_response, None

    try:
        # Extract tool block
        start = ai_response.index('```tool') + 7
        end = ai_response.index('```', start)
        tool_json = ai_response[start:end].strip()
        tool_data = json.loads(tool_json)

        tool_name = tool_data.get('tool')
        params = tool_data.get('params', {})

        if tool_name == 'create_note':
            result = create_note(user, **params)
        elif tool_name == 'create_task':
            result = create_task(user, **params)
        elif tool_name == 'create_goal':
            result = create_goal(user, **params)
        else:
            result = None

        # Remove tool block from response shown to user
        clean = ai_response[:ai_response.index('```tool')].strip()
        if not clean:
            clean = "Done! Here's what I did:"

        return clean, result

    except Exception as e:
        return ai_response, None