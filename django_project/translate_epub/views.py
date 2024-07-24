from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Book, BookItemElement, Language

@login_required
def home(request):
    # Add any necessary logic for the home view
    return render(request, 'translate_epub/home.html')

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

