from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
import datetime
import json
from .models import Conversation, Message
from .gemini_client import chat_with_history
from .tools import parse_and_execute_tool
from notes.models import Note
from tasks.models import Task
from goals.models import Goal


def build_system_prompt(user):
    notes = Note.objects.filter(user=user).order_by('-created_at')[:5]

    notes_text = "\n".join([f"- {n.title}: {n.content[:150]}" for n in notes]) or "No notes yet."
    tasks_text = "\n".join([
        f"- [{t.status.upper()}] {t.title} | Priority: {t.priority} | Due: {t.due_date or 'No date'}"
        for t in Task.objects.filter(user=user).order_by('due_date')[:10]
    ]) or "No tasks yet."
    goals_text = "\n".join([
        f"- [{g.status.upper()}] {g.title} | Category: {g.category} | Progress: {g.progress}% | Target: {g.target_date or 'No date'}"
        for g in Goal.objects.filter(user=user)[:10]
    ]) or "No goals yet."

    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now_ist = datetime.datetime.now(ist)
    date_str = now_ist.strftime('%A, %B %d, %Y at %I:%M %p IST')

    return f"""You are FlowMind AI, a smart personal productivity assistant for {user.username}.
You have access to the user's REAL workspace data AND can create notes, tasks, and goals.

📝 RECENT NOTES:
{notes_text}

✅ ALL TASKS:
{tasks_text}

🎯 ALL GOALS:
{goals_text}

🕐 Current Date & Time: {date_str}

== TOOLS ==
When the user asks you to CREATE a note, task, or goal — follow this exact flow:

STEP 1 — GATHER INFO FIRST:
Before using any tool block, check if you have all required info.
If any required field is missing, ask the user for it in a friendly way.
Ask for ALL missing fields in ONE message, not one by one.

REQUIRED FIELDS:
- Note: title (ask for content too if not given)
- Task: title, priority (low/medium/high), due date
- Goal: title, category (personal/career/health/finance/learning/other), target date

EXAMPLE FLOWS:

User: "Create a task: Buy groceries"
AI: "Sure! A couple of quick questions to set it up properly:
     1. What priority? (low / medium / high)
     2. Any due date? (or say 'no deadline')"

User: "high priority, due July 20"
AI: [NOW use the tool block with all info collected]
```tool
{{"tool": "create_task", "params": {{"title": "Buy groceries", "priority": "high", "due_date": "2026-07-20"}}}}
```

User: "Create a goal: Learn Python"
AI: "Great goal! Just need a couple of details:
     1. Which category? (personal / career / health / finance / learning / other)
     2. Target completion date? (or say 'no deadline')"

User: "learning, target September 30"
AI: [NOW use tool block]
```tool
{{"tool": "create_goal", "params": {{"title": "Learn Python", "category": "learning", "target_date": "2026-09-30", "progress": 0}}}}
```

STEP 2 — ONLY use tool block when you have ALL required fields from the user.
STEP 3 — After tool executes, confirm what was created with the actual values.

STRICT RULES:
- Never assume or invent field values
- Always ask before creating
- Ask all missing fields in ONE message
- Use tool block ONLY after user provides all fields
- If user says 'no deadline' or 'no date' → omit that field entirely

RULES:
- ALWAYS use a tool block when user asks to create anything — never just say "I created it"
- After the tool block, write a friendly confirmation message
- For dates use YYYY-MM-DD format
- Priority must be: low, medium, or high
- Category must be one of: personal, career, health, finance, learning, other
- Always reference actual workspace data when answering questions
- Never say "no tasks/goals" if data exists above
- Today is {now_ist.strftime('%A')}
"""


@login_required
def chat_home(request):
    conversations = Conversation.objects.filter(user=request.user)
    return render(request, 'assistant/home.html', {'conversations': conversations})


@login_required
def conversation_new(request):
    conv = Conversation.objects.create(user=request.user, title='New Conversation')
    return redirect('assistant:conversation', pk=conv.pk)


@login_required
def conversation_detail(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    all_conversations = Conversation.objects.filter(user=request.user)
    chat_messages = conversation.messages.all()
    return render(request, 'assistant/chat.html', {
        'conversation': conversation,
        'chat_messages': chat_messages,
        'all_conversations': all_conversations,
    })


@login_required
@require_POST
def conversation_send(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    data = json.loads(request.body)
    user_message = data.get('message', '').strip()

    if not user_message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    # Save user message
    Message.objects.create(conversation=conversation, role='user', content=user_message)

    # Auto-title conversation
    if conversation.title == 'New Conversation':
        conversation.title = user_message[:50]
        conversation.save()

    # Build history
    history = list(conversation.messages.values('role', 'content').order_by('created_at'))
    system_prompt = build_system_prompt(request.user)
    ai_response = chat_with_history(history, system_prompt=system_prompt)

    # ✅ Parse and execute any tool calls
    clean_response, tool_result = parse_and_execute_tool(request.user, ai_response)

    # Build final message shown to user
    final_response = clean_response
    if tool_result:
        final_response = f"{clean_response}\n\n{tool_result}"

    # Save AI response
    Message.objects.create(conversation=conversation, role='assistant', content=final_response)

    return JsonResponse({
        'response': final_response,
        'conversation_title': conversation.title,
        'tool_executed': tool_result is not None
    })


@login_required
@require_POST
def conversation_delete(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    conversation.delete()
    return JsonResponse({'success': True})