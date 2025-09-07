from datetime import datetime
from models import db
import json

class Badge(db.Model):
    __tablename__ = 'badges'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), nullable=True)  # FontAwesome icon class
    color = db.Column(db.String(20), default='primary')  # Bootstrap color class
    category = db.Column(db.String(50), nullable=False)  # mood, journal, chat, study, etc.
    criteria_type = db.Column(db.String(50), nullable=False)  # streak, count, milestone, etc.
    criteria_value = db.Column(db.Integer, nullable=False)  # Required value to earn badge
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user_badges = db.relationship('UserBadge', backref='badge', lazy=True)

    def __init__(self, name, description, category, criteria_type, criteria_value, icon=None, color='primary'):
        self.name = name
        self.description = description
        self.category = category
        self.criteria_type = criteria_type
        self.criteria_value = criteria_value
        self.icon = icon
        self.color = color

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'category': self.category,
            'criteria_type': self.criteria_type,
            'criteria_value': self.criteria_value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def get_active_badges():
        """Get all active badges."""
        return Badge.query.filter_by(is_active=True).all()

    @staticmethod
    def get_badges_by_category(category):
        """Get badges by category."""
        return Badge.query.filter_by(category=category, is_active=True).all()

    @staticmethod
    def create_default_badges():
        """Create default badges for the system."""
        default_badges = [
            # Mood tracking badges
            Badge('First Mood', 'Logged your first mood entry', 'mood', 'count', 1, 'fas fa-smile', 'success'),
            Badge('Mood Tracker', 'Logged mood for 7 consecutive days', 'mood', 'streak', 7, 'fas fa-calendar-check', 'info'),
            Badge('Mood Master', 'Logged mood for 30 consecutive days', 'mood', 'streak', 30, 'fas fa-crown', 'warning'),
            Badge('Mood Explorer', 'Logged 50 different mood entries', 'mood', 'count', 50, 'fas fa-search', 'primary'),

            # Journal badges
            Badge('First Entry', 'Wrote your first journal entry', 'journal', 'count', 1, 'fas fa-pen', 'success'),
            Badge('Reflective', 'Wrote 10 journal entries', 'journal', 'count', 10, 'fas fa-book', 'info'),
            Badge('Storyteller', 'Wrote 50 journal entries', 'journal', 'count', 50, 'fas fa-scroll', 'warning'),
            Badge('Mood Improver', 'Journal entries show consistent mood improvement', 'journal', 'milestone', 5, 'fas fa-chart-line', 'success'),

            # Chat badges
            Badge('First Chat', 'Started your first conversation', 'chat', 'count', 1, 'fas fa-comments', 'success'),
            Badge('Active Listener', 'Had 25 conversations', 'chat', 'count', 25, 'fas fa-ear-listen', 'info'),
            Badge('Chat Champion', 'Had 100 conversations', 'chat', 'count', 100, 'fas fa-trophy', 'warning'),

            # Study badges
            Badge('Study Starter', 'Completed first study session', 'study', 'count', 1, 'fas fa-graduation-cap', 'success'),
            Badge('Focused Learner', 'Completed 10 study sessions', 'study', 'count', 10, 'fas fa-brain', 'info'),
            Badge('Study Master', 'Completed 50 study sessions', 'study', 'count', 50, 'fas fa-award', 'warning'),
            Badge('Marathon Student', 'Studied for 10 hours total', 'study', 'time', 600, 'fas fa-clock', 'primary'),

            # Wellness badges
            Badge('Wellness Beginner', 'Completed first micro-plan', 'wellness', 'count', 1, 'fas fa-seedling', 'success'),
            Badge('Wellness Explorer', 'Completed 5 micro-plans', 'wellness', 'count', 5, 'fas fa-tree', 'info'),
            Badge('Wellness Champion', 'Completed 20 micro-plans', 'wellness', 'count', 20, 'fas fa-mountain', 'warning'),

            # Streak badges
            Badge('Week Warrior', '7-day streak in any activity', 'streak', 'streak', 7, 'fas fa-fire', 'danger'),
            Badge('Month Master', '30-day streak in any activity', 'streak', 'streak', 30, 'fas fa-star', 'warning'),
            Badge('Consistency King', '100-day streak in any activity', 'streak', 'streak', 100, 'fas fa-crown', 'gold'),
        ]

        for badge in default_badges:
            existing = Badge.query.filter_by(name=badge.name).first()
            if not existing:
                db.session.add(badge)

        db.session.commit()
        return default_badges
