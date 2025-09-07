import google.generativeai as genai
from dotenv import load_dotenv
import os

class GeminiService:
    def __init__(self):
        load_dotenv()  # Load environment variables from .env file
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("❌ GEMINI_API_KEY not found. Please set it in your .env file.")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')  # Using Gemini 1.5 Flash

    def generate_response(self, user_message, persona, language, conversation_history=None):
        # Adjust system prompt to handle Hinglish and cultural context
        if language == 'hinglish':
            language_desc = "Hinglish (a mix of Hindi and English, commonly used in India)"
        elif language == 'hi':
            language_desc = "Hindi"
        else:
            language_desc = "English"

        system_prompt = f"""
        You are a compassionate mental health companion for Indian youth.  
Your role is to respond with empathy, cultural sensitivity, and simple, practical guidance.  

Always:  
- Acknowledge the user’s feelings in a warm, understanding way.  
- Provide **direct, step-by-step suggestions** the user can try immediately (e.g., breathing exercises, journaling, calling a friend, listening to music, taking a walk, etc.).  
- Encourage small, doable actions that bring comfort or relief.  
- If the user shares ongoing sadness or hopelessness, gently recommend reaching out to a trusted friend, family member, or professional.  
- If the user expresses thoughts of self-harm or suicide, respond with urgency and compassion. Provide Indian helpline numbers (e.g., iCall: +91 9152987821, Vandrevala Foundation Helpline: 1860 266 2345, AASRA: +91 98204 66726) and strongly encourage contacting them right away.  

Tone:  
- Warm, supportive, and non-judgmental.  
- Use simple, everyday English (and switch naturally to Hindi/Gujarati/Hinglish if the user does).  
- Keep responses short, clear, and directly helpful instead of abstract explanations.  

Goal:  
Make the user feel heard, give them hope, and show them **exactly what they can do next** to feel a little better.

        The user persona is: {persona}.
        """

        if conversation_history:
            prompt = system_prompt + "\n\nConversation history:\n" + "\n".join(conversation_history) + "\n\nUser: " + user_message
        else:
            prompt = system_prompt + "\n\nUser: " + user_message

        response = self.model.generate_content(prompt)
        return response.text
