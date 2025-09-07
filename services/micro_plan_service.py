import json
import os
from datetime import datetime, timedelta
from models import db, MicroPlanProgress

class MicroPlanService:
    def __init__(self):
        self.plans_data = self._load_plans_data()

    def _load_plans_data(self):
        """Load micro-plans data from JSON file."""
        plans_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'micro_plans.json')
        with open(plans_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_available_plans(self, persona=None):
        """Get all available micro-plans, optionally filtered by persona."""
        if persona:
            return {k: v for k, v in self.plans_data.items() if v.get('target_audience') == persona}
        return self.plans_data

    def get_plan_details(self, plan_id):
        """Get detailed information about a specific plan."""
        return self.plans_data.get(plan_id)

    def enroll_user(self, session_id, plan_id):
        """Enroll a user in a micro-plan."""
        if plan_id not in self.plans_data:
            raise ValueError(f"Plan {plan_id} not found")

        return MicroPlanProgress.enroll_user(session_id, plan_id)

    def get_user_progress(self, session_id, plan_id):
        """Get user's progress in a specific plan."""
        progress = MicroPlanProgress.get_user_progress(session_id, plan_id)
        if not progress:
            return None

        plan_data = self.get_plan_details(plan_id)
        if not plan_data:
            return None

        # Calculate completion percentage
        total_tasks = sum(len(day_data.get('tasks', [])) for day_data in plan_data['days'].values())
        completed_tasks = sum(len(progress.get_completed_tasks_for_day(day)) for day in range(1, progress.current_day + 1))

        return {
            'progress': progress,
            'plan_data': plan_data,
            'completion_percentage': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            'current_day_data': plan_data['days'].get(str(progress.current_day)),
            'is_plan_complete': progress.is_completed
        }

    def mark_task_complete(self, session_id, plan_id, day, task_id):
        """Mark a task as completed."""
        progress = MicroPlanProgress.get_user_progress(session_id, plan_id)
        if not progress:
            raise ValueError("User not enrolled in this plan")

        if progress.is_completed:
            raise ValueError("Plan already completed")

        # Validate day and task
        plan_data = self.get_plan_details(plan_id)
        if str(day) not in plan_data['days']:
            raise ValueError(f"Invalid day {day} for plan {plan_id}")

        day_tasks = plan_data['days'][str(day)]['tasks']
        task_ids = [task['id'] for task in day_tasks]
        if task_id not in task_ids:
            raise ValueError(f"Invalid task {task_id} for day {day}")

        # Mark task complete
        if progress.mark_task_complete(day, task_id):
            db.session.commit()

            # Check if day is complete and advance if needed
            completed_tasks = progress.get_completed_tasks_for_day(day)
            if len(completed_tasks) == len(task_ids) and day == progress.current_day:
                progress.advance_day()
                db.session.commit()

                # Check if plan is complete
                if progress.current_day > plan_data['duration_days']:
                    progress.complete_plan()
                    db.session.commit()

            return True
        return False

    def get_user_active_plans(self, session_id):
        """Get all active (not completed) plans for a user."""
        active_plans = MicroPlanProgress.query.filter_by(
            session_id=session_id,
            is_completed=False
        ).all()

        result = []
        for progress in active_plans:
            plan_data = self.get_plan_details(progress.plan_id)
            if plan_data:
                result.append({
                    'progress': progress,
                    'plan_data': plan_data,
                    'current_day_title': plan_data['days'].get(str(progress.current_day), {}).get('title', 'Unknown')
                })

        return result

    def get_user_completed_plans(self, session_id):
        """Get all completed plans for a user."""
        completed_plans = MicroPlanProgress.query.filter_by(
            session_id=session_id,
            is_completed=True
        ).all()

        result = []
        for progress in completed_plans:
            plan_data = self.get_plan_details(progress.plan_id)
            if plan_data:
                result.append({
                    'progress': progress,
                    'plan_data': plan_data,
                    'days_taken': (progress.completion_date - progress.enrolled_date).days if progress.completion_date else None
                })

        return result

    def get_plan_streak_info(self, session_id, plan_id):
        """Get streak information for a plan (consecutive days with completed tasks)."""
        progress = MicroPlanProgress.get_user_progress(session_id, plan_id)
        if not progress:
            return {'current_streak': 0, 'longest_streak': 0}

        # Calculate streaks based on completed days
        completed = json.loads(progress.completed_tasks)
        current_streak = 0
        longest_streak = 0
        temp_streak = 0

        for day in range(1, progress.current_day + 1):
            day_str = str(day)
            if day_str in completed and len(completed[day_str]) > 0:
                temp_streak += 1
                current_streak = temp_streak
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 0

        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak
        }
