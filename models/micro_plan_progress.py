from . import db
from datetime import datetime
import json

class MicroPlanProgress(db.Model):
    __tablename__ = 'micro_plan_progress'

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), db.ForeignKey('user_sessions.session_id'), nullable=False)
    plan_id = db.Column(db.String(50), nullable=False)  # e.g., 'exam_stress_sos', 'sleep_reset', 'anxiety_grounding'
    enrolled_date = db.Column(db.DateTime, default=datetime.utcnow)
    current_day = db.Column(db.Integer, default=1)
    completed_tasks = db.Column(db.Text, default='{}')  # JSON: {"day": [task_ids]}
    is_completed = db.Column(db.Boolean, default=False)
    completion_date = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<MicroPlanProgress {self.session_id} - {self.plan_id} Day {self.current_day}>'

    def mark_task_complete(self, day, task_id):
        """Mark a specific task as completed for a given day."""
        completed = json.loads(self.completed_tasks)
        if str(day) not in completed:
            completed[str(day)] = []

        if task_id not in completed[str(day)]:
            completed[str(day)].append(task_id)
            self.completed_tasks = json.dumps(completed)
            return True
        return False

    def is_task_completed(self, day, task_id):
        """Check if a specific task is completed."""
        completed = json.loads(self.completed_tasks)
        day_str = str(day)
        return day_str in completed and task_id in completed[day_str]

    def get_completed_tasks_for_day(self, day):
        """Get list of completed task IDs for a specific day."""
        completed = json.loads(self.completed_tasks)
        day_str = str(day)
        return completed.get(day_str, [])

    def advance_day(self):
        """Move to the next day if all tasks for current day are completed."""
        # This would need plan data to check completion
        # For now, just increment (logic will be in service)
        self.current_day += 1

    def complete_plan(self):
        """Mark the entire plan as completed."""
        self.is_completed = True
        self.completion_date = datetime.utcnow()

    @staticmethod
    def get_user_progress(session_id, plan_id):
        """Get progress for a specific user and plan."""
        return MicroPlanProgress.query.filter_by(
            session_id=session_id,
            plan_id=plan_id
        ).first()

    @staticmethod
    def enroll_user(session_id, plan_id):
        """Enroll a user in a micro-plan."""
        existing = MicroPlanProgress.get_user_progress(session_id, plan_id)
        if existing:
            return existing

        progress = MicroPlanProgress(
            session_id=session_id,
            plan_id=plan_id
        )
        db.session.add(progress)
        db.session.commit()
        return progress
