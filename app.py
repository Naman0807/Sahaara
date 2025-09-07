from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_session import Session
import uuid
from datetime import datetime, timedelta

from config import Config
from models import db, UserSession, Conversation, CrisisLog
from services.gemini_service import GeminiService
from services.language_service import LanguageService
from services.wellness_tracker import WellnessTracker
from services.helpline_service import HelplineService
from services.micro_plan_service import MicroPlanService
from services.myths_facts_service import MythsFactsService
from services.journal_service import JournalService
from services.badge_service import BadgeService
from services.study_timer_service import StudyTimerService

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    Session(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Helper function to get or create session
    def get_or_create_session():
        if 'session_id' not in session:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            user_session = UserSession(session_id=session_id)
            db.session.add(user_session)
            db.session.commit()
        else:
            session_id = session['session_id']
            user_session = UserSession.query.filter_by(session_id=session_id).first()
            if not user_session:
                user_session = UserSession(session_id=session_id)
                db.session.add(user_session)
                db.session.commit()
            user_session.update_activity()
            db.session.commit()
        return session_id

    @app.route('/')
    def index():
        get_or_create_session()
        return render_template('index.html')

    @app.route('/chat')
    def chat():
        session_id = get_or_create_session()
        user_session = UserSession.query.filter_by(session_id=session_id).first()
        persona = user_session.persona if user_session else None
        language = user_session.language if user_session else 'en'
        return render_template('chat.html', persona=persona, language=language)

    @app.route('/api/chat', methods=['POST'])
    def api_chat():
        session_id = get_or_create_session()
        user_session = UserSession.query.filter_by(session_id=session_id).first()
        data = request.get_json()
        user_message = data.get('message', '')
        language = data.get('language', user_session.language if user_session else 'en')

        # Auto-detect language if not specified or if message contains mixed content
        if not language or language == 'auto':
            detected_lang = LanguageService.detect_language(user_message)
            if detected_lang in ['hi', 'hinglish']:
                language = detected_lang
            else:
                language = 'en'

        # Update user session
        if user_session:
            user_session.language = language
            db.session.commit()

        # Get conversation history
        conversations = Conversation.query.filter_by(session_id=session_id).order_by(Conversation.timestamp.desc()).limit(10).all()
        history = [f"User: {c.message}\nAI: {c.response}" for c in reversed(conversations)]

        # Detect crisis
        crisis_keywords = app.config['CRISIS_KEYWORDS']
        detected = CrisisLog.detect_crisis(user_message, crisis_keywords)
        crisis_detected = len(detected) > 0

        if crisis_detected:
            HelplineService.escalate_crisis(session_id, detected)
            response_text = "I'm concerned about what you've shared. Please contact a helpline immediately. " + str(app.config['HELPLINES'])
        else:
            gemini = GeminiService()
            persona = user_session.persona if user_session else 'general'
            response_text = gemini.generate_response(user_message, persona, language, history)

        # Save conversation
        conv = Conversation(session_id=session_id, message=user_message, response=response_text, language=language, crisis_detected=crisis_detected)
        db.session.add(conv)
        db.session.commit()

        return jsonify({'response': response_text, 'crisis': crisis_detected, 'detected_language': language})

    @app.route('/resources/<persona>')
    def resources(persona):
        get_or_create_session()
        # Load resources based on persona
        # For now, placeholder
        return render_template('resources.html', persona=persona)

    @app.route('/track')
    def track():
        session_id = get_or_create_session()
        mood_history = WellnessTracker.get_mood_history(session_id)
        return render_template('track.html', mood_history=mood_history)

    @app.route('/api/mood', methods=['POST'])
    def api_mood():
        session_id = get_or_create_session()
        data = request.get_json()
        mood = data.get('mood', 5)
        WellnessTracker.log_mood(session_id, mood)
        return jsonify({'success': True})

    @app.route('/crisis')
    def crisis():
        get_or_create_session()
        helplines = HelplineService.get_helplines()
        return render_template('crisis.html', helplines=helplines)

    @app.route('/gatekeeper')
    def gatekeeper():
        # In a real app, check authentication
        crisis_logs = HelplineService.get_crisis_logs()
        # Aggregate anonymized data
        total_crises = len(crisis_logs)
        escalated = sum(1 for log in crisis_logs if log['escalated'])
        return render_template('gatekeeper.html', total_crises=total_crises, escalated=escalated)

    @app.route('/set_persona', methods=['POST'])
    def set_persona():
        session_id = get_or_create_session()
        data = request.get_json()
        persona = data.get('persona')
        user_session = UserSession.query.filter_by(session_id=session_id).first()
        if user_session:
            user_session.persona = persona
            db.session.commit()
        return jsonify({'success': True})

    @app.route('/micro-plans')
    def micro_plans():
        session_id = get_or_create_session()
        user_session = UserSession.query.filter_by(session_id=session_id).first()
        persona = user_session.persona if user_session else None

        micro_plan_svc = MicroPlanService()
        available_plans = micro_plan_svc.get_available_plans(persona)
        active_plans = micro_plan_svc.get_user_active_plans(session_id)
        completed_plans = micro_plan_svc.get_user_completed_plans(session_id)

        return render_template('micro_plans.html',
                             available_plans=available_plans,
                             active_plans=active_plans,
                             completed_plans=completed_plans)

    @app.route('/api/micro-plans/enroll', methods=['POST'])
    def enroll_micro_plan():
        session_id = get_or_create_session()
        data = request.get_json()
        plan_id = data.get('plan_id')

        if not plan_id:
            return jsonify({'success': False, 'error': 'Plan ID required'}), 400

        try:
            micro_plan_svc = MicroPlanService()
            progress = micro_plan_svc.enroll_user(session_id, plan_id)
            return jsonify({'success': True, 'progress_id': progress.id})
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400

    @app.route('/api/micro-plans/progress/<plan_id>')
    def get_micro_plan_progress(plan_id):
        session_id = get_or_create_session()

        micro_plan_svc = MicroPlanService()
        progress_data = micro_plan_svc.get_user_progress(session_id, plan_id)

        if not progress_data:
            return jsonify({'success': False, 'error': 'Not enrolled in this plan'}), 404

        return jsonify({
            'success': True,
            'progress': {
                'current_day': progress_data['progress'].current_day,
                'is_completed': progress_data['progress'].is_completed,
                'completion_percentage': progress_data['completion_percentage']
            },
            'plan': progress_data['plan_data'],
            'current_day_data': progress_data['current_day_data']
        })

    @app.route('/api/micro-plans/task/complete', methods=['POST'])
    def complete_micro_plan_task():
        session_id = get_or_create_session()
        data = request.get_json()
        plan_id = data.get('plan_id')
        day = data.get('day')
        task_id = data.get('task_id')

        if not all([plan_id, day, task_id]):
            return jsonify({'success': False, 'error': 'Missing required parameters'}), 400

        try:
            micro_plan_svc = MicroPlanService()
            success = micro_plan_svc.mark_task_complete(session_id, plan_id, int(day), task_id)
            return jsonify({'success': success})
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400

    @app.route('/api/mood/reminder/check')
    def check_mood_reminder():
        session_id = get_or_create_session()
        should_remind = WellnessTracker.should_send_mood_reminder(session_id)

        if should_remind:
            WellnessTracker.mark_mood_reminder_sent(session_id)
            return jsonify({
                'should_remind': True,
                'message': 'How are you feeling today? Take a moment to log your mood.',
                'type': 'mood_reminder'
            })

        return jsonify({'should_remind': False})

    @app.route('/api/mood/streak')
    def get_mood_streak():
        session_id = get_or_create_session()
        streak = WellnessTracker.get_mood_streak(session_id)
        return jsonify({'streak': streak})

    @app.route('/api/mood/weekly-summary')
    def get_weekly_mood_summary():
        session_id = get_or_create_session()
        summary = WellnessTracker.get_weekly_mood_summary(session_id)
        return jsonify({'summary': summary})

    @app.route('/api/nudges/pending')
    def get_pending_nudges():
        session_id = get_or_create_session()
        pending_nudges = WellnessTracker.get_pending_nudges(session_id)

        # Mark nudges as sent
        for nudge in pending_nudges:
            WellnessTracker.mark_nudge_sent(session_id, nudge['id'])

        return jsonify({'nudges': pending_nudges})

    @app.route('/api/nudges/schedule', methods=['POST'])
    def schedule_nudge():
        session_id = get_or_create_session()
        data = request.get_json()
        nudge_type = data.get('type')
        scheduled_time_str = data.get('scheduled_time')

        if not nudge_type:
            return jsonify({'success': False, 'error': 'Nudge type required'}), 400

        scheduled_time = None
        if scheduled_time_str:
            try:
                scheduled_time = datetime.fromisoformat(scheduled_time_str.replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid scheduled time format'}), 400

        success = WellnessTracker.schedule_nudge(session_id, nudge_type, scheduled_time)
        return jsonify({'success': success})

    @app.route('/myths-facts')
    def myths_facts():
        get_or_create_session()
        return render_template('myths_facts.html')

    @app.route('/api/myths-facts')
    def get_myths_facts():
        category = request.args.get('category')
        language = request.args.get('language', 'en')
        limit = int(request.args.get('limit', 10))

        myths_facts = MythsFactsService.get_myths_facts(category=category, language=language, limit=limit)
        return jsonify({'myths_facts': myths_facts})

    @app.route('/api/myths-facts/random')
    def get_random_myth_fact():
        language = request.args.get('language', 'en')
        myth_fact = MythsFactsService.get_random_myth_fact(language=language)

        if myth_fact:
            return jsonify({'myth_fact': myth_fact})
        return jsonify({'error': 'No myths/facts found'}), 404

    @app.route('/api/myths-facts/search')
    def search_myths_facts():
        query = request.args.get('q', '')
        language = request.args.get('language', 'en')

        if not query:
            return jsonify({'error': 'Search query required'}), 400

        results = MythsFactsService.search_myths_facts(query=query, language=language)
        return jsonify({'results': results, 'query': query})

    @app.route('/api/myths-facts/categories')
    def get_myths_facts_categories():
        categories = MythsFactsService.get_categories()
        return jsonify({'categories': categories})

    @app.route('/api/myths-facts/popular')
    def get_popular_myths():
        language = request.args.get('language', 'en')
        popular_myths = MythsFactsService.get_popular_myths(language=language)
        return jsonify({'popular_myths': popular_myths})

    # Journal routes
    @app.route('/journal')
    def journal():
        get_or_create_session()
        return render_template('journal.html')

    @app.route('/api/journal/entries', methods=['GET'])
    def get_journal_entries():
        session_id = get_or_create_session()
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))
        decrypt = request.args.get('decrypt', 'true').lower() == 'true'

        entries = JournalService.get_entries(session_id, limit, offset, decrypt)
        return jsonify({'entries': [entry.to_dict() for entry in entries]})

    @app.route('/api/journal/entry', methods=['POST'])
    def create_journal_entry():
        session_id = get_or_create_session()
        data = request.get_json()

        entry = JournalService.create_entry(
            session_id=session_id,
            content=data.get('content', ''),
            title=data.get('title'),
            mood_before=data.get('mood_before'),
            mood_after=data.get('mood_after'),
            tags=data.get('tags'),
            encrypt=data.get('encrypt', True)
        )

        # Check for badges
        BadgeService.check_and_award_badges(session_id)

        return jsonify({'success': True, 'entry': entry.to_dict()})

    @app.route('/api/journal/entry/<entry_id>', methods=['GET'])
    def get_journal_entry(entry_id):
        session_id = get_or_create_session()
        decrypt = request.args.get('decrypt', 'true').lower() == 'true'

        entry = JournalService.get_entry_by_id(entry_id, session_id, decrypt)
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404

        return jsonify({'entry': entry.to_dict()})

    @app.route('/api/journal/entry/<entry_id>', methods=['PUT'])
    def update_journal_entry(entry_id):
        session_id = get_or_create_session()
        data = request.get_json()

        entry = JournalService.update_entry(
            entry_id=entry_id,
            session_id=session_id,
            content=data.get('content'),
            title=data.get('title'),
            mood_before=data.get('mood_before'),
            mood_after=data.get('mood_after'),
            tags=data.get('tags')
        )

        if not entry:
            return jsonify({'error': 'Entry not found'}), 404

        return jsonify({'success': True, 'entry': entry.to_dict()})

    @app.route('/api/journal/entry/<entry_id>', methods=['DELETE'])
    def delete_journal_entry(entry_id):
        session_id = get_or_create_session()

        success = JournalService.delete_entry(entry_id, session_id)
        if not success:
            return jsonify({'error': 'Entry not found'}), 404

        return jsonify({'success': True})

    @app.route('/api/journal/search')
    def search_journal_entries():
        session_id = get_or_create_session()
        query = request.args.get('q', '')
        decrypt = request.args.get('decrypt', 'true').lower() == 'true'

        if not query:
            return jsonify({'error': 'Search query required'}), 400

        entries = JournalService.search_entries(session_id, query, decrypt)
        return jsonify({'entries': [entry.to_dict() for entry in entries]})

    @app.route('/api/journal/stats')
    def get_journal_stats():
        session_id = get_or_create_session()
        days = int(request.args.get('days', 30))

        stats = JournalService.get_journal_stats(session_id, days)
        return jsonify({'stats': stats})

    # Badge routes
    @app.route('/api/badges')
    def get_user_badges():
        session_id = get_or_create_session()

        badges = BadgeService.get_user_badges(session_id)
        return jsonify({'badges': badges})

    @app.route('/api/badges/progress')
    def get_badge_progress():
        session_id = get_or_create_session()

        progress = BadgeService.get_user_badge_progress(session_id)
        return jsonify({'progress': progress})

    @app.route('/api/badges/check')
    def check_badges():
        session_id = get_or_create_session()

        earned_badges = BadgeService.check_and_award_badges(session_id)
        return jsonify({'earned_badges': earned_badges})

    @app.route('/api/badges/stats')
    def get_badge_stats():
        session_id = get_or_create_session()

        stats = BadgeService.get_badge_stats(session_id)
        return jsonify({'stats': stats})

    # Study Timer routes
    @app.route('/study_timer')
    def study_timer():
        get_or_create_session()
        return render_template('study_timer.html')

    @app.route('/api/study/start', methods=['POST'])
    def start_study_session():
        session_id = get_or_create_session()
        data = request.get_json()

        session, message = StudyTimerService.start_session(
            session_id=session_id,
            subject=data.get('subject'),
            mood_before=data.get('mood_before')
        )

        if not session:
            return jsonify({'success': False, 'error': message}), 400

        # Check for badges
        BadgeService.check_and_award_badges(session_id)

        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'message': message
        })

    @app.route('/api/study/stop', methods=['POST'])
    def stop_study_session():
        session_id = get_or_create_session()
        data = request.get_json()

        session, message = StudyTimerService.stop_session(
            session_id=session_id,
            mood_after=data.get('mood_after'),
            productivity_rating=data.get('productivity_rating'),
            notes=data.get('notes')
        )

        if not session:
            return jsonify({'success': False, 'error': message}), 400

        # Check for badges
        BadgeService.check_and_award_badges(session_id)

        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'message': message
        })

    @app.route('/api/study/status')
    def get_study_status():
        session_id = get_or_create_session()

        status = StudyTimerService.get_session_status(session_id)
        return jsonify({'status': status})

    @app.route('/api/study/pause', methods=['POST'])
    def pause_study_session():
        session_id = get_or_create_session()

        session, message = StudyTimerService.pause_session(session_id)

        if not session:
            return jsonify({'success': False, 'error': message}), 400

        return jsonify({
            'success': True,
            'session': session.to_dict(),
            'message': message
        })

    @app.route('/api/study/sessions')
    def get_study_sessions():
        session_id = get_or_create_session()
        limit = int(request.args.get('limit', 20))
        offset = int(request.args.get('offset', 0))

        sessions = StudyTimerService.get_user_sessions(session_id, limit, offset)
        return jsonify({'sessions': [session.to_dict() for session in sessions]})

    @app.route('/api/study/stats')
    def get_study_stats():
        session_id = get_or_create_session()
        days = int(request.args.get('days', 30))

        stats = StudyTimerService.get_study_stats(session_id, days)
        return jsonify({'stats': stats})

    @app.route('/api/study/insights')
    def get_study_insights():
        session_id = get_or_create_session()

        insights = StudyTimerService.get_productivity_insights(session_id)
        goals = StudyTimerService.get_study_goals(session_id)

        return jsonify({
            'insights': insights,
            'goals': goals
        })

    @app.route('/api/study/goals')
    def get_study_goals_api():
        session_id = get_or_create_session()

        goals = StudyTimerService.get_study_goals(session_id)
        return jsonify({'goals': goals})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
