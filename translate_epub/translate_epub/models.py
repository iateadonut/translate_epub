from django.db import models

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Book: {self.book.file_name}, Item ID: {self.item_id}"

    class Meta:
        unique_together = ('book', 'item_id')

class Language(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class BookItemElement(models.Model):
    book_item = models.ForeignKey(BookItem, on_delete=models.CASCADE, related_name='elements')
    element_id = models.IntegerField()
    element_type = models.CharField(max_length=50)
    content = models.TextField()
    translated_content = models.TextField()
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    complete = models.BooleanField(default=False, db_default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Book Item: {self.book_item}, Element ID: {self.element_id}"

    class Meta:
        unique_together = ('book_item', 'element_id', 'language')
