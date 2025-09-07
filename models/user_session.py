from . import db
from datetime import datetime
import json

class UserSession(db.Model):
    __tablename__ = 'user_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    persona = db.Column(db.String(50), nullable=True)  # e.g., 'class_10_12', 'college_youth', 'first_jobbers'
    language = db.Column(db.String(10), default='en')
    mood_history = db.Column(db.Text, default='[]')  # JSON string for mood check-ins
    preferences = db.Column(db.Text, default='{}')  # JSON string for user preferences

    def update_activity(self):
        self.last_activity = datetime.utcnow()

    def add_mood_entry(self, mood, date=None):
        if date is None:
            date = datetime.utcnow().isoformat()
        history = json.loads(self.mood_history)
        history.append({'mood': mood, 'date': date})
        self.mood_history = json.dumps(history)

    def get_mood_history(self):
        return json.loads(self.mood_history)

    def set_preference(self, key, value):
        prefs = json.loads(self.preferences)
        prefs[key] = value
        self.preferences = json.dumps(prefs)

    def get_preference(self, key, default=None):
        prefs = json.loads(self.preferences)
        return prefs.get(key, default)
