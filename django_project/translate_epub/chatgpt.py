from openai import OpenAI
import environ
import re

env = environ.Env()
environ.Env.read_env()

API_BASE = env('API_BASE')
API_KEY = env('API_KEY')
API_MODEL = env('API_MODEL')

class ChatGPT:
    def translate(self, text, lang_from, lang_to):
        print('Original Text:')
        print(text)
        if not text.strip():
            return ''

        if re.match(r'^[\d\s\-\?]*$', text):
            print('Text contains only digits and allowed punctuation. Returning original.')
            return text

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

    def ask(self, content, question):
        if not content.strip() or not question.strip():
            return ''
        
        client = OpenAI(
            base_url=API_BASE,
            api_key=API_KEY,
        )
        
        try:
            completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that answers questions based on the provided content."
                    },
                    {
                        "role": "user",
                        "content": f"Here's some content:\n\n{content}\n\nPlease answer the following question based on this content:\n\n{question}"
                    }
                ],
                model=API_MODEL,
            )
            
            answer = (
                completion.choices[0].message.content
                .encode("utf8")
                .decode()
            )
            
            print('Question:', question)
            print('Answer:', answer)
            
            return answer
        
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return f"An error occurred while processing your request: {str(e)}"


