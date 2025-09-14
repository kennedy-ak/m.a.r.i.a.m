import httpx
import os
from typing import Dict
from app.core.config import settings


class MnotifyService:
    """Service for sending SMS and voice calls via Mnotify API"""
    
    def __init__(self):
        self.api_key = settings.mnotify_api_key
        self.sms_url = "https://api.mnotify.com/api/sms/quick"
        self.voice_url = "https://api.mnotify.com/api/voice/quick"
        self.phone_number = os.getenv("YOUR_PHONE_NUMBER")
        self.sender = "Kenn-Site"
    
    async def send_sms_reminder(self, task_description: str, scheduled_time: str) -> Dict:
        """
        Send SMS reminder for a task
        
        Args:
            task_description (str): Description of the task
            scheduled_time (str): When the task is scheduled
            
        Returns:
            Dict: API response
        """
        message = f"⏰ Reminder: {task_description} is scheduled for {scheduled_time} (in 15 minutes)!"
        
        payload = {
            "recipient": [self.phone_number],
            "sender": self.sender,
            "message": message,
            "is_schedule": False,
            "schedule_date": ""
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add API key as query parameter
        url = f"{self.sms_url}?key={self.api_key}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                result = response.json()
                print(f"SMS sent: {result}")
                return result
                
        except Exception as e:
            print(f"Error sending SMS: {e}")
            return {"error": str(e)}
    
    async def make_voice_call(self, task_description: str = "") -> Dict:
        """
        Make a voice call reminder using audio file
        
        Args:
            task_description (str): Description of the task (not used with audio file)
            
        Returns:
            Dict: API response
        """
        import os
        
        # Path to the audio file
        audio_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'message.wav')
        
        if not os.path.exists(audio_file_path):
            return {"error": "Audio file 'message.wav' not found"}
        
        data = {
            'campaign': f'Task Reminder Call',
            'recipient[]': [self.phone_number],
            'voice_id': '',
            'is_schedule': False,
            'schedule_date': ''
        }
        
        # Add API key as query parameter
        url = f"{self.voice_url}?key={self.api_key}"
        
        try:
            async with httpx.AsyncClient() as client:
                with open(audio_file_path, 'rb') as audio_file:
                    files = {'file': audio_file}
                    
                    response = await client.post(
                        url,
                        data=data,
                        files=files,
                        timeout=60.0
                    )
                    
                    result = response.json()
                    print(f"Voice call made: {result}")
                    return result
                    
        except Exception as e:
            print(f"Error making voice call: {e}")
            return {"error": str(e)}
    
    async def test_connection(self) -> bool:
        """
        Test the Mnotify API connection
        
        Returns:
            bool: True if connection is working
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.mnotify.com/api/balance?key={self.api_key}",
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Mnotify connection test failed: {e}")
            return False