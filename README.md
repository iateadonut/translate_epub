## translate epub

usage: python ./manage.py translate_epub --book=./translate_epub/test_data/14-test.epub --lang_from=Portuguese --lang_to=English --mirror

### What this does

This program queries a LLM in order to translate an epub, and then recompiles the epub in the translated language.

It also saves each element's translation in a database, so that, if the process is interrupted, you can start it again and it will simply pull from the database instead of asking the LLM for a translation.

There is also an interface within django, with the route: translate_book/{book_id}/{language_id} where you can modify the translations.

### Options

-- mirror - when generating the epub, this will keep the original, so that you can see the original language and then the translation one after the other

### Setup

Set this up just like a django application, by running the migrations and serving it.

You need to have the db tables set up in order to use the translator, but you do not need to have the app running unless you want to run the interface (which lets you change the translations of the books).

There is a .env file here: in django_project/translate_epub/.env.example

Modify the values there.  One set of values is for the openai-compatible api that you'll ask for a translation.  The other is the mysql database.
