from django.db import models
from django.contrib.auth.models import User

class Book(models.Model):
    file_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file_name

class BookItem(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='items')
    item_id = models.IntegerField()
    item_type = models.IntegerField()
    content = models.TextField()
    heading = models.CharField(max_length=255, null=True, blank=True)
    subheading = models.CharField(max_length=255, null=True, blank=True)
    is_chapter = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Book: {self.book.file_name}, Item ID: {self.item_id}"

    class Meta:
        unique_together = ('book', 'item_id')

class Question(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='questions')
    book_items = models.ManyToManyField(BookItem, related_name='questions')
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.book.file_name}"

class Answer(models.Model):
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='answer')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to: {self.question.title}"

class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class TranslationVersion(models.Model):
    book_item_element = models.ForeignKey(
        'BookItemElement', 
        on_delete=models.SET_NULL,
        null=True,
        related_name='versions'
    )
    translated_content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_machine_translation = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Fields to maintain data integrity if BookItemElement is deleted
    book_item_id = models.IntegerField(null=True)
    element_id = models.IntegerField(null=True)
    element_type = models.CharField(max_length=50, null=True)
    language = models.ForeignKey('Language', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Translation version {self.id} created at {self.created_at}"

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.book_item_element:
            self.book_item_id = self.book_item_element.book_item_id
            self.element_id = self.book_item_element.element_id
            self.element_type = self.book_item_element.element_type
            self.language = self.book_item_element.language
        super().save(*args, **kwargs)

class BookItemElement(models.Model):
    book_item = models.ForeignKey('BookItem', on_delete=models.CASCADE, related_name='elements')
    element_id = models.IntegerField()
    element_type = models.CharField(max_length=50)
    content = models.TextField()
    translated_content = models.TextField()
    language = models.ForeignKey('Language', on_delete=models.CASCADE)
    complete = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Book Item: {self.book_item}, Element ID: {self.element_id}"

    class Meta:
        unique_together = ('book_item', 'element_id', 'language')

    def save_translation(self, translated_content, user=None, is_machine_translation=False):
        # Check if the content has actually changed
        if self.translated_content == translated_content:
            # Content hasn't changed, no need to create a new version
            return self.versions.filter(
                translated_content=translated_content,
                is_machine_translation=is_machine_translation
            ).first()
        
        # Content has changed, create a new version
        self.translated_content = translated_content
        self.save()
        
        new_version = TranslationVersion.objects.create(
            book_item_element=self,
            translated_content=translated_content,
            user=user,
            is_machine_translation=is_machine_translation
        )
        return new_version


