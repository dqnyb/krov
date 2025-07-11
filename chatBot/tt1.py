from google.cloud import translate_v2 as translate

def translate_text(text, target_language='ro'):
    translate_client = translate.Client()

    result = translate_client.translate(text, target_language=target_language)
    return result['translatedText']

# Exemplu de utilizare
text = "Hello, how are you?"
translated = translate_text(text, target_language='ro')
print(translated)  # Va afișa: "Salut, ce faci?"