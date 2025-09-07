from . import db
from datetime import datetime
import json

class CrisisLog(db.Model):
    __tablename__ = 'crisis_logs'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), db.ForeignKey('user_sessions.session_id'), nullable=False)
    detected_keywords = db.Column(db.Text, nullable=False)  # JSON string of keywords
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    escalated = db.Column(db.Boolean, default=False)
    helpline_contacted = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f'<CrisisLog {self.id} for session {self.session_id}>'

    @staticmethod
    def detect_crisis(message, keywords):
        detected = []
        for keyword in keywords:
            if keyword.lower() in message.lower():
                detected.append(keyword)
        return detected

    def log_crisis(self, message, keywords):
        detected = self.detect_crisis(message, keywords)
        if detected:
            self.detected_keywords = json.dumps(detected)
            return True
        return False
