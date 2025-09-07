from datetime import datetime
from models import db
import json
from cryptography.fernet import Fernet
import base64
import os

class JournalEntry(db.Model):
    __tablename__ = 'journal_entries'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=False, index=True)
    title = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=False)
    mood_before = db.Column(db.Integer, nullable=True)  # 1-10 scale
    mood_after = db.Column(db.Integer, nullable=True)  # 1-10 scale
    tags = db.Column(db.Text, nullable=True)  # JSON array of tags
    is_encrypted = db.Column(db.Boolean, default=True)
    encryption_key = db.Column(db.Text, nullable=True)  # Base64 encoded key
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, session_id, content, title=None, mood_before=None, mood_after=None, tags=None, encrypt=True):
        self.session_id = session_id
        self.title = title
        self.content = content
        self.mood_before = mood_before
        self.mood_after = mood_after
        self.tags = json.dumps(tags) if tags else None
        self.is_encrypted = encrypt

        if encrypt:
            self._encrypt_content()
        else:
            self.encryption_key = None

    def _generate_key(self):
        """Generate a new encryption key."""
        return Fernet.generate_key()

    def _encrypt_content(self):
        """Encrypt the content and title if they exist."""
        key = self._generate_key()
        fernet = Fernet(key)

        if self.content:
            self.content = fernet.encrypt(self.content.encode()).decode()
        if self.title:
            self.title = fernet.encrypt(self.title.encode()).decode()

        self.encryption_key = base64.b64encode(key).decode()

    def decrypt_content(self):
        """Decrypt the content and return a copy with decrypted data."""
        if not self.is_encrypted or not self.encryption_key:
            return self

        try:
            key = base64.b64decode(self.encryption_key)
            fernet = Fernet(key)

            # Create a copy to avoid modifying the original
            decrypted_entry = JournalEntry(
                session_id=self.session_id,
                content=fernet.decrypt(self.content.encode()).decode() if self.content else '',
                title=fernet.decrypt(self.title.encode()).decode() if self.title else None,
                mood_before=self.mood_before,
                mood_after=self.mood_after,
                tags=self.tags,
                encrypt=False
            )
            decrypted_entry.id = self.id
            decrypted_entry.created_at = self.created_at
            decrypted_entry.updated_at = self.updated_at
            decrypted_entry.is_encrypted = False
            decrypted_entry.encryption_key = None

            return decrypted_entry
        except Exception as e:
            print(f"Decryption failed: {e}")
            return self

    def get_tags_list(self):
        """Get tags as a list."""
        if self.tags:
            try:
                return json.loads(self.tags)
            except:
                return []
        return []

    def set_tags_list(self, tags_list):
        """Set tags from a list."""
        self.tags = json.dumps(tags_list) if tags_list else None

    @staticmethod
    def get_user_entries(session_id, limit=50, offset=0, decrypt=True):
        """Get journal entries for a user."""
        entries = JournalEntry.query.filter_by(session_id=session_id)\
            .order_by(JournalEntry.created_at.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()

        if decrypt:
            return [entry.decrypt_content() for entry in entries]
        return entries

    @staticmethod
    def get_entries_by_date_range(session_id, start_date, end_date, decrypt=True):
        """Get entries within a date range."""
        entries = JournalEntry.query.filter_by(session_id=session_id)\
            .filter(JournalEntry.created_at >= start_date)\
            .filter(JournalEntry.created_at <= end_date)\
            .order_by(JournalEntry.created_at.desc())\
            .all()

        if decrypt:
            return [entry.decrypt_content() for entry in entries]
        return entries

    @staticmethod
    def get_entries_by_tag(session_id, tag, decrypt=True):
        """Get entries containing a specific tag."""
        entries = JournalEntry.query.filter_by(session_id=session_id)\
            .filter(JournalEntry.tags.contains(f'"{tag}"'))\
            .order_by(JournalEntry.created_at.desc())\
            .all()

        if decrypt:
            return [entry.decrypt_content() for entry in entries]
        return entries

    @staticmethod
    def get_entries_by_mood(session_id, mood_min=None, mood_max=None, decrypt=True):
        """Get entries filtered by mood range."""
        query = JournalEntry.query.filter_by(session_id=session_id)

        if mood_min is not None:
            query = query.filter(JournalEntry.mood_after >= mood_min)
        if mood_max is not None:
            query = query.filter(JournalEntry.mood_after <= mood_max)

        entries = query.order_by(JournalEntry.created_at.desc()).all()

        if decrypt:
            return [entry.decrypt_content() for entry in entries]
        return entries

    @staticmethod
    def search_entries(session_id, query, decrypt=True):
        """Search entries by content or title."""
        # Note: This is a basic search. For encrypted entries, search would be limited
        # In a real app, you might want to implement searchable encryption or search decrypted content
        entries = JournalEntry.query.filter_by(session_id=session_id)\
            .filter(
                db.or_(
                    JournalEntry.title.contains(query),
                    JournalEntry.content.contains(query)
                )
            )\
            .order_by(JournalEntry.created_at.desc())\
            .all()

        if decrypt:
            return [entry.decrypt_content() for entry in entries]
        return entries

    @staticmethod
    def get_mood_trends(session_id, days=30):
        """Get mood trends from journal entries."""
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        entries = JournalEntry.query.filter_by(session_id=session_id)\
            .filter(JournalEntry.created_at >= cutoff_date)\
            .filter(JournalEntry.mood_before.isnot(None))\
            .filter(JournalEntry.mood_after.isnot(None))\
            .order_by(JournalEntry.created_at)\
            .all()

        trends = []
        for entry in entries:
            trends.append({
                'date': entry.created_at.isoformat(),
                'mood_before': entry.mood_before,
                'mood_after': entry.mood_after,
                'improvement': entry.mood_after - entry.mood_before if entry.mood_after and entry.mood_before else 0
            })

        return trends

    def to_dict(self, include_encrypted=False):
        """Convert entry to dictionary."""
        data = {
            'id': self.id,
            'session_id': self.session_id,
            'title': self.title,
            'content': self.content,
            'mood_before': self.mood_before,
            'mood_after': self.mood_after,
            'tags': self.get_tags_list(),
            'is_encrypted': self.is_encrypted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

        if not include_encrypted and self.is_encrypted:
            data['title'] = '[ENCRYPTED]'
            data['content'] = '[ENCRYPTED - Click to decrypt]'

        return data
