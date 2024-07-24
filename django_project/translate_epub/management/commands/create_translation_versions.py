from django.core.management.base import BaseCommand
from translate_epub.models import BookItemElement, TranslationVersion
from django.db import transaction

class Command(BaseCommand):
    help = 'Creates TranslationVersion entries for existing BookItemElement instances'

    def handle(self, *args, **kwargs):
        self.stdout.write('Starting to create TranslationVersion entries...')

        book_item_elements = BookItemElement.objects.all()
        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            for element in book_item_elements:
                if not element.versions.exists():
                    TranslationVersion.objects.create(
                        book_item_element=element,
                        translated_content=element.translated_content,
                        is_machine_translation=True,  # Assume machine translation for existing entries
                        book_item_id=element.book_item_id,
                        element_id=element.element_id,
                        element_type=element.element_type,
                        language=element.language
                    )
                    created_count += 1
                else:
                    skipped_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} TranslationVersion entries'))
        self.stdout.write(f'Skipped {skipped_count} BookItemElements that already had versions')
