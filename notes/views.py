from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Note, Tag
from .forms import NoteForm
from assistant.gemini_client import ask_gemini


@login_required
def note_list(request):
    query = request.GET.get('q', '')
    notes = Note.objects.filter(user=request.user)
    if query:
        notes = notes.filter(title__icontains=query) | notes.filter(content__icontains=query)
    return render(request, 'notes/list.html', {'notes': notes, 'query': query})


@login_required
def note_create(request):
    form = NoteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        note = form.save(commit=False)
        note.user = request.user
        note.save()

        # Handle tags
        tags_input = form.cleaned_data.get('tags_input', '')
        if tags_input:
            for tag_name in tags_input.split(','):
                tag_name = tag_name.strip().lower()
                if tag_name:
                    tag, _ = Tag.objects.get_or_create(user=request.user, name=tag_name)
                    note.tags.add(tag)

        messages.success(request, 'Note created successfully!')
        return redirect('notes:detail', pk=note.pk)

    return render(request, 'notes/form.html', {'form': form, 'action': 'Create'})


@login_required
def note_detail(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    return render(request, 'notes/detail.html', {'note': note})


@login_required
def note_edit(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    form = NoteForm(request.POST or None, instance=note)
    if request.method == 'POST' and form.is_valid():
        note = form.save()

        # Update tags
        note.tags.clear()
        tags_input = form.cleaned_data.get('tags_input', '')
        if tags_input:
            for tag_name in tags_input.split(','):
                tag_name = tag_name.strip().lower()
                if tag_name:
                    tag, _ = Tag.objects.get_or_create(user=request.user, name=tag_name)
                    note.tags.add(tag)

        messages.success(request, 'Note updated!')
        return redirect('notes:detail', pk=note.pk)

    return render(request, 'notes/form.html', {'form': form, 'action': 'Edit', 'note': note})


@login_required
def note_delete(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    if request.method == 'POST':
        note.delete()
        messages.success(request, 'Note deleted.')
        return redirect('notes:list')
    return render(request, 'notes/confirm_delete.html', {'note': note})


@login_required
@require_POST
def note_ai_summarize(request, pk):
    """AI summarize a note using Gemini — called via AJAX"""
    note = get_object_or_404(Note, pk=pk, user=request.user)

    if not note.content.strip():
        return JsonResponse({'error': 'Note content is empty.'}, status=400)

    prompt = f"""
    Summarize the following note in 3-5 clear bullet points.
    Be concise and capture the key ideas only.

    Note Title: {note.title}
    Note Content:
    {note.content}

    Return only the bullet points, no extra explanation.
    """

    summary = ask_gemini(prompt)
    note.ai_summary = summary
    note.save()

    return JsonResponse({'summary': summary})


@login_required
@require_POST
def note_ai_improve(request, pk):
    """AI improve writing of a note using Gemini"""
    note = get_object_or_404(Note, pk=pk, user=request.user)

    if not note.content.strip():
        return JsonResponse({'error': 'Note content is empty.'}, status=400)

    prompt = f"""
    Improve the writing of the following note. Make it clearer, more structured,
    and professional while keeping the original meaning intact.

    Note:
    {note.content}

    Return only the improved note content, nothing else.
    """

    improved = ask_gemini(prompt)
    return JsonResponse({'improved': improved})