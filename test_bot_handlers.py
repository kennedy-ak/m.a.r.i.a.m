"""
Test Telegram bot handlers in isolation
"""
import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8280809938:AAHqSXsk0pP4h0ZFaWuIxLYlbiEzMM0-JFQ"
AUTHORIZED_USER_ID = "838052010"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = str(update.effective_user.id)
    print(f"Received /start from user {user_id}")
    
    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return
    
    welcome_message = """
🤖 Welcome to your Personal Assistant Bot!

I can help you manage your tasks with natural language. Here's what you can do:

📝 **Add tasks**: Just tell me what you need to do
   • "Remind me to call John at 4 PM"
   • "Finish report in 2 hours"
   • "Meeting tomorrow at 10 AM"

📋 **Commands**:
   • /start - Show this welcome message
   • /help - Get help
   • /tasks - List your tasks
   • /complete <id> - Mark task as completed

Just type your task in plain English and I'll schedule it for you!
    """
    
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user_id = str(update.effective_user.id)
    print(f"Received /help from user {user_id}")
    
    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return
        
    help_text = """
🆘 **Help - Personal Assistant Bot**

**Creating Tasks:**
Just type what you want to do in natural language:
• "Call mom at 3 PM today"
• "Submit report by Friday"
• "Doctor appointment next Tuesday at 10 AM"

**Commands:**
• /start - Welcome message
• /help - This help message  
• /tasks - List your pending tasks
• /complete <id> - Mark task as completed

**Features:**
• 📱 SMS reminders 15 minutes before tasks
• 📞 Voice call reminders when tasks are due
• 🤖 Natural language processing powered by AI

Just start typing your tasks!
    """
    
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages"""
    user_id = str(update.effective_user.id)
    message_text = update.message.text
    
    print(f"Received message from user {user_id}: {message_text}")
    
    if user_id != AUTHORIZED_USER_ID:
        await update.message.reply_text("Sorry, you are not authorized to use this bot.")
        return
    
    await update.message.reply_text(f"I received your message: '{message_text}'\n\nThis is just a test bot. The full functionality will parse this as a task!")

async def main():
    """Main function to run the bot"""
    print("Starting test bot...")
    print(f"Bot token: {TOKEN[:20]}...")
    print(f"Authorized user: {AUTHORIZED_USER_ID}")
    
    # Create application
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot handlers added. Starting polling...")
    
    # Start the bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    
    print("Bot is now running! Press Ctrl+C to stop.")
    
    try:
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping bot...")
        await application.stop()
        
if __name__ == "__main__":
    asyncio.run(main())