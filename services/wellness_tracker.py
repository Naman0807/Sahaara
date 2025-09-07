from models import db, UserSession
from datetime import datetime, timedelta
import json

class WellnessTracker:
    @staticmethod
    def log_mood(session_id, mood):
        session = UserSession.query.filter_by(session_id=session_id).first()
        if session:
            session.add_mood_entry(mood)
            session.update_activity()
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_mood_history(session_id):
        session = UserSession.query.filter_by(session_id=session_id).first()
        if session:
            return session.get_mood_history()
        return []

    @staticmethod
    def get_mood_trend(session_id, days=7):
        history = WellnessTracker.get_mood_history(session_id)
        if not history:
            return None
        recent = [entry for entry in history if datetime.fromisoformat(entry['date']) > datetime.utcnow() - timedelta(days=days)]
        if not recent:
            return None
        avg_mood = sum(entry['mood'] for entry in recent) / len(recent)
        return avg_mood

    @staticmethod
    def set_reminder(session_id, reminder_type, time):
        session = UserSession.query.filter_by(session_id=session_id).first()
        if session:
            session.set_preference(f'reminder_{reminder_type}', time)
            return True
        return False

    @staticmethod
    def get_reminder(session_id, reminder_type):
        session = UserSession.query.filter_by(session_id=session_id).first()
        if session:
            return session.get_preference(f'reminder_{reminder_type}')
        return None

    @staticmethod
    def should_send_mood_reminder(session_id):
        """Check if user should receive a mood reminder today."""
        session = UserSession.query.filter_by(session_id=session_id).first()
        if not session:
            return False

        # Check if user has mood reminders enabled
        reminders_enabled = session.get_preference('mood_reminders_enabled', True)
        if not reminders_enabled:
            return False

        # Check if user has logged mood today
        today = datetime.utcnow().date()
        mood_history = session.get_mood_history()
        today_entries = [entry for entry in mood_history if datetime.fromisoformat(entry['date']).date() == today]

        # Send reminder if no mood logged today and it's between 9 AM and 9 PM
        now = datetime.utcnow()
        if not today_entries and 9 <= now.hour <= 21:
            # Check last reminder time to avoid spamming
            last_reminder = session.get_preference('last_mood_reminder')
            if last_reminder:
                last_reminder_time = datetime.fromisoformat(last_reminder)
                # Don't send reminder more than once every 4 hours
                if (now - last_reminder_time).total_seconds() < 14400:  # 4 hours
                    return False

            return True
        return False

    @staticmethod
    def mark_mood_reminder_sent(session_id):
        """Mark that a mood reminder was sent to user."""
        session = UserSession.query.filter_by(session_id=session_id).first()
        if session:
            session.set_preference('last_mood_reminder', datetime.utcnow().isoformat())
            db.session.commit()

    @staticmethod
    def get_mood_streak(session_id):
        """Calculate current mood logging streak in days."""
        session = UserSession.query.filter_by(session_id=session_id).first()
        if not session:
            return 0

        mood_history = session.get_mood_history()
        if not mood_history:
            return 0

        # Sort by date descending
        sorted_history = sorted(mood_history, key=lambda x: x['date'], reverse=True)

        streak = 0
        current_date = datetime.utcnow().date()

        for entry in sorted_history:
            entry_date = datetime.fromisoformat(entry['date']).date()

            # If this entry is for today or yesterday (continuing streak)
            if entry_date == current_date or entry_date == current_date - timedelta(days=streak):
                streak += 1
                current_date = entry_date
            else:
                break

        return streak

    @staticmethod
    def get_weekly_mood_summary(session_id):
        """Get mood summary for the current week."""
        session = UserSession.query.filter_by(session_id=session_id).first()
        if not session:
            return None

        mood_history = session.get_mood_history()
        if not mood_history:
            return None

        # Get entries from the last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_entries = [entry for entry in mood_history if datetime.fromisoformat(entry['date']) > week_ago]

        if not weekly_entries:
            return None

        # Calculate statistics
        moods = [entry['mood'] for entry in weekly_entries]
        avg_mood = sum(moods) / len(moods)
        best_day = max(weekly_entries, key=lambda x: x['mood'])
        worst_day = min(weekly_entries, key=lambda x: x['mood'])

        return {
            'average_mood': round(avg_mood, 1),
            'entries_count': len(weekly_entries),
            'best_mood': best_day,
            'worst_mood': worst_day,
            'streak': WellnessTracker.get_mood_streak(session_id)
        }

    @staticmethod
    def schedule_nudge(session_id, nudge_type, scheduled_time=None):
        """Schedule a wellness nudge for the user."""
        session = UserSession.query.filter_by(session_id=session_id).first()
        if not session:
            return False

        if scheduled_time is None:
            scheduled_time = datetime.utcnow() + timedelta(hours=1)  # Default to 1 hour from now

        # Get existing nudges
        nudges = session.get_preference('scheduled_nudges', [])
        if not isinstance(nudges, list):
            nudges = []

        # Add new nudge
        nudge = {
            'id': f"{nudge_type}_{int(datetime.utcnow().timestamp())}",
            'type': nudge_type,
            'scheduled_time': scheduled_time.isoformat(),
            'sent': False
        }

        nudges.append(nudge)
        session.set_preference('scheduled_nudges', nudges)
        db.session.commit()
        return True

    @staticmethod
    def get_pending_nudges(session_id):
        """Get all pending nudges that should be sent now."""
        session = UserSession.query.filter_by(session_id=session_id).first()
        if not session:
            return []

        nudges = session.get_preference('scheduled_nudges', [])
        if not isinstance(nudges, list):
            return []

        now = datetime.utcnow()
        pending_nudges = []

        for nudge in nudges:
            if not nudge.get('sent', False):
                scheduled_time = datetime.fromisoformat(nudge['scheduled_time'])
                if scheduled_time <= now:
                    pending_nudges.append(nudge)

        return pending_nudges

    @staticmethod
    def mark_nudge_sent(session_id, nudge_id):
        """Mark a nudge as sent."""
        session = UserSession.query.filter_by(session_id=session_id).first()
        if not session:
            return False

        nudges = session.get_preference('scheduled_nudges', [])
        if not isinstance(nudges, list):
            return False

        for nudge in nudges:
            if nudge.get('id') == nudge_id:
                nudge['sent'] = True
                nudge['sent_time'] = datetime.utcnow().isoformat()
                break

        session.set_preference('scheduled_nudges', nudges)
        db.session.commit()
        return True
