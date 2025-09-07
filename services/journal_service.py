from models import JournalEntry, db
from datetime import datetime, timedelta
import json

class JournalService:
    @staticmethod
    def create_entry(session_id, content, title=None, mood_before=None, mood_after=None, tags=None, encrypt=True):
        """Create a new journal entry."""
        entry = JournalEntry(
            session_id=session_id,
            content=content,
            title=title,
            mood_before=mood_before,
            mood_after=mood_after,
            encrypt=encrypt
        )

        if tags:
            entry.set_tags_list(tags)

        db.session.add(entry)
        db.session.commit()

        return entry

    @staticmethod
    def get_entries(session_id, limit=20, offset=0, decrypt=True):
        """Get journal entries for a user."""
        return JournalEntry.get_user_entries(session_id, limit, offset, decrypt)

    @staticmethod
    def get_entry_by_id(entry_id, session_id, decrypt=True):
        """Get a specific journal entry."""
        entry = JournalEntry.query.filter_by(id=entry_id, session_id=session_id).first()
        if entry and decrypt:
            return entry.decrypt_content()
        return entry

    @staticmethod
    def update_entry(entry_id, session_id, content=None, title=None, mood_before=None,
                    mood_after=None, tags=None, decrypt=True):
        """Update an existing journal entry."""
        entry = JournalEntry.query.filter_by(id=entry_id, session_id=session_id).first()
        if not entry:
            return None

        # If entry is encrypted, we need to decrypt it first to update
        if entry.is_encrypted and decrypt:
            entry = entry.decrypt_content()

        if content is not None:
            entry.content = content
        if title is not None:
            entry.title = title
        if mood_before is not None:
            entry.mood_before = mood_before
        if mood_after is not None:
            entry.mood_after = mood_after
        if tags is not None:
            entry.set_tags_list(tags)

        entry.updated_at = datetime.utcnow()

        # Re-encrypt if it was originally encrypted
        if entry.is_encrypted:
            entry._encrypt_content()

        db.session.commit()
        return entry

    @staticmethod
    def delete_entry(entry_id, session_id):
        """Delete a journal entry."""
        entry = JournalEntry.query.filter_by(id=entry_id, session_id=session_id).first()
        if entry:
            db.session.delete(entry)
            db.session.commit()
            return True
        return False

    @staticmethod
    def search_entries(session_id, query, decrypt=True):
        """Search journal entries."""
        return JournalEntry.search_entries(session_id, query, decrypt)

    @staticmethod
    def get_entries_by_tag(session_id, tag, decrypt=True):
        """Get entries by tag."""
        return JournalEntry.get_entries_by_tag(session_id, tag, decrypt)

    @staticmethod
    def get_entries_by_date_range(session_id, start_date, end_date, decrypt=True):
        """Get entries within a date range."""
        return JournalEntry.get_entries_by_date_range(session_id, start_date, end_date, decrypt)

    @staticmethod
    def get_entries_by_mood(session_id, mood_min=None, mood_max=None, decrypt=True):
        """Get entries filtered by mood range."""
        return JournalEntry.get_entries_by_mood(session_id, mood_min, mood_max, decrypt)

    @staticmethod
    def get_mood_trends(session_id, days=30):
        """Get mood trends from journal entries."""
        return JournalEntry.get_mood_trends(session_id, days)

    @staticmethod
    def get_journal_stats(session_id, days=30):
        """Get journal statistics."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Basic stats
        total_entries = JournalEntry.query.filter_by(session_id=session_id)\
            .filter(JournalEntry.created_at >= cutoff_date)\
            .count()

        # Mood stats
        entries_with_mood = JournalEntry.query.filter_by(session_id=session_id)\
            .filter(JournalEntry.created_at >= cutoff_date)\
            .filter(JournalEntry.mood_before.isnot(None))\
            .filter(JournalEntry.mood_after.isnot(None))\
            .all()

        mood_improvements = sum(1 for e in entries_with_mood if e.mood_after > e.mood_before)
        mood_declines = sum(1 for e in entries_with_mood if e.mood_after < e.mood_before)

        # Tag stats
        all_tags = []
        entries = JournalEntry.query.filter_by(session_id=session_id)\
            .filter(JournalEntry.created_at >= cutoff_date)\
            .all()

        for entry in entries:
            all_tags.extend(entry.get_tags_list())

        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Average mood
        if entries_with_mood:
            avg_mood_before = sum(e.mood_before for e in entries_with_mood) / len(entries_with_mood)
            avg_mood_after = sum(e.mood_after for e in entries_with_mood) / len(entries_with_mood)
        else:
            avg_mood_before = avg_mood_after = 0

        return {
            'period_days': days,
            'total_entries': total_entries,
            'entries_with_mood': len(entries_with_mood),
            'mood_improvements': mood_improvements,
            'mood_declines': mood_declines,
            'average_mood_before': round(avg_mood_before, 1),
            'average_mood_after': round(avg_mood_after, 1),
            'top_tags': [{'tag': tag, 'count': count} for tag, count in top_tags],
            'unique_tags': len(tag_counts)
        }

    @staticmethod
    def get_recent_entries(session_id, limit=5, decrypt=True):
        """Get recent journal entries."""
        return JournalEntry.get_user_entries(session_id, limit, 0, decrypt)

    @staticmethod
    def export_entries(session_id, start_date=None, end_date=None, decrypt=True):
        """Export journal entries as JSON."""
        if start_date and end_date:
            entries = JournalEntry.get_entries_by_date_range(session_id, start_date, end_date, decrypt)
        else:
            entries = JournalEntry.get_user_entries(session_id, limit=1000, decrypt=decrypt)

        export_data = {
            'export_date': datetime.utcnow().isoformat(),
            'session_id': session_id,
            'total_entries': len(entries),
            'entries': [entry.to_dict(include_encrypted=False) for entry in entries]
        }

        return export_data

    @staticmethod
    def get_writing_streak(session_id):
        """Calculate current writing streak."""
        from datetime import datetime, timedelta

        # Get entries from last 60 days
        cutoff_date = datetime.utcnow() - timedelta(days=60)
        entries = JournalEntry.query.filter_by(session_id=session_id)\
            .filter(JournalEntry.created_at >= cutoff_date)\
            .order_by(JournalEntry.created_at.desc())\
            .all()

        if not entries:
            return 0

        # Calculate streak
        streak = 0
        current_date = datetime.utcnow().date()
        entry_dates = {entry.created_at.date() for entry in entries}

        while current_date in entry_dates or (current_date - timedelta(days=1)) in entry_dates:
            if current_date in entry_dates:
                streak += 1
            current_date -= timedelta(days=1)

        return streak
