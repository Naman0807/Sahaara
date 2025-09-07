from datetime import datetime
from models import db

class UserBadge(db.Model):
    __tablename__ = 'user_badges'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), nullable=False, index=True)
    badge_id = db.Column(db.Integer, db.ForeignKey('badges.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=datetime.utcnow)
    progress_value = db.Column(db.Integer, nullable=True)  # Current progress towards badge
    is_earned = db.Column(db.Boolean, default=True)

    def __init__(self, session_id, badge_id, progress_value=None):
        self.session_id = session_id
        self.badge_id = badge_id
        self.progress_value = progress_value

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'badge_id': self.badge_id,
            'earned_at': self.earned_at.isoformat() if self.earned_at else None,
            'progress_value': self.progress_value,
            'is_earned': self.is_earned
        }

    @staticmethod
    def get_user_badges(session_id):
        """Get all badges earned by a user."""
        return UserBadge.query.filter_by(session_id=session_id, is_earned=True)\
            .join(Badge)\
            .order_by(UserBadge.earned_at.desc())\
            .all()

    @staticmethod
    def get_user_badge_progress(session_id):
        """Get user's progress towards all badges."""
        from models import Badge

        user_badges = {}
        earned_badges = UserBadge.query.filter_by(session_id=session_id, is_earned=True).all()
        all_badges = Badge.query.filter_by(is_active=True).all()

        # Mark earned badges
        for user_badge in earned_badges:
            user_badges[user_badge.badge_id] = {
                'earned': True,
                'earned_at': user_badge.earned_at,
                'progress': user_badge.progress_value
            }

        # Add unearned badges with progress
        for badge in all_badges:
            if badge.id not in user_badges:
                progress = UserBadge._calculate_progress(session_id, badge)
                user_badges[badge.id] = {
                    'earned': False,
                    'progress': progress,
                    'percentage': min(100, (progress / badge.criteria_value) * 100) if badge.criteria_value > 0 else 0
                }

        return user_badges

    @staticmethod
    def _calculate_progress(session_id, badge):
        """Calculate user's progress towards a specific badge."""
        from models import MoodEntry, JournalEntry, Conversation, MicroPlanProgress, StudySession

        if badge.criteria_type == 'count':
            if badge.category == 'mood':
                return MoodEntry.query.filter_by(session_id=session_id).count()
            elif badge.category == 'journal':
                return JournalEntry.query.filter_by(session_id=session_id).count()
            elif badge.category == 'chat':
                return Conversation.query.filter_by(session_id=session_id).count()
            elif badge.category == 'wellness':
                return MicroPlanProgress.query.filter_by(session_id=session_id)\
                    .filter_by(is_completed=True).count()
            elif badge.category == 'study':
                return StudySession.query.filter_by(session_id=session_id).count()

        elif badge.criteria_type == 'streak':
            if badge.category == 'mood':
                return UserBadge._calculate_mood_streak(session_id)
            elif badge.category == 'streak':
                # Generic streak across all activities
                return max(
                    UserBadge._calculate_mood_streak(session_id),
                    UserBadge._calculate_journal_streak(session_id),
                    UserBadge._calculate_study_streak(session_id)
                )

        elif badge.criteria_type == 'time':
            if badge.category == 'study':
                total_time = db.session.query(db.func.sum(StudySession.duration))\
                    .filter(StudySession.session_id == session_id)\
                    .scalar() or 0
                return total_time // 60  # Convert to minutes

        elif badge.criteria_type == 'milestone':
            if badge.name == 'Mood Improver':
                return UserBadge._calculate_mood_improvement_count(session_id)

        return 0

    @staticmethod
    def _calculate_mood_streak(session_id):
        """Calculate current mood logging streak."""
        from models import MoodEntry
        from datetime import datetime, timedelta

        # Get mood entries from last 60 days
        cutoff_date = datetime.utcnow() - timedelta(days=60)
        entries = MoodEntry.query.filter_by(session_id=session_id)\
            .filter(MoodEntry.created_at >= cutoff_date)\
            .order_by(MoodEntry.created_at.desc())\
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

    @staticmethod
    def _calculate_journal_streak(session_id):
        """Calculate current journal writing streak."""
        from models import JournalEntry
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=60)
        entries = JournalEntry.query.filter_by(session_id=session_id)\
            .filter(JournalEntry.created_at >= cutoff_date)\
            .order_by(JournalEntry.created_at.desc())\
            .all()

        if not entries:
            return 0

        streak = 0
        current_date = datetime.utcnow().date()
        entry_dates = {entry.created_at.date() for entry in entries}

        while current_date in entry_dates or (current_date - timedelta(days=1)) in entry_dates:
            if current_date in entry_dates:
                streak += 1
            current_date -= timedelta(days=1)

        return streak

    @staticmethod
    def _calculate_study_streak(session_id):
        """Calculate current study session streak."""
        from models import StudySession
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=60)
        sessions = StudySession.query.filter_by(session_id=session_id)\
            .filter(StudySession.created_at >= cutoff_date)\
            .order_by(StudySession.created_at.desc())\
            .all()

        if not sessions:
            return 0

        streak = 0
        current_date = datetime.utcnow().date()
        session_dates = {session.created_at.date() for session in sessions}

        while current_date in session_dates or (current_date - timedelta(days=1)) in session_dates:
            if current_date in session_dates:
                streak += 1
            current_date -= timedelta(days=1)

        return streak

    @staticmethod
    def _calculate_mood_improvement_count(session_id):
        """Calculate number of journal entries showing mood improvement."""
        from models import JournalEntry

        entries = JournalEntry.query.filter_by(session_id=session_id)\
            .filter(JournalEntry.mood_before.isnot(None))\
            .filter(JournalEntry.mood_after.isnot(None))\
            .all()

        improvement_count = 0
        for entry in entries:
            if entry.mood_after > entry.mood_before:
                improvement_count += 1

        return improvement_count

    @staticmethod
    def check_and_award_badges(session_id):
        """Check if user has earned any new badges and award them."""
        from models import Badge

        earned_badges = []

        badges = Badge.query.filter_by(is_active=True).all()
        for badge in badges:
            # Check if user already has this badge
            existing = UserBadge.query.filter_by(session_id=session_id, badge_id=badge.id, is_earned=True).first()
            if existing:
                continue

            # Calculate current progress
            progress = UserBadge._calculate_progress(session_id, badge)

            # Check if criteria is met
            if progress >= badge.criteria_value:
                # Award the badge
                user_badge = UserBadge(session_id=session_id, badge_id=badge.id, progress_value=progress)
                db.session.add(user_badge)
                earned_badges.append(badge)
            else:
                # Update progress if not earned yet
                progress_badge = UserBadge.query.filter_by(session_id=session_id, badge_id=badge.id, is_earned=False).first()
                if progress_badge:
                    progress_badge.progress_value = progress
                else:
                    progress_badge = UserBadge(session_id=session_id, badge_id=badge.id, progress_value=progress)
                    progress_badge.is_earned = False
                    db.session.add(progress_badge)

        if earned_badges:
            db.session.commit()

        return earned_badges

    @staticmethod
    def get_recently_earned_badges(session_id, days=7):
        """Get badges earned in the last N days."""
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return UserBadge.query.filter_by(session_id=session_id, is_earned=True)\
            .filter(UserBadge.earned_at >= cutoff_date)\
            .join(Badge)\
            .order_by(UserBadge.earned_at.desc())\
            .all()
