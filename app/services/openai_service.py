import openai
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from app.core.config import settings

# Configure OpenAI
openai.api_key = settings.openai_api_key


class OpenAIService:
    """Service for processing natural language task inputs using OpenAI"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
    
    async def parse_task(self, user_input: str) -> Dict:
        """
        Parse natural language task input and extract task details
        
        Args:
            user_input (str): Natural language task input
            
        Returns:
            Dict: Parsed task details with description and scheduled_time
        """
        current_time = datetime.now()
        
        # Create a detailed prompt for task parsing
        prompt = f"""
        You are a personal assistant that parses natural language task inputs.
        Current time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
        
        Parse the following task input and return a JSON response with these fields:
        - task_description: Clear, concise description of the task
        - scheduled_time: ISO format datetime when the task should be done
        
        Rules:
        1. If no specific time is mentioned, default to 1 hour from now
        2. If time is mentioned (like "in 2 hours", "at 4 PM", "tomorrow at 9 AM"), calculate the exact datetime
        3. For relative times like "in X hours/minutes", add to current time
        4. For absolute times like "at 4 PM", use today's date unless specified otherwise
        5. For "tomorrow" or future dates, calculate accordingly
        
        User input: "{user_input}"
        
        Return only valid JSON with no additional text.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that parses task inputs and returns JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse the JSON response
            parsed_result = json.loads(result)
            
            # Validate and ensure we have required fields
            if "task_description" not in parsed_result or "scheduled_time" not in parsed_result:
                raise ValueError("Missing required fields in OpenAI response")
            
            # Convert scheduled_time to datetime object if it's a string
            if isinstance(parsed_result["scheduled_time"], str):
                parsed_result["scheduled_time"] = datetime.fromisoformat(
                    parsed_result["scheduled_time"].replace("Z", "+00:00")
                )
            
            return parsed_result
            
        except json.JSONDecodeError:
            # Fallback parsing if JSON parsing fails
            return self._fallback_parse(user_input)
        except Exception as e:
            print(f"Error parsing task with OpenAI: {e}")
            return self._fallback_parse(user_input)
    
    def _fallback_parse(self, user_input: str) -> Dict:
        """
        Fallback parsing method when OpenAI fails
        
        Args:
            user_input (str): Original user input
            
        Returns:
            Dict: Basic parsed task with default 1-hour scheduling
        """
        return {
            "task_description": user_input,
            "scheduled_time": datetime.now() + timedelta(hours=1)
        }
    
    async def query_tasks(self, user_input: str, tasks: list) -> str:
        """
        Process natural language queries about tasks
        
        Args:
            user_input (str): Natural language query
            tasks (list): List of user's tasks
            
        Returns:
            str: Formatted response about tasks
        """
        if not tasks:
            return "You don't have any tasks scheduled."
        
        # Format tasks for OpenAI
        tasks_text = "\n".join([
            f"- {task.task_description} (scheduled for {task.scheduled_time.strftime('%Y-%m-%d %H:%M')}, "
            f"{'completed' if task.is_completed else 'pending'})"
            for task in tasks
        ])
        
        prompt = f"""
        User query: "{user_input}"
        
        Current tasks:
        {tasks_text}
        
        Provide a helpful response to the user's query about their tasks. Be conversational and informative.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful personal assistant responding to task queries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error processing query with OpenAI: {e}")
            return f"Here are your tasks:\n{tasks_text}"
    
    async def chat_response(self, user_message: str, context: str = "") -> str:
        """
        Generate conversational responses for general chat
        
        Args:
            user_message (str): User's message
            context (str): Additional context if needed
            
        Returns:
            str: AI-generated response
        """
        try:
            system_prompt = """You are Kennedy's personal AI assistant bot. You are friendly, helpful, and conversational. 
            You help manage tasks, provide information, and engage in natural conversation. 
            Keep responses concise but warm and personalized for Kennedy.
            If the message seems like it could be a task, suggest creating it as a task."""
            
            full_prompt = f"{context}\n\nUser message: {user_message}" if context else user_message
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.8,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating chat response: {e}")
            return "I'm here to help! You can create tasks by telling me what you need to do, or just chat with me."
    
    async def is_task_request(self, user_message: str) -> bool:
        """
        Determine if a message is a task creation request
        
        Args:
            user_message (str): User's message
            
        Returns:
            bool: True if it's likely a task request
        """
        try:
            prompt = f"""
            Classify this message as either a TASK creation request or a QUERY/CHAT.
            
            TASK creation requests:
            - Want to CREATE a new task/reminder
            - Examples: "Remind me to call John at 3pm", "Schedule meeting tomorrow", "I need to buy groceries"
            - Usually have imperative verbs: remind, schedule, book, do, call, meet
            - Specify WHAT to do and WHEN to do it
            
            QUERY/CHAT (NOT task creation):
            - Questions about EXISTING tasks: "Do I have tasks today?", "What tasks do I have?", "Show my tasks"
            - General conversation: greetings, questions, comments
            - Information requests: "How are you?", "What can you do?"
            - Questions with: "do I have", "what tasks", "show me", "list my", "any tasks"
            
            Message: "{user_message}"
            
            Key question: Is the user asking to CREATE a new task, or asking ABOUT existing tasks?
            
            Respond with only "TASK" (for creation) or "QUERY" (for questions/chat) - nothing else.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at distinguishing between task creation requests and task queries/general chat. Be very careful to classify correctly."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip().upper()
            return result == "TASK"
            
        except Exception as e:
            print(f"Error classifying message: {e}")
            # Improved fallback logic - be more conservative
            user_lower = user_message.lower()
            
            # Strong indicators of queries (NOT task creation)
            query_indicators = [
                'do i have', 'what tasks', 'show me', 'list my', 'any tasks', 
                'tasks today', 'tasks for', 'what do i', 'what are my',
                'check my', 'view my', 'see my', 'have i got', 'got any'
            ]
            
            if any(indicator in user_lower for indicator in query_indicators):
                return False
            
            # Only treat as task if it has clear task creation indicators
            task_indicators = ['remind me to', 'schedule', 'book', 'set reminder', 'i need to', 'i have to']
            return any(indicator in user_lower for indicator in task_indicators)
    
    async def generate_daily_summary(self, tasks: List, time_of_day: str) -> str:
        """
        Generate daily task summaries for check-ins
        
        Args:
            tasks (List): List of tasks
            time_of_day (str): "morning", "afternoon", "evening", or "night"
            
        Returns:
            str: Formatted summary message
        """
        if not tasks:
            greetings = {
                "morning": "Good morning, Kennedy! 🌅 You have no tasks scheduled for today. Enjoy your free day!",
                "afternoon": "Good afternoon, Kennedy! ☀️ No tasks on your schedule right now. Perfect time to relax or plan ahead.",
                "evening": "Good evening, Kennedy! 🌆 No pending tasks for today. You're all caught up!",
                "night": "Good night, Kennedy! 🌙 No incomplete tasks today. Great job staying on top of things!"
            }
            return greetings.get(time_of_day, "You have no tasks scheduled.")
        
        # Separate completed and pending tasks
        completed_tasks = [t for t in tasks if t.is_completed]
        pending_tasks = [t for t in tasks if not t.is_completed]
        
        tasks_text = ""
        if pending_tasks:
            tasks_text += "Pending tasks:\n"
            for task in pending_tasks:
                tasks_text += f"• {task.task_description} (due: {task.scheduled_time.strftime('%H:%M')})\n"
        
        if completed_tasks:
            tasks_text += f"\nCompleted today: {len(completed_tasks)} tasks ✅"
        
        try:
            prompt = f"""
            Generate a personalized {time_of_day} check-in message for Kennedy about his tasks.
            
            {tasks_text}
            
            Make it warm, encouraging, and include appropriate greetings for the {time_of_day}.
            Keep it concise but motivating.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Kennedy's personal assistant providing daily task check-ins."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"Error generating daily summary: {e}")
            return f"{time_of_day.capitalize()} update:\n{tasks_text}"
    
    async def transcribe_audio(self, audio_file_path: str) -> str:
        """
        Convert speech to text using OpenAI Whisper
        
        Args:
            audio_file_path (str): Path to the audio file
            
        Returns:
            str: Transcribed text
        """
        try:
            with open(audio_file_path, 'rb') as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="en"  # You can make this dynamic or auto-detect
                )
                
                transcribed_text = response.text.strip()
                print(f"Voice transcribed: {transcribed_text}")
                return transcribed_text
                
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return "Sorry, I couldn't understand the audio. Please try again or type your message."