from datetime import datetime, timedelta
from models import db
import json

class StudySession(db.Model):
    __tablename__ = 'study_sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=False, index=True)
    subject = db.Column(db.String(100), nullable=True)
    duration = db.Column(db.Integer, nullable=False)  # Duration in seconds
    break_duration = db.Column(db.Integer, default=0)  # Break duration in seconds
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)
    mood_before = db.Column(db.Integer, nullable=True)  # 1-10 scale
    mood_after = db.Column(db.Integer, nullable=True)  # 1-10 scale
    productivity_rating = db.Column(db.Integer, nullable=True)  # 1-5 scale
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, session_id, duration, subject=None, start_time=None, end_time=None,
                 break_duration=0, notes=None, mood_before=None, mood_after=None,
                 productivity_rating=None):
        self.session_id = session_id
        self.subject = subject
        self.duration = duration
        self.break_duration = break_duration
        self.start_time = start_time or datetime.utcnow()
        self.end_time = end_time or (self.start_time + timedelta(seconds=duration))
        self.notes = notes
        self.mood_before = mood_before
        self.mood_after = mood_after
        self.productivity_rating = productivity_rating

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'subject': self.subject,
            'duration': self.duration,
            'duration_formatted': self._format_duration(),
            'break_duration': self.break_duration,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'completed': self.completed,
            'notes': self.notes,
            'mood_before': self.mood_before,
            'mood_after': self.mood_after,
            'productivity_rating': self.productivity_rating,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def _format_duration(self):
        """Format duration in human readable format."""
        minutes = self.duration // 60
        seconds = self.duration % 60
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    @staticmethod
    def get_user_sessions(session_id, limit=50, offset=0):
        """Get study sessions for a user."""
        return StudySession.query.filter_by(session_id=session_id)\
            .order_by(StudySession.start_time.desc())\
            .limit(limit)\
            .offset(offset)\
            .all()

    @staticmethod
    def get_sessions_by_date_range(session_id, start_date, end_date):
        """Get sessions within a date range."""
        return StudySession.query.filter_by(session_id=session_id)\
            .filter(StudySession.start_time >= start_date)\
            .filter(StudySession.start_time <= end_date)\
            .order_by(StudySession.start_time.desc())\
            .all()

    @staticmethod
    def get_sessions_by_subject(session_id, subject):
        """Get sessions for a specific subject."""
        return StudySession.query.filter_by(session_id=session_id, subject=subject)\
            .order_by(StudySession.start_time.desc())\
            .all()

    @staticmethod
    def get_total_study_time(session_id, days=None):
        """Get total study time for a user."""
        query = db.session.query(db.func.sum(StudySession.duration))\
            .filter(StudySession.session_id == session_id)

        if days:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(StudySession.start_time >= cutoff_date)

        total_seconds = query.scalar() or 0
        return total_seconds

    @staticmethod
    def get_study_streak(session_id):
        """Calculate current study streak."""
        from datetime import datetime, timedelta

        # Get sessions from last 60 days
        cutoff_date = datetime.utcnow() - timedelta(days=60)
        sessions = StudySession.query.filter_by(session_id=session_id)\
            .filter(StudySession.start_time >= cutoff_date)\
            .order_by(StudySession.start_time.desc())\
            .all()

        if not sessions:
            return 0

        # Calculate streak
        streak = 0
        current_date = datetime.utcnow().date()
        session_dates = {session.start_time.date() for session in sessions}

        while current_date in session_dates or (current_date - timedelta(days=1)) in session_dates:
            if current_date in session_dates:
                streak += 1
            current_date -= timedelta(days=1)

        return streak

    @staticmethod
    def get_average_productivity(session_id, days=30):
        """Get average productivity rating."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = db.session.query(db.func.avg(StudySession.productivity_rating))\
            .filter(StudySession.session_id == session_id)\
            .filter(StudySession.start_time >= cutoff_date)\
            .filter(StudySession.productivity_rating.isnot(None))\
            .scalar()

        return round(result, 1) if result else 0

    @staticmethod
    def get_most_productive_time(session_id):
        """Get the most productive time of day."""
        sessions = StudySession.query.filter_by(session_id=session_id)\
            .filter(StudySession.productivity_rating.isnot(None))\
            .all()

        if not sessions:
            return None

        # Group by hour and calculate average productivity
        hourly_stats = {}
        for session in sessions:
            hour = session.start_time.hour
            if hour not in hourly_stats:
                hourly_stats[hour] = {'total': 0, 'count': 0}
            hourly_stats[hour]['total'] += session.productivity_rating
            hourly_stats[hour]['count'] += 1

        # Find hour with highest average productivity
        best_hour = None
        best_avg = 0
        for hour, stats in hourly_stats.items():
            avg = stats['total'] / stats['count']
            if avg > best_avg:
                best_avg = avg
                best_hour = hour

        return {
            'hour': best_hour,
            'average_productivity': round(best_avg, 1),
            'total_sessions': len(sessions)
        }

    @staticmethod
    def get_study_stats(session_id, days=30):
        """Get comprehensive study statistics."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Basic stats
        total_sessions = StudySession.query.filter_by(session_id=session_id)\
            .filter(StudySession.start_time >= cutoff_date)\
            .count()

        total_time = StudySession.get_total_study_time(session_id, days)
        avg_session_length = total_time / total_sessions if total_sessions > 0 else 0

        # Subject breakdown
        subject_stats = db.session.query(
            StudySession.subject,
            db.func.count(StudySession.id),
            db.func.sum(StudySession.duration)
        )\
        .filter(StudySession.session_id == session_id)\
        .filter(StudySession.start_time >= cutoff_date)\
        .filter(StudySession.subject.isnot(None))\
        .group_by(StudySession.subject)\
        .all()

        subjects = []
        for subject, count, time in subject_stats:
            subjects.append({
                'subject': subject,
                'sessions': count,
                'total_time': time,
                'average_time': time / count if count > 0 else 0
            })

        # Mood impact
        mood_entries = StudySession.query.filter_by(session_id=session_id)\
            .filter(StudySession.start_time >= cutoff_date)\
            .filter(StudySession.mood_before.isnot(None))\
            .filter(StudySession.mood_after.isnot(None))\
            .all()

        mood_improvements = sum(1 for s in mood_entries if s.mood_after > s.mood_before)
        mood_declines = sum(1 for s in mood_entries if s.mood_after < s.mood_before)

        return {
            'period_days': days,
            'total_sessions': total_sessions,
            'total_time_seconds': total_time,
            'total_time_formatted': StudySession._format_total_time(total_time),
            'average_session_length': avg_session_length,
            'average_session_formatted': StudySession._format_total_time(int(avg_session_length)),
            'current_streak': StudySession.get_study_streak(session_id),
            'average_productivity': StudySession.get_average_productivity(session_id, days),
            'subjects': subjects,
            'mood_entries_count': len(mood_entries),
            'mood_improvements': mood_improvements,
            'mood_declines': mood_declines,
            'most_productive_time': StudySession.get_most_productive_time(session_id)
        }

    @staticmethod
    def _format_total_time(total_seconds):
        """Format total time in human readable format."""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    @staticmethod
    def get_recent_sessions(session_id, limit=10):
        """Get recent study sessions."""
        return StudySession.query.filter_by(session_id=session_id)\
            .order_by(StudySession.start_time.desc())\
            .limit(limit)\
            .all()
