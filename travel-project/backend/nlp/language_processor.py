from inltk.inltk import identify_language, tokenize
from googletrans import Translator
import re

class LanguageProcessor:
    def __init__(self):
        self.translator = Translator()
        self.supported_languages = {
            'hi': 'Hindi',
            'ta': 'Tamil',
            'ml': 'Malayalam',
            'bn': 'Bengali',
            'en': 'English'
        }
    
    def detect_language(self, text):
        """Detect the language of input text"""
        try:
            lang_code = identify_language(text)
            return lang_code if lang_code in self.supported_languages else 'en'
        except:
            return 'en'
    
    def translate_to_english(self, text, source_lang):
        """Translate regional language text to English"""
        if source_lang == 'en':
            return text
        
        try:
            translated = self.translator.translate(text, src=source_lang, dest='en')
            return translated.text
        except Exception as e:
            print(f"Translation error: {e}")
            return text
    
    def tokenize_text(self, text, language):
        """Tokenize text based on language"""
        try:
            if language != 'en':
                tokens = tokenize(text, language)
            else:
                tokens = text.split()
            return tokens
        except:
            return text.split()