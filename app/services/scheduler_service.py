import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from app.models.models import Task, SessionLocal
from app.services.mnotify_service import MnotifyService


class TaskScheduler:
    """Service for scheduling task reminders and notifications"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.mnotify_service = MnotifyService()
        self.scheduler.start()
    
    def schedule_task_reminders(self, task: Task):
        """
        Schedule SMS reminder and voice call for a task
        
        Args:
            task (Task): Task object to schedule reminders for
        """
        # Schedule SMS reminder 15 minutes before task time
        reminder_time = task.scheduled_time - timedelta(minutes=15)
        
        # Only schedule if reminder time is in the future
        if reminder_time > datetime.now():
            self.scheduler.add_job(
                func=self._send_sms_reminder,
                trigger=DateTrigger(run_date=reminder_time),
                args=[task.id],
                id=f"sms_reminder_{task.id}",
                replace_existing=True
            )
        
        # Schedule voice call at task time
        if task.scheduled_time > datetime.now():
            self.scheduler.add_job(
                func=self._make_voice_call,
                trigger=DateTrigger(run_date=task.scheduled_time),
                args=[task.id],
                id=f"voice_call_{task.id}",
                replace_existing=True
            )
        
        print(f"Scheduled reminders for task {task.id}: SMS at {reminder_time}, Call at {task.scheduled_time}")
    
    async def _send_sms_reminder(self, task_id: int):
        """
        Send SMS reminder for a task
        
        Args:
            task_id (int): ID of the task to remind about
        """
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task and not task.is_reminded and not task.is_completed:
                await self.mnotify_service.send_sms_reminder(
                    task.task_description,
                    task.scheduled_time.strftime('%Y-%m-%d %H:%M')
                )
                
                # Mark as reminded
                task.is_reminded = True
                db.commit()
                print(f"SMS reminder sent for task {task_id}")
            
        except Exception as e:
            print(f"Error sending SMS reminder for task {task_id}: {e}")
        finally:
            db.close()
    
    async def _make_voice_call(self, task_id: int):
        """
        Make voice call for a task
        
        Args:
            task_id (int): ID of the task to call about
        """
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task and not task.is_called and not task.is_completed:
                await self.mnotify_service.make_voice_call(task.task_description)
                
                # Mark as called
                task.is_called = True
                db.commit()
                print(f"Voice call made for task {task_id}")
            
        except Exception as e:
            print(f"Error making voice call for task {task_id}: {e}")
        finally:
            db.close()
    
    def cancel_task_reminders(self, task_id: int):
        """
        Cancel scheduled reminders for a task
        
        Args:
            task_id (int): ID of the task to cancel reminders for
        """
        try:
            # Cancel SMS reminder
            if self.scheduler.get_job(f"sms_reminder_{task_id}"):
                self.scheduler.remove_job(f"sms_reminder_{task_id}")
            
            # Cancel voice call
            if self.scheduler.get_job(f"voice_call_{task_id}"):
                self.scheduler.remove_job(f"voice_call_{task_id}")
                
            print(f"Cancelled reminders for task {task_id}")
            
        except Exception as e:
            print(f"Error cancelling reminders for task {task_id}: {e}")
    
    def reschedule_existing_tasks(self):
        """
        Reschedule reminders for existing tasks in the database
        This is useful when restarting the application
        """
        db = SessionLocal()
        try:
            # Get all pending tasks
            pending_tasks = db.query(Task).filter(
                Task.is_completed == False,
                Task.scheduled_time > datetime.now()
            ).all()
            
            for task in pending_tasks:
                self.schedule_task_reminders(task)
                
            print(f"Rescheduled {len(pending_tasks)} pending tasks")
            
        except Exception as e:
            print(f"Error rescheduling tasks: {e}")
        finally:
            db.close()
    
    def get_scheduled_jobs(self):
        """Get list of all scheduled jobs"""
        return self.scheduler.get_jobs()
    
    def schedule_daily_checkins(self, telegram_bot, user_id: str):
        """
        Schedule daily check-ins at specific times
        
        Args:
            telegram_bot: Telegram bot instance
            user_id: User ID to send check-ins to
        """
        try:
            # Morning check-in at 8:00 AM
            self.scheduler.add_job(
                func=self.send_daily_checkin,
                trigger="cron",
                hour=8,
                minute=0,
                args=[telegram_bot, user_id, "morning"],
                id="morning_checkin",
                replace_existing=True
            )
            
            # Afternoon check-in at 12:00 PM (noon)
            self.scheduler.add_job(
                func=self.send_daily_checkin,
                trigger="cron",
                hour=12,
                minute=0,
                args=[telegram_bot, user_id, "afternoon"],
                id="afternoon_checkin",
                replace_existing=True
            )
            
            # Evening check-in at 4:00 PM
            self.scheduler.add_job(
                func=self.send_daily_checkin,
                trigger="cron",
                hour=16,
                minute=0,
                args=[telegram_bot, user_id, "evening"],
                id="evening_checkin",
                replace_existing=True
            )
            
            # Night completion check at 9:00 PM
            self.scheduler.add_job(
                func=self.send_daily_checkin,
                trigger="cron",
                hour=21,
                minute=0,
                args=[telegram_bot, user_id, "night"],
                id="night_checkin",
                replace_existing=True
            )
            
            print("Daily check-ins scheduled: 8am, 12pm, 4pm, 9pm")
            
        except Exception as e:
            print(f"Error scheduling daily check-ins: {e}")
    
    async def send_daily_checkin(self, telegram_bot, user_id: str, time_of_day: str):
        """
        Send daily check-in message
        
        Args:
            telegram_bot: Telegram bot instance
            user_id: User ID to send to
            time_of_day: "morning", "afternoon", "evening", or "night"
        """
        try:
            from app.services.openai_service import OpenAIService
            openai_service = OpenAIService()
            
            db = SessionLocal()
            try:
                # Get today's tasks
                today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                today_end = today_start + timedelta(days=1)
                
                if time_of_day == "night":
                    # Night check: all tasks for today
                    tasks = db.query(Task).filter(
                        Task.user_id == user_id,
                        Task.scheduled_time >= today_start,
                        Task.scheduled_time < today_end
                    ).all()
                else:
                    # Other times: pending tasks for today and upcoming
                    tasks = db.query(Task).filter(
                        Task.user_id == user_id,
                        Task.is_completed == False,
                        Task.scheduled_time >= datetime.now() - timedelta(hours=1)  # Include recently due tasks
                    ).order_by(Task.scheduled_time).limit(10).all()
                
                # Generate AI summary
                summary = await openai_service.generate_daily_summary(tasks, time_of_day)
                
                # Send message via Telegram
                await telegram_bot.application.bot.send_message(
                    chat_id=int(user_id),
                    text=summary,
                    parse_mode='Markdown'
                )
                
                print(f"Daily {time_of_day} check-in sent to user {user_id}")
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error sending daily {time_of_day} check-in: {e}")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()