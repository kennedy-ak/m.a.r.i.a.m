import os
import asyncio
import tempfile
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from sqlalchemy.orm import Session
from app.models.models import Task, SessionLocal
from app.services.openai_service import OpenAIService
from app.services.scheduler_service import TaskScheduler
from app.services.mnotify_service import MnotifyService
from app.core.config import settings


class TelegramBot:
    """Telegram bot service for handling user interactions"""
    
    def __init__(self):
        self.token = settings.telegram_bot_token
        self.authorized_user_id = os.getenv("AUTHORIZED_USER_ID")
        self.openai_service = OpenAIService()
        self.scheduler = TaskScheduler()
        self.mnotify_service = MnotifyService()
        self.application = None
        
        # Initialize the application
        self.setup_bot()
    
    def setup_bot(self):
        """Setup the Telegram bot with handlers"""
        self.application = Application.builder().token(self.token).build()
        
        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("tasks", self.list_tasks))
        self.application.add_handler(CommandHandler("complete", self.complete_task))
        self.application.add_handler(CommandHandler("cancel", self.cancel_task))
        
        # Handle inline keyboard callbacks
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Handle voice messages
        self.application.add_handler(
            MessageHandler(filters.VOICE, self.handle_voice_message)
        )
        
        # Handle all text messages
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )
    
    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized"""
        return str(user_id) == self.authorized_user_id
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        print(f"Received /start from user {user_id}")
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("Sorry, you are not authorized to use this bot.")
            return
            
        welcome_message = """
🤖 Welcome to your Personal Assistant Bot!

I can help you manage your tasks with natural language. Here's what you can do:

📝 **Add tasks**: Just tell me what you need to do
   • "Remind me to call John at 4 PM"
   • "Finish report in 2 hours"
   • "Meeting tomorrow at 10 AM"

📋 **Query tasks**: Ask me about your tasks
   • "What do I have to do today?"
   • "Show me my pending tasks"
   • "What's next on my schedule?"

✅ **Complete tasks**: Mark tasks as done
   • `/complete <task_id>` - Mark a task as complete

❌ **Cancel tasks**: Remove tasks
   • `/cancel <task_id>` - Cancel a task

📱 **Reminders**: I'll send you:
   • SMS reminder 15 minutes before each task
   • Voice call when the task time arrives

Use `/help` for more information or just start typing your tasks!
        """
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user_id = update.effective_user.id
        print(f"Received /help from user {user_id}")
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("Sorry, you are not authorized to use this bot.")
            return
            
        help_message = """
🆘 **Help & Commands**

**Adding Tasks:**
Just type naturally what you want to do:
• "Call mom in 30 minutes"
• "Doctor appointment at 3 PM tomorrow"
• "Submit project by 5 PM"
• "Workout session in 1 hour"

**Querying Tasks:**
• "What's my schedule today?"
• "What tasks do I have?"
• "Show me tomorrow's tasks"
• "What's coming up next?"

**Commands:**
• `/start` - Welcome message and setup
• `/help` - Show this help message
• `/tasks` - List all your tasks with buttons
• `/complete <id>` - Mark task as complete
• `/cancel <id>` - Cancel a task

**Bulk Operations:**
• "cancel all tasks" - Remove all pending tasks
• "complete all tasks" - Mark all as done
• "show my tasks" - Display task list

**Voice Input:**
🎤 Send voice messages! I'll convert speech to text and process your request.
Just hold the microphone button and speak naturally.

**Time Examples:**
• "in 30 minutes" / "in 2 hours"
• "at 4 PM" / "at 14:30"
• "tomorrow at 9 AM"
• "next Monday at 10 AM"

If you don't specify a time, I'll default to 1 hour from now.

**Notifications:**
📱 SMS alert 15 minutes before each task
📞 Voice call when task time arrives
        """
        await update.message.reply_text(help_message)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle all text messages"""
        user_message = update.message.text
        user_id = str(update.effective_user.id)
        
        print(f"Received message from user {user_id}: {user_message}")
        
        if not self.is_authorized(int(user_id)):
            await update.message.reply_text("Sorry, you are not authorized to use this bot.")
            return
        
        await self.process_user_input(update, user_message, user_id)
    
    async def process_user_input(self, update: Update, user_message: str, user_id: str):
        """Process user input (from text or voice) and determine appropriate action"""
        user_lower = user_message.lower()
        
        # Handle explicit task management commands first
        if any(phrase in user_lower for phrase in ['cancel all', 'delete all', 'remove all']):
            await self.handle_bulk_cancel(update, user_id)
            return
        elif any(phrase in user_lower for phrase in ['complete all', 'mark all complete', 'finish all']):
            await self.handle_bulk_complete(update, user_id)
            return
        elif any(phrase in user_lower for phrase in ['show tasks', 'see tasks', 'list tasks', 'my tasks', 'view tasks']):
            await self.show_tasks_with_buttons(update, user_id)
            return
        
        # Handle task queries
        task_query_patterns = [
            'do i have', 'what tasks', 'any tasks', 'tasks today', 'tasks for', 
            'show me', 'list my', 'what do i', 'what are my', 'check my',
            'i want to know if i have', 'want to see', 'i want to see'
        ]
        
        if any(pattern in user_lower for pattern in task_query_patterns):
            await self.handle_task_query(update, user_message, user_id)
            return
        
        # Use AI to determine if this is a task creation request or general conversation
        is_task = await self.openai_service.is_task_request(user_message)
        
        if is_task:
            await self.handle_new_task(update, user_message, user_id)
        else:
            # Handle as general conversation
            await self.handle_conversation(update, user_message, user_id)
    
    async def handle_new_task(self, update: Update, user_message: str, user_id: str):
        """Handle new task creation"""
        try:
            # Send typing action
            await update.message.reply_text("🤔 Processing your task...")
            
            # Parse the task using OpenAI
            parsed_task = await self.openai_service.parse_task(user_message)
            
            # Save task to database
            db = SessionLocal()
            try:
                new_task = Task(
                    user_id=user_id,
                    task_description=parsed_task["task_description"],
                    original_input=user_message,
                    scheduled_time=parsed_task["scheduled_time"]
                )
                
                db.add(new_task)
                db.commit()
                db.refresh(new_task)
                
                # Schedule reminders
                self.scheduler.schedule_task_reminders(new_task)
                
                # Send SMS confirmation
                try:
                    sms_message = f"Task created: '{new_task.task_description}' scheduled for {new_task.scheduled_time.strftime('%m/%d at %H:%M')}. You'll get reminders via SMS and voice call."
                    await self.mnotify_service.send_sms_reminder(sms_message, new_task.scheduled_time.strftime('%Y-%m-%d %H:%M'))
                    sms_status = "✅ SMS confirmation sent"
                except Exception as e:
                    print(f"Error sending SMS confirmation: {e}")
                    sms_status = "❌ SMS confirmation failed"
                
                # Send Telegram confirmation
                response = f"""
✅ **Task Added Successfully!**

📝 **Task**: {new_task.task_description}
⏰ **Scheduled**: {new_task.scheduled_time.strftime('%Y-%m-%d at %H:%M')}
🆔 **Task ID**: {new_task.id}

📱 **Reminders scheduled:**
• SMS reminder 15 minutes before ({(new_task.scheduled_time - timedelta(minutes=15)).strftime('%H:%M')})
• Voice call at task time ({new_task.scheduled_time.strftime('%H:%M')})

📲 {sms_status}
                """
                
                await update.message.reply_text(response)
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error creating task: {e}")
            await update.message.reply_text(
                "❌ Sorry, I had trouble processing your task. Please try again or use the format: 'Task description at time'"
            )
    
    async def handle_task_query(self, update: Update, user_message: str, user_id: str):
        """Handle task queries"""
        try:
            db = SessionLocal()
            try:
                # Get user's tasks based on query context
                if 'today' in user_message.lower():
                    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    today_end = today_start + timedelta(days=1)
                    tasks = db.query(Task).filter(
                        Task.user_id == user_id,
                        Task.scheduled_time >= today_start,
                        Task.scheduled_time < today_end
                    ).order_by(Task.scheduled_time).all()
                elif 'tomorrow' in user_message.lower():
                    tomorrow_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                    tomorrow_end = tomorrow_start + timedelta(days=1)
                    tasks = db.query(Task).filter(
                        Task.user_id == user_id,
                        Task.scheduled_time >= tomorrow_start,
                        Task.scheduled_time < tomorrow_end
                    ).order_by(Task.scheduled_time).all()
                else:
                    # Get all pending tasks
                    tasks = db.query(Task).filter(
                        Task.user_id == user_id,
                        Task.is_completed == False,
                        Task.scheduled_time > datetime.now()
                    ).order_by(Task.scheduled_time).all()
                
                # Use OpenAI to format the response
                response = await self.openai_service.query_tasks(user_message, tasks)
                await update.message.reply_text(response)
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error querying tasks: {e}")
            await update.message.reply_text("❌ Sorry, I had trouble retrieving your tasks. Please try again.")
    
    async def list_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tasks command with interactive buttons"""
        user_id = str(update.effective_user.id)
        
        if not self.is_authorized(int(user_id)):
            await update.message.reply_text("Sorry, you are not authorized to use this bot.")
            return
        
        await self.show_tasks_with_buttons(update, user_id)
    
    async def complete_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /complete command"""
        if not context.args:
            await update.message.reply_text("❌ Please provide a task ID. Usage: `/complete <task_id>`")
            return
        
        try:
            task_id = int(context.args[0])
            user_id = str(update.effective_user.id)
            
            db = SessionLocal()
            try:
                task = db.query(Task).filter(
                    Task.id == task_id,
                    Task.user_id == user_id
                ).first()
                
                if not task:
                    await update.message.reply_text("❌ Task not found or doesn't belong to you.")
                    return
                
                # Mark task as completed
                task.is_completed = True
                db.commit()
                
                # Cancel scheduled reminders
                self.scheduler.cancel_task_reminders(task_id)
                
                await update.message.reply_text(
                    f"✅ Task completed: **{task.task_description}**\n"
                    f"🎉 Great job! Reminders have been cancelled."
                )
                
            finally:
                db.close()
                
        except ValueError:
            await update.message.reply_text("❌ Invalid task ID. Please provide a number.")
        except Exception as e:
            print(f"Error completing task: {e}")
            await update.message.reply_text("❌ Error completing task. Please try again.")
    
    async def cancel_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command"""
        if not context.args:
            await update.message.reply_text("❌ Please provide a task ID. Usage: `/cancel <task_id>`")
            return
        
        try:
            task_id = int(context.args[0])
            user_id = str(update.effective_user.id)
            
            db = SessionLocal()
            try:
                task = db.query(Task).filter(
                    Task.id == task_id,
                    Task.user_id == user_id
                ).first()
                
                if not task:
                    await update.message.reply_text("❌ Task not found or doesn't belong to you.")
                    return
                
                # Delete the task
                task_description = task.task_description
                db.delete(task)
                db.commit()
                
                # Cancel scheduled reminders
                self.scheduler.cancel_task_reminders(task_id)
                
                await update.message.reply_text(
                    f"🗑️ Task cancelled: **{task_description}**\n"
                    f"❌ Task has been removed and reminders cancelled."
                )
                
            finally:
                db.close()
                
        except ValueError:
            await update.message.reply_text("❌ Invalid task ID. Please provide a number.")
        except Exception as e:
            print(f"Error cancelling task: {e}")
            await update.message.reply_text("❌ Error cancelling task. Please try again.")
    
    async def run(self):
        """Start the Telegram bot"""
        try:
            # Reschedule existing tasks
            self.scheduler.reschedule_existing_tasks()
            
            # Schedule daily check-ins for the authorized user
            if self.authorized_user_id:
                self.scheduler.schedule_daily_checkins(self, self.authorized_user_id)
            
            print("Starting Telegram bot...")
            
            # Initialize and start polling within existing event loop
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            print(f"[OK] Telegram bot is now running and polling for updates...")
                
        except Exception as e:
            print(f"Error running Telegram bot: {e}")
            raise
    
    async def stop(self):
        """Stop the Telegram bot"""
        try:
            if self.application and hasattr(self.application, 'updater'):
                if self.application.updater.running:
                    await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            if self.scheduler:
                self.scheduler.shutdown()
            print("[OK] Telegram bot stopped.")
        except Exception as e:
            print(f"Error stopping Telegram bot: {e}")
    
    async def handle_conversation(self, update: Update, user_message: str, user_id: str):
        """Handle general conversation using AI"""
        try:
            response = await self.openai_service.chat_response(user_message)
            await update.message.reply_text(response)
        except Exception as e:
            print(f"Error handling conversation: {e}")
            await update.message.reply_text("I'm here to help! You can create tasks or just chat with me.")
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages by converting speech to text"""
        user_id = str(update.effective_user.id)
        
        print(f"Received voice message from user {user_id}")
        
        if not self.is_authorized(int(user_id)):
            await update.message.reply_text("Sorry, you are not authorized to use this bot.")
            return
        
        try:
            # Show typing while processing
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            
            # Get the voice file
            voice_file = await context.bot.get_file(update.message.voice.file_id)
            
            # Create temporary file for the voice message
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                temp_voice_path = temp_file.name
            
            try:
                # Download the voice file
                await voice_file.download_to_drive(temp_voice_path)
                
                # Convert speech to text using OpenAI Whisper
                transcribed_text = await self.openai_service.transcribe_audio(temp_voice_path)
                
                if transcribed_text.startswith("Sorry, I couldn't understand"):
                    await update.message.reply_text(
                        "🎤❌ I couldn't understand your voice message. Please try again or type your message instead."
                    )
                    return
                
                # Send confirmation of what was heard
                await update.message.reply_text(
                    f"🎤 I heard: \"{transcribed_text}\"\n\nProcessing your request..."
                )
                
                # Process the transcribed text as if it were a regular text message
                await self.process_user_input(update, transcribed_text, user_id)
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_voice_path):
                    os.unlink(temp_voice_path)
                
        except Exception as e:
            print(f"Error processing voice message: {e}")
            await update.message.reply_text(
                "❌ Sorry, I had trouble processing your voice message. Please try again or type your message."
            )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard button presses"""
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        if not self.is_authorized(int(user_id)):
            await query.answer("Not authorized")
            return
        
        await query.answer()  # Acknowledge the callback
        
        data = query.data
        if data.startswith("complete_"):
            task_id = int(data.split("_")[1])
            await self.complete_task_callback(query, task_id, user_id)
        elif data.startswith("cancel_"):
            task_id = int(data.split("_")[1])
            await self.cancel_task_callback(query, task_id, user_id)
        elif data == "show_tasks":
            await self.show_tasks_with_buttons(query, user_id)
    
    async def complete_task_callback(self, query, task_id: int, user_id: str):
        """Complete task from inline button"""
        try:
            db = SessionLocal()
            try:
                task = db.query(Task).filter(
                    Task.id == task_id,
                    Task.user_id == user_id
                ).first()
                
                if not task:
                    await query.edit_message_text("Task not found or already completed.")
                    return
                
                task.is_completed = True
                db.commit()
                
                # Cancel scheduled reminders
                self.scheduler.cancel_task_reminders(task_id)
                
                await query.edit_message_text(
                    f"✅ Task completed: **{task.task_description}**\n"
                    f"Great job! Task marked as complete."
                )
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error completing task via callback: {e}")
            await query.edit_message_text("❌ Error completing task.")
    
    async def cancel_task_callback(self, query, task_id: int, user_id: str):
        """Cancel task from inline button"""
        try:
            db = SessionLocal()
            try:
                task = db.query(Task).filter(
                    Task.id == task_id,
                    Task.user_id == user_id
                ).first()
                
                if not task:
                    await query.edit_message_text("Task not found.")
                    return
                
                task_description = task.task_description
                db.delete(task)
                db.commit()
                
                # Cancel scheduled reminders
                self.scheduler.cancel_task_reminders(task_id)
                
                await query.edit_message_text(
                    f"🗑️ Task cancelled: **{task_description}**\n"
                    f"Task has been removed and reminders cancelled."
                )
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error cancelling task via callback: {e}")
            await query.edit_message_text("❌ Error cancelling task.")
    
    async def show_tasks_with_buttons(self, query_or_update, user_id: str):
        """Show tasks with inline keyboard buttons for easy management"""
        try:
            db = SessionLocal()
            try:
                # Get pending tasks
                tasks = db.query(Task).filter(
                    Task.user_id == user_id,
                    Task.is_completed == False,
                    Task.scheduled_time > datetime.now()
                ).order_by(Task.scheduled_time).limit(10).all()
                
                if not tasks:
                    message = "You have no pending tasks! 🎉"
                    if hasattr(query_or_update, 'edit_message_text'):
                        await query_or_update.edit_message_text(message)
                    else:
                        await query_or_update.message.reply_text(message)
                    return
                
                # Create message with tasks
                message = "📋 **Your Pending Tasks:**\n\n"
                keyboard = []
                
                for i, task in enumerate(tasks, 1):
                    time_str = task.scheduled_time.strftime("%m/%d %H:%M")
                    message += f"{i}. **{task.task_description}**\n"
                    message += f"   ⏰ Due: {time_str}\n\n"
                    
                    # Add buttons for each task
                    task_buttons = [
                        InlineKeyboardButton(f"✅ Complete #{i}", callback_data=f"complete_{task.id}"),
                        InlineKeyboardButton(f"❌ Cancel #{i}", callback_data=f"cancel_{task.id}")
                    ]
                    keyboard.append(task_buttons)
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                if hasattr(query_or_update, 'edit_message_text'):
                    await query_or_update.edit_message_text(message, reply_markup=reply_markup, parse_mode='Markdown')
                else:
                    await query_or_update.message.reply_text(message, reply_markup=reply_markup, parse_mode='Markdown')
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error showing tasks with buttons: {e}")
            error_msg = "❌ Error loading tasks."
            if hasattr(query_or_update, 'edit_message_text'):
                await query_or_update.edit_message_text(error_msg)
            else:
                await query_or_update.message.reply_text(error_msg)
    
    async def handle_bulk_cancel(self, update: Update, user_id: str):
        """Cancel all pending tasks"""
        try:
            db = SessionLocal()
            try:
                # Get all pending tasks
                pending_tasks = db.query(Task).filter(
                    Task.user_id == user_id,
                    Task.is_completed == False
                ).all()
                
                if not pending_tasks:
                    await update.message.reply_text("You have no pending tasks to cancel.")
                    return
                
                # Cancel all tasks and their reminders
                cancelled_count = 0
                for task in pending_tasks:
                    self.scheduler.cancel_task_reminders(task.id)
                    db.delete(task)
                    cancelled_count += 1
                
                db.commit()
                
                await update.message.reply_text(
                    f"✅ Cancelled all {cancelled_count} pending tasks!\n"
                    f"All reminders have been removed."
                )
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error in bulk cancel: {e}")
            await update.message.reply_text("❌ Error cancelling tasks. Please try again.")
    
    async def handle_bulk_complete(self, update: Update, user_id: str):
        """Mark all pending tasks as complete"""
        try:
            db = SessionLocal()
            try:
                # Get all pending tasks
                pending_tasks = db.query(Task).filter(
                    Task.user_id == user_id,
                    Task.is_completed == False
                ).all()
                
                if not pending_tasks:
                    await update.message.reply_text("You have no pending tasks to complete.")
                    return
                
                # Mark all as complete and cancel reminders
                completed_count = 0
                for task in pending_tasks:
                    task.is_completed = True
                    self.scheduler.cancel_task_reminders(task.id)
                    completed_count += 1
                
                db.commit()
                
                await update.message.reply_text(
                    f"✅ Marked all {completed_count} tasks as complete!\n"
                    f"Great job staying on top of everything! 🎉"
                )
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"Error in bulk complete: {e}")
            await update.message.reply_text("❌ Error completing tasks. Please try again.")