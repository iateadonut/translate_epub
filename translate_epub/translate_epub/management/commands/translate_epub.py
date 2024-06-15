from openai import OpenAI
import environ
from bs4 import BeautifulSoup as bs
from ebooklib import epub
from rich import print
import os

from django.core.management.base import BaseCommand
from django.db.models import Q
from translate_epub.models import Book, BookItem, BookItemElement, Language

env = environ.Env()
environ.Env.read_env()

API_BASE = env('API_BASE')
API_KEY = env('API_KEY')
API_MODEL = env('API_MODEL')

class Command(BaseCommand):
    help = 'Translates an .epub'

    def add_arguments(self, parser):
        parser.add_argument(
            '--lang_to',
            dest='lang_to',
            type=str,
            help='translate the epub to language',
        )
        parser.add_argument(
            '--lang_from',
            dest='lang_from',
            type=str,
            help='translate the epub from language',
        )
        parser.add_argument(
            '--book_name',
            dest='book_name',
            type=str,
            help='your epub book name',
        )
        parser.add_argument(
            '--mirror',
            action='store_true',
            help='keep both original and translated paragraphs',
        )

    def handle(self, *args, **options):
        if not options['book_name'].endswith('.epub'):
            raise Exception('This program translates .epub files only.')
        if not options['lang_to'] or not options['lang_from']:
            raise Exception('needs --lang_to and --lang_from')
        mirror = options.get('mirror', False)
        e = TEPUB(options['book_name'], options['lang_from'], options['lang_to'], mirror)
        e.translate_book()

class ChatGPT:
    # def __init__(self):

    def translate(self, text, lang_from, lang_to):
        print('Original Text:')
        # print('"' + text + '"')
        print(text)
        if not text.strip():
            return ''
        client = OpenAI(
                base_url=API_BASE,
                api_key=API_KEY,
                )
        language_to = lang_to
        language_from = lang_from
        try:
            completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": f"Return only a translation.  Keep line breaks.  Translate the following text from {language_from} into {language_to}.\n {language_from}: {text}\n{language_to}:"
                    }
                ],
                model=API_MODEL,
            )
            t_text = (
                completion.choices[0].message.content
                .encode("utf8")
                .decode()
            )
        except Exception as e:
            print(str(e))

        print('Translation:')
        print(t_text)
        return t_text


class TEPUB:
    def __init__(self, epub_name, lang_from, lang_to, mirror=False):
        self.epub_name = epub_name
        self.translate_model = ChatGPT()
        self.origin_book = epub.read_epub(self.epub_name)
        self.lang_from = lang_from
        self.lang_to = lang_to
        self.mirror = mirror

    def translate_book(self):
        base_name = os.path.basename(self.epub_name)
        name = os.path.splitext(base_name)[0]

        book, created = Book.objects.get_or_create(file_name=base_name)

        new_book = epub.EpubBook()
        new_book.metadata = self.origin_book.metadata
        new_book.spine = self.origin_book.spine
        new_book.toc = self.origin_book.toc

        for item_index, i in enumerate(self.origin_book.get_items()):
        # for i in self.origin_book.get_items():
            if i.get_type() == 9:

                book_item, item_created = BookItem.objects.get_or_create(
                    book=book,
                    item_id=item_index,
                    item_type=i.get_type(),
                    defaults={'content': i.content}
                )

                soup = bs(i.content, "html.parser")
                element_types = ['h1', 'h2', 'h3', 'h4', 'p', 'li']
                p_list = soup.findAll(element_types)

                for element_index, p in enumerate(p_list):
                    if p.text and not p.text.isdigit():

                        # Check if the book item element exists in the database for the specific language
                        book_item_element = BookItemElement.objects.filter(
                            book_item=book_item,
                            element_id=element_index,
                            element_type=p.name,
                            language__name=self.lang_to
                        ).first()

                        if book_item_element:
                            translation = book_item_element.translated_content
                        else:
                            # If the element doesn't exist, translate and save it to the database
                            translation = self.translate_model.translate(p.text, self.lang_from, self.lang_to)
                            language, _ = Language.objects.get_or_create(name=self.lang_to)
                            book_item_element = BookItemElement.objects.create(
                                book_item=book_item,
                                element_id=element_index,
                                element_type=p.name,
                                content=p.text,
                                translated_content=translation,
                                language=language,
                                complete=False
                            )

                        # Split translation into lines and create HTML with <br> for line breaks
                        translation_lines = translation.split('\n')
                        new_p_contents = soup.new_tag("span")  # Using span to insert HTML content inside p tag
                        for line in translation_lines:
                            if new_p_contents.contents:  # If not the first line, add a <br> before adding next line
                                new_p_contents.append(soup.new_tag("br"))
                            new_p_contents.append(soup.new_string(line))

                        new_p = soup.new_tag("p")
                        new_p.insert(0, new_p_contents)

                        if self.mirror:
                            p.insert_after(new_p)
                        else:
                            p.replace_with(new_p)
                        

                book_item.content = soup.prettify().encode()
                book_item.save()

                i.content = soup.prettify().encode()

            new_book.add_item(i)

        # name = self.epub_name.split(".")[0]
        # epub.write_epub(f"{name}_{self.lang_from}_to_{self.lang_to}.epub", new_book, {})
        if self.mirror:
            epub.write_epub(f"{name}_{self.lang_from}_to_{self.lang_to}_mirrored.epub", new_book, {})
        else:
            epub.write_epub(f"{name}_{self.lang_from}_to_{self.lang_to}.epub", new_book, {})


