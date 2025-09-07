from . import db
from datetime import datetime

class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), db.ForeignKey('user_sessions.session_id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    language = db.Column(db.String(10), default='en')
    crisis_detected = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Conversation {self.id} for session {self.session_id}>'
