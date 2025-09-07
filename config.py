import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'supersecretkey')
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = 'sessions'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(os.path.dirname(__file__), "mental_wellness.db")}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    LANGUAGES = ['en', 'hi', 'bn', 'ta', 'te', 'mr']
    CRISIS_KEYWORDS = [
        # English keywords
        'suicide', 'self-harm', 'ending life', "can't go on", 'kill myself', 'want to die',
        'no reason to live', 'better off dead', 'end it all', 'suicidal thoughts',
        'cutting myself', 'overdose', 'jump off', 'hang myself', 'drown myself',
        'hurt myself', 'self injury', 'self destructive',

        # Hindi keywords
        'आत्महत्या', 'आत्म-हानि', 'जीवन समाप्त करना', 'नहीं जा सकता',
        'खुद को मारना', 'मर जाना चाहता', 'जीना नहीं चाहता', 'सब खत्म कर दूं',
        'कोई वजह नहीं', 'मरना बेहतर', 'सब खत्म', 'आत्मघाती विचार',
        'खुद को काटना', 'दवा ज्यादा खाना', 'कूद जाना', 'फांसी लगाना',
        'डूब जाना', 'खुद को चोट पहुंचाना', 'आत्म विनाशी',

        # Hinglish keywords (common in India)
        'suicide karna', 'self harm karna', 'marna chahta', 'end karna',
        'life khatam', 'jaan dena', 'khatam karna', 'suicidal feel kar raha',
        'cut karna', 'overdose karna', 'jump karna', 'hang karna',
        'drown karna', 'hurt karna', 'self injury karna',

        # Additional crisis indicators
        'hopeless', 'worthless', 'no future', 'give up', 'tired of living',
        'pain too much', 'suffering too much', 'depression severe',
        'anxiety attack', 'panic attack severe', 'mental breakdown',
        'निराशा', 'बेकार', 'कोई भविष्य नहीं', 'हार मानना', 'जीने से थक गया',
        'दर्द बहुत', 'सuffering बहुत', 'depression गंभीर', 'anxiety attack',
        'panic attack गंभीर', 'mental breakdown'
    ]
    HELPLINES = {
        'national': '+91-9152987821 (COOJ)',
        'vandrevala': '9999666555',
        'sneha': '044-24640050',
        # Add regional numbers as needed
    }
