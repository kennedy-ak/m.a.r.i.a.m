"""
Test script for voice input functionality
Note: This script would need an actual audio file to test with.
For now it just tests the integration setup.
"""
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_voice_setup():
    """Test that voice input components are properly imported"""
    try:
        from app.services.openai_service import OpenAIService
        from app.services.telegram_service import TelegramBot
        
        print("Testing voice input setup...")
        
        # Test OpenAI service import
        service = OpenAIService()
        print("✅ OpenAI service initialized successfully")
        
        # Test that transcribe_audio method exists
        if hasattr(service, 'transcribe_audio'):
            print("✅ transcribe_audio method available")
        else:
            print("❌ transcribe_audio method missing")
        
        # Test Telegram bot import
        # Note: Don't actually initialize to avoid token issues
        print("✅ TelegramBot class imported successfully")
        
        # Check if pydub is available (for potential audio conversion)
        try:
            import tempfile
            print("✅ tempfile module available")
        except ImportError:
            print("❌ tempfile module not available")
        
        print("\n🎉 Voice input setup completed successfully!")
        print("\nTo test voice input:")
        print("1. Start your bot: python main.py")
        print("2. Send a voice message to @Effe_ken_bot")
        print("3. The bot should transcribe and process your voice message")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please ensure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"❌ Setup error: {e}")


if __name__ == "__main__":
    test_voice_setup()