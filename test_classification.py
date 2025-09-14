"""
Test script for message classification
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.openai_service import OpenAIService


async def test_classification():
    """Test message classification"""
    service = OpenAIService()
    
    # Test messages
    test_messages = [
        # Task queries (should return False)
        "Do I have any tasks today?",
        "What tasks do I have?",
        "Show me my tasks",
        "I want to know if I have any task to complete today?",
        "List my tasks",
        "Any tasks for tomorrow?",
        "What's on my schedule?",
        
        # Task creation (should return True)
        "Remind me to call John at 3 PM",
        "Schedule a meeting tomorrow at 10 AM",
        "I need to buy groceries",
        "Book a dentist appointment",
        "Set reminder for 5 PM",
        
        # General chat (should return False)
        "Hello",
        "How are you?",
        "What's the weather?",
        "Tell me a joke"
    ]
    
    print("Testing message classification...")
    print("=" * 50)
    
    for message in test_messages:
        try:
            is_task = await service.is_task_request(message)
            result = "TASK" if is_task else "QUERY/CHAT"
            print(f"{message:<45} -> {result}")
        except Exception as e:
            print(f"{message:<45} -> ERROR: {e}")
    
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_classification())