"""
Simple test to check if Telegram bot token works
"""
import asyncio
import os
import sys
from telegram import Bot

async def test_bot_token():
    """Test if the bot token is working"""
    
    # Get token from .env
    token = "8280809938:AAHqSXsk0pP4h0ZFaWuIxLYlbiEzMM0-JFQ"
    
    try:
        bot = Bot(token=token)
        
        print("Testing bot connection...")
        me = await bot.get_me()
        print("[OK] Bot connected successfully!")
        print(f"Bot name: {me.first_name}")
        print(f"Bot username: @{me.username}")
        print(f"Bot ID: {me.id}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Bot connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_bot_token())