from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Count, Q
from .models import Book, BookItem, Question, Answer, BookItemElement, Language
from django.urls import reverse
from .chatgpt import ChatGPT

from django.http import JsonResponse
from django.views.decorators.http import require_POST


@login_required
def home(request):
    books = Book.objects.all()
    languages = Language.objects.all()
    
    book_data = []
    for book in books:
        translations = BookItemElement.objects.filter(book_item__book=book).values('language').distinct()
        translation_count = translations.count()
        
        translation_links = []
        for lang in languages:
            if translations.filter(language=lang).exists():
                translation_links.append({
                    'language': lang,
                    'url': reverse('translate_book', args=[book.id, lang.id])
                })
        
        book_data.append({
            'book': book,
            'translation_count': translation_count,
            'translations': translation_links,
            'detail_url': reverse('book_detail', args=[book.id]),
        })
    
    return render(request, 'translate_epub/home.html', {'book_data': book_data})

@login_required
@require_POST
def update_element(request, element_id):
    element = get_object_or_404(BookItemElement, id=element_id)
    translation = request.POST.get('translation', '').strip()
    complete = request.POST.get('complete') == 'true'

    # Save the translation and completion status
    element.save_translation(translation, user=request.user)
    element.complete = complete
    element.save()

    return JsonResponse({'success': True, 'complete': element.complete})
    # Return a JSON response indicating success
    # return JsonResponse({'success': True})

def translate_book(request, book_id, language_id):
    book = get_object_or_404(Book, id=book_id)
    language = get_object_or_404(Language, id=language_id)
    show_completed = request.GET.get('show_completed', False)

    if show_completed:
        book_item_elements = BookItemElement.objects.filter(book_item__book=book, language=language)
    else:
        book_item_elements = BookItemElement.objects.filter(book_item__book=book, language=language, complete=False)

    paginator = Paginator(book_item_elements, 20)  # Show 20 elements per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.method == 'POST':
        for element in page_obj:
            translation = request.POST.get(f'translation_{element.id}')
            complete = request.POST.get(f'complete_{element.id}')
            # element.translated_content = translation
            element.save_translation(translation, user=request.user)
            element.complete = complete == 'on'
            element.save()

    context = {
        'book': book,
        'language': language,
        'page_obj': page_obj,
        'show_completed': show_completed,
    }
    return render(request, 'translate_epub/translate_book.html', context)


def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    book_items = book.items.all().order_by('item_id')
    return render(request, 'translate_epub/book_detail.html', {'book': book, 'book_items': book_items})

def book_item_detail(request, item_id):
    book_item = get_object_or_404(BookItem, id=item_id)
    
    # Get all questions related to this book item
    questions = Question.objects.filter(book_items=book_item)
    
    # Annotate questions with the count of related book items
    questions = questions.annotate(item_count=Count('book_items'))
    
    # Separate single questions and group questions
    single_questions = questions.filter(item_count=1)
    group_questions = questions.filter(item_count__gt=1)

    context = {
        'book_item': book_item,
        'single_questions': single_questions,
        'group_questions': group_questions,
    }
    return render(request, 'translate_epub/book_item_detail.html', context)


def ask_question(request, book_id):
    if request.method == 'POST':
        book = get_object_or_404(Book, id=book_id)
        selected_items = request.POST.getlist('selected_items')
        question_title = request.POST.get('question_title')
        question_content = request.POST.get('question_content')

        # Create a new Question object
        question = Question.objects.create(
            book=book,
            title=question_title,
            content=question_content
        )

        # Associate selected BookItems with the Question
        book_items = BookItem.objects.filter(id__in=selected_items)
        question.book_items.set(book_items)

        # Prepare content for AI processing
        content = "\n".join([item.content for item in book_items])

        # Use ChatGPT to generate an answer
        chatgpt = ChatGPT()
        ai_response = chatgpt.ask(content, question_content)

        # Create a new Answer object
        Answer.objects.create(
            question=question,
            content=ai_response
        )

        return redirect(reverse('book_item_detail', args=[book_items[0].id]))

    return redirect(reverse('book_detail', args=[book_id]))


