from models import StudySession, db
from datetime import datetime, timedelta
import json

class StudyTimerService:
    @staticmethod
    def start_session(session_id, subject=None, mood_before=None):
        """Start a new study session."""
        # Check if there's an active session
        active_session = StudyTimerService.get_active_session(session_id)
        if active_session:
            return None, "An active study session already exists"

        session = StudySession(
            session_id=session_id,
            duration=0,  # Will be updated when stopped
            subject=subject,
            mood_before=mood_before
        )

        db.session.add(session)
        db.session.commit()

        return session, "Study session started"

    @staticmethod
    def stop_session(session_id, mood_after=None, productivity_rating=None, notes=None):
        """Stop the active study session."""
        active_session = StudyTimerService.get_active_session(session_id)
        if not active_session:
            return None, "No active study session found"

        # Calculate duration
        end_time = datetime.utcnow()
        duration = int((end_time - active_session.start_time).total_seconds())

        active_session.end_time = end_time
        active_session.duration = duration
        active_session.mood_after = mood_after
        active_session.productivity_rating = productivity_rating
        active_session.notes = notes
        active_session.completed = True

        db.session.commit()

        return active_session, f"Study session completed ({duration} seconds)"

    @staticmethod
    def pause_session(session_id):
        """Pause the active study session."""
        active_session = StudyTimerService.get_active_session(session_id)
        if not active_session:
            return None, "No active study session found"

        # For now, we'll just mark it as completed with current duration
        # In a more advanced implementation, you could track pause/resume times
        end_time = datetime.utcnow()
        duration = int((end_time - active_session.start_time).total_seconds())

        active_session.end_time = end_time
        active_session.duration = duration
        active_session.completed = False  # Mark as incomplete/paused

        db.session.commit()

        return active_session, "Study session paused"

    @staticmethod
    def get_active_session(session_id):
        """Get the currently active study session."""
        # An active session is one that doesn't have an end_time set
        return StudySession.query.filter_by(session_id=session_id, end_time=None).first()

    @staticmethod
    def get_session_status(session_id):
        """Get the status of the current study session."""
        active_session = StudyTimerService.get_active_session(session_id)
        if not active_session:
            return {'active': False}

        elapsed_time = int((datetime.utcnow() - active_session.start_time).total_seconds())

        return {
            'active': True,
            'session_id': active_session.id,
            'subject': active_session.subject,
            'start_time': active_session.start_time.isoformat(),
            'elapsed_seconds': elapsed_time,
            'elapsed_formatted': StudyTimerService._format_duration(elapsed_time),
            'mood_before': active_session.mood_before
        }

    @staticmethod
    def get_user_sessions(session_id, limit=20, offset=0):
        """Get study sessions for a user."""
        return StudySession.get_user_sessions(session_id, limit, offset)

    @staticmethod
    def get_session_by_id(session_id, user_session_id):
        """Get a specific study session."""
        return StudySession.query.filter_by(id=session_id, session_id=user_session_id).first()

    @staticmethod
    def update_session(session_id, user_session_id, **kwargs):
        """Update a study session."""
        session = StudySession.query.filter_by(id=session_id, session_id=user_session_id).first()
        if not session:
            return None

        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)

        db.session.commit()
        return session

    @staticmethod
    def delete_session(session_id, user_session_id):
        """Delete a study session."""
        session = StudySession.query.filter_by(id=session_id, session_id=user_session_id).first()
        if session:
            db.session.delete(session)
            db.session.commit()
            return True
        return False

    @staticmethod
    def get_study_stats(session_id, days=30):
        """Get comprehensive study statistics."""
        return StudySession.get_study_stats(session_id, days)

    @staticmethod
    def get_sessions_by_subject(session_id, subject):
        """Get sessions for a specific subject."""
        return StudySession.get_sessions_by_subject(session_id, subject)

    @staticmethod
    def get_sessions_by_date_range(session_id, start_date, end_date):
        """Get sessions within a date range."""
        return StudySession.get_sessions_by_date_range(session_id, start_date, end_date)

    @staticmethod
    def get_total_study_time(session_id, days=None):
        """Get total study time."""
        return StudySession.get_total_study_time(session_id, days)

    @staticmethod
    def get_study_streak(session_id):
        """Get current study streak."""
        return StudySession.get_study_streak(session_id)

    @staticmethod
    def get_recent_sessions(session_id, limit=10):
        """Get recent study sessions."""
        return StudySession.get_recent_sessions(session_id, limit)

    @staticmethod
    def suggest_break_time(session_id):
        """Suggest break time based on study patterns."""
        recent_sessions = StudyTimerService.get_recent_sessions(session_id, 10)

        if not recent_sessions:
            return 5  # Default 5 minutes

        # Calculate average session length
        avg_duration = sum(s.duration for s in recent_sessions) / len(recent_sessions)

        # Suggest break based on session length
        if avg_duration < 1800:  # Less than 30 minutes
            return 5
        elif avg_duration < 3600:  # Less than 1 hour
            return 10
        else:  # More than 1 hour
            return 15

    @staticmethod
    def get_productivity_insights(session_id):
        """Get productivity insights."""
        stats = StudyTimerService.get_study_stats(session_id, 30)

        insights = []

        # Study time insights
        if stats['total_sessions'] > 0:
            avg_session = stats['average_session_length']
            if avg_session < 1800:  # Less than 30 minutes
                insights.append({
                    'type': 'suggestion',
                    'message': 'Try longer study sessions for better focus',
                    'icon': 'fas fa-clock'
                })
            elif avg_session > 7200:  # More than 2 hours
                insights.append({
                    'type': 'warning',
                    'message': 'Consider taking breaks during long sessions',
                    'icon': 'fas fa-exclamation-triangle'
                })

        # Productivity insights
        if stats['average_productivity'] > 0:
            if stats['average_productivity'] >= 4:
                insights.append({
                    'type': 'success',
                    'message': 'Great productivity! Keep up the good work',
                    'icon': 'fas fa-star'
                })
            elif stats['average_productivity'] <= 2:
                insights.append({
                    'type': 'suggestion',
                    'message': 'Consider adjusting your study environment or techniques',
                    'icon': 'fas fa-lightbulb'
                })

        # Streak insights
        if stats['current_streak'] >= 7:
            insights.append({
                'type': 'achievement',
                'message': f'Impressive {stats["current_streak"]}-day study streak!',
                'icon': 'fas fa-fire'
            })

        # Mood insights
        if stats['mood_entries_count'] > 0:
            improvement_rate = stats['mood_improvements'] / stats['mood_entries_count']
            if improvement_rate > 0.7:
                insights.append({
                    'type': 'success',
                    'message': 'Study sessions are improving your mood!',
                    'icon': 'fas fa-smile'
                })

        return insights

    @staticmethod
    def get_study_goals(session_id):
        """Get or create study goals based on user's history."""
        stats = StudyTimerService.get_study_stats(session_id, 30)

        goals = []

        # Daily study time goal
        current_daily_avg = stats['total_time_seconds'] / 30
        suggested_daily = max(current_daily_avg * 1.2, 1800)  # At least 30 minutes, 20% increase

        goals.append({
            'type': 'daily_time',
            'current': int(current_daily_avg),
            'target': int(suggested_daily),
            'unit': 'seconds',
            'description': f'Study {StudyTimerService._format_duration(int(suggested_daily))} per day'
        })

        # Weekly sessions goal
        current_weekly_sessions = stats['total_sessions'] / 4.3  # Approximate weeks
        suggested_weekly = max(current_weekly_sessions * 1.1, 5)  # At least 5 sessions

        goals.append({
            'type': 'weekly_sessions',
            'current': int(current_weekly_sessions),
            'target': int(suggested_weekly),
            'unit': 'sessions',
            'description': f'Complete {int(suggested_weekly)} study sessions per week'
        })

        # Productivity goal
        if stats['average_productivity'] > 0:
            target_productivity = min(stats['average_productivity'] + 0.5, 5.0)
            goals.append({
                'type': 'productivity',
                'current': stats['average_productivity'],
                'target': target_productivity,
                'unit': 'rating',
                'description': f'Achieve {target_productivity} average productivity rating'
            })

        return goals

    @staticmethod
    def _format_duration(seconds):
        """Format duration in human readable format."""
        minutes = seconds // 60
        hours = minutes // 60
        minutes = minutes % 60
        seconds = seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    @staticmethod
    def export_sessions(session_id, start_date=None, end_date=None):
        """Export study sessions as JSON."""
        if start_date and end_date:
            sessions = StudySession.get_sessions_by_date_range(session_id, start_date, end_date)
        else:
            sessions = StudySession.get_user_sessions(session_id, limit=1000)

        export_data = {
            'export_date': datetime.utcnow().isoformat(),
            'session_id': session_id,
            'total_sessions': len(sessions),
            'total_time_seconds': sum(s.duration for s in sessions),
            'sessions': [session.to_dict() for session in sessions]
        }

        return export_data
