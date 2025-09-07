class LanguageService:
    SUPPORTED_LANGUAGES = {
        'en': 'English',
        'hi': 'Hindi',
        'bn': 'Bengali',
        'ta': 'Tamil',
        'te': 'Telugu',
        'mr': 'Marathi',
        'hinglish': 'Hinglish'
    }

    HINGLISH_KEYWORDS = [
        'kya', 'hai', 'nahi', 'kar', 'raha', 'rah', 'hun', 'hoon', 'tha', 'thi',
        'ka', 'ki', 'ke', 'ko', 'se', 'me', 'pe', 'par', 'aur', 'lekin', 'magar',
        'fir', 'phir', 'ab', 'tab', 'jab', 'kab', 'kyun', 'kaise', 'kahan',
        'acha', 'theek', 'badiya', 'mast', 'cool', 'awesome', 'problem', 'issue',
        'friend', 'school', 'college', 'exam', 'study', 'homework', 'parents',
        'stress', 'tension', 'depression', 'anxiety', 'mood', 'happy', 'sad'
    ]

    @staticmethod
    def get_language_name(code):
        return LanguageService.SUPPORTED_LANGUAGES.get(code, 'English')

    @staticmethod
    def is_supported_language(code):
        return code in LanguageService.SUPPORTED_LANGUAGES

    @staticmethod
    def get_default_language():
        return 'en'

    @staticmethod
    def detect_language(text):
        """
        Detect the language of the input text.
        Returns 'hinglish' if it contains both English and Hindi words,
        otherwise returns the detected language code.
        """
        # Simple detection based on character sets and keywords
        has_hindi_chars = any('\u0900' <= char <= '\u097F' for char in text)
        has_english_chars = any(char.isascii() and char.isalpha() for char in text)

        if has_hindi_chars and has_english_chars:
            return 'hinglish'
        elif has_hindi_chars:
            return 'hi'
        else:
            return 'en'

    @staticmethod
    def is_hinglish(text):
        """
        Check if text is likely Hinglish (mix of Hindi and English).
        """
        words = text.lower().split()
        hindi_words = sum(1 for word in words if word in LanguageService.HINGLISH_KEYWORDS)
        english_words = sum(1 for word in words if word.isascii() and len(word) > 2)

        # If we have both Hindi keywords and English words, likely Hinglish
        return hindi_words > 0 and english_words > 0
