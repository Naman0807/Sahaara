from flask import current_app
from models import CrisisLog, db
import json
from datetime import datetime

class HelplineService:
    @staticmethod
    def get_helplines(region=None):
        """Get helplines, optionally filtered by region."""
        helplines = current_app.config['HELPLINES']

        if region:
            # Filter helplines by region if specified
            regional_helplines = {}
            for key, value in helplines.items():
                if region.lower() in key.lower():
                    regional_helplines[key] = value
            return regional_helplines if regional_helplines else helplines

        return helplines

    @staticmethod
    def get_regional_helplines():
        """Get helplines organized by region."""
        helplines = current_app.config['HELPLINES']
        regional = {
            'national': {},
            'delhi': {},
            'mumbai': {},
            'chennai': {},
            'kolkata': {},
            'bangalore': {},
            'pune': {},
            'hyderabad': {},
            'ahmedabad': {},
            'jaipur': {},
            'lucknow': {},
            'chandigarh': {},
            'other': {}
        }

        for key, value in helplines.items():
            key_lower = key.lower()
            if 'national' in key_lower or 'cooj' in key_lower:
                regional['national'][key] = value
            elif 'delhi' in key_lower or 'ncr' in key_lower:
                regional['delhi'][key] = value
            elif 'mumbai' in key_lower or 'maharashtra' in key_lower:
                regional['mumbai'][key] = value
            elif 'chennai' in key_lower or 'tamil' in key_lower or 'sneha' in key_lower:
                regional['chennai'][key] = value
            elif 'kolkata' in key_lower or 'west bengal' in key_lower:
                regional['kolkata'][key] = value
            elif 'bangalore' in key_lower or 'karnataka' in key_lower:
                regional['bangalore'][key] = value
            elif 'pune' in key_lower:
                regional['pune'][key] = value
            elif 'hyderabad' in key_lower or 'telangana' in key_lower:
                regional['hyderabad'][key] = value
            elif 'ahmedabad' in key_lower or 'gujarat' in key_lower:
                regional['ahmedabad'][key] = value
            elif 'jaipur' in key_lower or 'rajasthan' in key_lower:
                regional['jaipur'][key] = value
            elif 'lucknow' in key_lower or 'uttar pradesh' in key_lower:
                regional['lucknow'][key] = value
            elif 'chandigarh' in key_lower or 'punjab' in key_lower:
                regional['chandigarh'][key] = value
            else:
                regional['other'][key] = value

        # Remove empty regions
        return {k: v for k, v in regional.items() if v}

    @staticmethod
    def escalate_crisis(session_id, keywords, user_location=None):
        """Escalate crisis with enhanced logging and regional helpline selection."""
        log = CrisisLog(session_id=session_id, detected_keywords=str(keywords))
        log.escalated = True

        # Determine appropriate helpline based on location or keywords
        helpline_contacted = HelplineService._determine_helpline(user_location, keywords)

        log.helpline_contacted = helpline_contacted

        # In a real app, this would:
        # 1. Send SMS/email alert to helpline
        # 2. Log to external crisis management system
        # 3. Send immediate response to user
        # 4. Notify emergency contacts if available

        # For now, just log the escalation
        print(f"CRISIS ESCALATION: Session {session_id} - Keywords: {keywords} - Helpline: {helpline_contacted}")

        db.session.add(log)
        db.session.commit()
        return log

    @staticmethod
    def _determine_helpline(user_location, keywords):
        """Determine which helpline to contact based on location and crisis type."""
        # Default to national helpline
        helpline = 'national'

        if user_location:
            location_lower = user_location.lower()
            if 'delhi' in location_lower or 'ncr' in location_lower:
                helpline = 'vandrevala'
            elif 'mumbai' in location_lower or 'maharashtra' in location_lower:
                helpline = 'national'  # Could add Mumbai-specific helpline
            elif 'chennai' in location_lower or 'tamil' in location_lower:
                helpline = 'sneha'
            # Add more location-based logic as needed

        # Check if it's a specific type of crisis that needs specialized helpline
        keywords_str = str(keywords).lower()
        if 'student' in keywords_str or 'exam' in keywords_str:
            helpline = 'student_helpline'  # Could be specialized
        elif 'domestic' in keywords_str or 'abuse' in keywords_str:
            helpline = 'women_helpline'  # Could be specialized

        return helpline

    @staticmethod
    def get_crisis_logs(limit=50):
        """Get anonymized crisis logs for gatekeeper/monitoring."""
        logs = CrisisLog.query.order_by(CrisisLog.timestamp.desc()).limit(limit).all()
        anonymized = []
        for log in logs:
            anonymized.append({
                'timestamp': log.timestamp.isoformat(),
                'keywords': log.detected_keywords,
                'escalated': log.escalated,
                'helpline_contacted': log.helpline_contacted,
                'session_id': log.session_id[:8] + '...'  # Partial anonymization
            })
        return anonymized

    @staticmethod
    def get_crisis_stats(days=30):
        """Get crisis statistics for monitoring."""
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        logs = CrisisLog.query.filter(CrisisLog.timestamp >= cutoff_date).all()

        total_crises = len(logs)
        escalated = sum(1 for log in logs if log.escalated)
        unique_sessions = len(set(log.session_id for log in logs))

        # Group by helpline
        helpline_stats = {}
        for log in logs:
            helpline = log.helpline_contacted or 'unknown'
            if helpline not in helpline_stats:
                helpline_stats[helpline] = 0
            helpline_stats[helpline] += 1

        return {
            'total_crises': total_crises,
            'escalated': escalated,
            'unique_sessions': unique_sessions,
            'escalation_rate': (escalated / total_crises * 100) if total_crises > 0 else 0,
            'helpline_distribution': helpline_stats,
            'period_days': days
        }

    @staticmethod
    def get_emergency_resources():
        """Get emergency resources and coping strategies."""
        return {
            'immediate_actions': [
                'Call a helpline immediately',
                'Talk to someone you trust',
                'Remove means of self-harm if possible',
                'Practice deep breathing or grounding techniques',
                'Remember that this feeling will pass'
            ],
            'coping_strategies': [
                '5-4-3-2-1 grounding technique',
                'Cold water on face or ice cube hold',
                'Physical activity or walk',
                'Listen to calming music',
                'Write down your thoughts'
            ],
            'professional_help': [
                'Mental health professionals',
                'Crisis helplines',
                'Emergency services if in immediate danger',
                'Support groups and online communities'
            ]
        }
