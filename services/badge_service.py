from models import Badge, UserBadge, db

class BadgeService:
    @staticmethod
    def create_badge(name, description, category, criteria_type, criteria_value, icon=None, color='primary'):
        """Create a new badge."""
        badge = Badge(name, description, category, criteria_type, criteria_value, icon, color)
        db.session.add(badge)
        db.session.commit()
        return badge

    @staticmethod
    def get_all_badges():
        """Get all active badges."""
        return Badge.get_active_badges()

    @staticmethod
    def get_badges_by_category(category):
        """Get badges by category."""
        return Badge.get_badges_by_category(category)

    @staticmethod
    def get_user_badges(session_id):
        """Get all badges earned by a user."""
        user_badges = UserBadge.get_user_badges(session_id)
        badges = []
        for user_badge in user_badges:
            badge_data = user_badge.badge.to_dict()
            badge_data['earned_at'] = user_badge.earned_at.isoformat() if user_badge.earned_at else None
            badges.append(badge_data)
        return badges

    @staticmethod
    def get_user_badge_progress(session_id):
        """Get user's progress towards all badges."""
        progress_data = UserBadge.get_user_badge_progress(session_id)
        badges = Badge.get_active_badges()

        result = []
        for badge in badges:
            badge_info = badge.to_dict()
            badge_progress = progress_data.get(badge.id, {'earned': False, 'progress': 0, 'percentage': 0})
            badge_info.update(badge_progress)
            result.append(badge_info)

        return result

    @staticmethod
    def check_and_award_badges(session_id):
        """Check for new badges and award them."""
        earned_badges = UserBadge.check_and_award_badges(session_id)
        return [badge.to_dict() for badge in earned_badges]

    @staticmethod
    def get_recently_earned_badges(session_id, days=7):
        """Get badges earned recently."""
        user_badges = UserBadge.get_recently_earned_badges(session_id, days)
        badges = []
        for user_badge in user_badges:
            badge_data = user_badge.badge.to_dict()
            badge_data['earned_at'] = user_badge.earned_at.isoformat() if user_badge.earned_at else None
            badges.append(badge_data)
        return badges

    @staticmethod
    def get_badge_stats(session_id):
        """Get badge statistics for a user."""
        user_badges = UserBadge.get_user_badges(session_id)
        all_badges = Badge.get_active_badges()

        earned_count = len(user_badges)
        total_count = len(all_badges)

        # Category breakdown
        category_stats = {}
        for user_badge in user_badges:
            category = user_badge.badge.category
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1

        # Recent badges (last 30 days)
        recent_badges = UserBadge.get_recently_earned_badges(session_id, 30)

        return {
            'total_badges': total_count,
            'earned_badges': earned_count,
            'completion_percentage': (earned_count / total_count * 100) if total_count > 0 else 0,
            'category_breakdown': category_stats,
            'recent_badges_count': len(recent_badges),
            'recent_badges': [badge.badge.name for badge in recent_badges]
        }

    @staticmethod
    def get_badge_by_id(badge_id):
        """Get a specific badge by ID."""
        return Badge.query.get(badge_id)

    @staticmethod
    def update_badge(badge_id, **kwargs):
        """Update a badge."""
        badge = Badge.query.get(badge_id)
        if not badge:
            return None

        for key, value in kwargs.items():
            if hasattr(badge, key):
                setattr(badge, key, value)

        db.session.commit()
        return badge

    @staticmethod
    def delete_badge(badge_id):
        """Delete a badge."""
        badge = Badge.query.get(badge_id)
        if badge:
            db.session.delete(badge)
            db.session.commit()
            return True
        return False

    @staticmethod
    def initialize_default_badges():
        """Initialize default badges in the system."""
        return Badge.create_default_badges()

    @staticmethod
    def get_leaderboard_badges(limit=10):
        """Get most earned badges across all users."""
        # This would require aggregating user badges across sessions
        # For now, return all badges with their earn counts
        badges = Badge.get_active_badges()
        badge_stats = []

        for badge in badges:
            earned_count = UserBadge.query.filter_by(badge_id=badge.id, is_earned=True).count()
            badge_stats.append({
                'badge': badge.to_dict(),
                'earned_count': earned_count
            })

        # Sort by earned count
        badge_stats.sort(key=lambda x: x['earned_count'], reverse=True)
        return badge_stats[:limit]

    @staticmethod
    def get_popular_badges():
        """Get most popular badges."""
        return BadgeService.get_leaderboard_badges(5)

    @staticmethod
    def get_rare_badges():
        """Get rarest badges (least earned)."""
        badges = Badge.get_active_badges()
        badge_stats = []

        for badge in badges:
            earned_count = UserBadge.query.filter_by(badge_id=badge.id, is_earned=True).count()
            badge_stats.append({
                'badge': badge.to_dict(),
                'earned_count': earned_count
            })

        # Sort by earned count (ascending)
        badge_stats.sort(key=lambda x: x['earned_count'])
        return badge_stats[:5]
