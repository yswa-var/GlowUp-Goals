from llm_connector import get_response, pars_response_json
from datetime import datetime, timezone
from conn.database import DatabaseManager
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

def classify_message(message):
    flag = "General"
    if "add" and "task" in message.lower():
        flag = "Task"
        message = "create a specific and actionable task for: " + message
        task_ending = """
        today's date is: """ + datetime.now().strftime("%Y-%m-%d") + """
        Please create a specific and actionable task following these guidelines:
        1. task should be concrete and measurable
    elif "task" or "plan" or "goal" in message.lower():
        task_ending = 
        today's date is: """ + datetime.now().strftime("%Y-%m-%d") + """
        Please create a specific and actionable task  following these guidelines:
        1. task should be concrete and measurable
        2. All due dates MUST be in the future (after today's date)
        3. Due dates should be realistic and spaced appropriately
        4. Tasks should be broken down into specific, actionable steps
        5. task should have a clear, detailed description
        6. The goal should be specific and achievable

        Example format:
        {
            "tasks": [
                {
                    "title": "Design user interface mockups",
                    "description": "Create wireframes and mockups for all main screens including workout tracking, progress dashboard, and user profile",
                    "due_date": "2024-04-15"
                },
            ]
        }

        Important requirements:
        - All due dates must be in YYYY-MM-DD format
        - Due dates must be after today's date
        - task description should be specific and detailed
        - Tasks should be logically ordered
        - The goal should be clear and achievable
        """
        message = "create a specific and actionable task for: " + message + task_ending
        flag = "Task"
    return message, flag

async def save_tasks_to_db(tasks_data, user_id):
    try:
        db = DatabaseManager.get_database()
        tasks = tasks_data.get("tasks", [])
        
        for task in tasks:
            task_doc = {
                "user_id": ObjectId(user_id),
                "title": task["title"],
                "description": task["description"],
                "due_date": datetime.strptime(task["due_date"], "%Y-%m-%d"),
                "status": "pending",
                "created_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc)
            }
            await db.tasks.insert_one(task_doc)
        
        logger.info(f"Successfully saved {len(tasks)} tasks for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving tasks to database: {str(e)}")
        return False

async def chat_with_mc(message, user_id=None):
    message, flag = classify_message(message)
    
    response = get_response(message)
    parsed_response = pars_response_json(response)
    
    if flag == "Task" and user_id:
        await save_tasks_to_db(parsed_response, user_id)
    
    return parsed_response