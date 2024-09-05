import zipfile
import xml.etree.ElementTree as ET
from .models import Book, BookItem, BookItemElement, Language
from .chatgpt import ChatGPT

import logging

# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class IDMLParser:
    def __init__(self, file_path, lang_from, lang_to):
        self.file_path = file_path
        self.lang_from = lang_from
        self.lang_to = lang_to
        self.namespace = {'idPkg': 'http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging'}
        self.translate_model = ChatGPT()

    def parse(self):
        with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
            book, _ = Book.objects.get_or_create(file_name=self.file_path)
            
            for file_name in zip_ref.namelist():
                if file_name.startswith('Stories/Story_') and file_name.endswith('.xml'):
                    story_content = zip_ref.read(file_name)
                    self.parse_story(book, file_name, story_content)

    def parse_story(self, book, story_file_name, story_content):
        root = ET.fromstring(story_content)
        story_element = root.find('Story', self.namespace)
        
        if story_element is None:
            raise ValueError(f"Could not find Story element in {story_file_name}")
        
        story_id = story_element.attrib.get('Self')
        if story_id is None:
            raise ValueError(f"Story element does not have a 'Self' attribute in {story_file_name}")
        
        book_item, _ = BookItem.objects.get_or_create(
            book=book,
            item_id=story_id,
            defaults={'content': story_content.decode('utf-8'), 'item_type': 9}  # 9 for IDML story
        )

        self.process_element(story_element, book_item)

    def process_element(self, element, book_item, element_counter=0):
        element_counter = int(element_counter)
        if element.tag.endswith('Content'):
            content = element.text
            if content and content.strip():
                element_counter += 1
                book_item_element, created = BookItemElement.objects.get_or_create(
                    book_item=book_item,
                    element_id=str(element_counter),
                    language=Language.objects.get(name=self.lang_from),
                    defaults={'content': content.strip()}
                )
                
                if created or not book_item_element.translated_content:
                    translation = self.translate_model.translate(content.strip(), self.lang_from, self.lang_to)
                    book_item_element.save_translation(translation, is_machine_translation=True)

        for child in element:
            element_counter = self.process_element(child, book_item, element_counter)

        return element_counter

class IDMLWriter:
    def __init__(self, input_file, output_path, lang_to):
        self.input_file = input_file
        self.output_path = output_path
        self.lang_to = lang_to
        self.namespace = {'idPkg': 'http://ns.adobe.com/AdobeInDesign/idml/1.0/packaging'}
        self.element_counter = 0

    def write(self):
        with zipfile.ZipFile(self.input_file, 'r') as input_zip:
            with zipfile.ZipFile(self.output_path, 'w') as output_zip:
                for item in input_zip.infolist():
                    if item.filename.startswith('Stories/Story_') and item.filename.endswith('.xml'):
                        story_content = input_zip.read(item.filename)
                        modified_content = self.modify_story_content(story_content)
                        output_zip.writestr(item.filename, modified_content)
                    else:
                        buffer = input_zip.read(item.filename)
                        output_zip.writestr(item.filename, buffer)

    def modify_story_content(self, story_content):
        root = ET.fromstring(story_content)
        story_element = root.find('Story', self.namespace)
        if story_element is not None:
            story_id = story_element.attrib.get('Self')
            logger.debug(f"Processing story with ID: {story_id}")
            try:
                book = Book.objects.get(file_name=self.input_file)
                book_item = BookItem.objects.get(book=book, item_id=story_id)
                self.element_counter = 0
                self.process_element(story_element, book_item)
            except Book.DoesNotExist:
                logger.error(f"Book not found for file: {self.input_file}")
            except BookItem.DoesNotExist:
                logger.error(f"BookItem not found for story ID: {story_id}")

        return ET.tostring(root, encoding='utf-8', xml_declaration=True)

    def process_element(self, element, book_item):
        if element.tag.endswith('Content'):
            self.element_counter += 1
            try:
                book_item_element = BookItemElement.objects.get(
                    book_item=book_item,
                    element_id=str(self.element_counter),
                )
                element.text = book_item_element.translated_content
                # logger.debug(f"Found translation for element {self.element_counter}: {element.text[:50]}...")
            except BookItemElement.DoesNotExist:
                logger.warning(f"Translation not found for element {self.element_counter} in language {self.lang_to}")

        for child in element:
            self.process_element(child, book_item)


