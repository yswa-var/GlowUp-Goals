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
        5. task should have a clear, short and detailed description
        6. The goal should be specific and achievable

        Example format:
        {
            "tasks": [
                {
                    "title": "Market research on fitness app competitors",
                    "estimated_time": "2h",
                    "repeat": {
                        "enabled": "no",
                    },
                    "due_date": "2024-04-15"
                },
            ]
        }
        or 
        {
            "tasks": [
                {
                    "title": "Beta testing with fitness enthusiasts",
                    "estimated_time": "2h",
                    "repeat": {
                        "enabled": "yes",
                        "interval": "1d"
                    },
                    "due_date": "2024-04-15"
                },
            ]
        }

        Important requirements:
        - All due dates must be in YYYY-MM-DD format
        - Due dates must be after today's date
        - Estimated time should be in format: Xh (hours) or Xm (minutes)
        - Repeat interval should be in format: Xd (days), Xh (hours), or Xm (minutes)
        - Tasks should be logically ordered
        - The goal should be clear and achievable
        """
        message = f"create a specific and actionable task for: ({message}) \n" + task_ending
        flag = "Task"
        return message, flag
    
    elif "plan" or "goal" or "task" in message.lower():
        flag = "Task"
        task_ending = """
        today's date is: """ + datetime.now().strftime("%Y-%m-%d") + """
        Please create a specific and actionable task list following these guidelines:
        1. task list should be concrete and measurable
        2. All due dates MUST be in the future (after today's date)
        3. Due dates should be realistic and spaced appropriately
        4. Tasks should be broken down into specific, actionable steps
        5. Each task should have an estimated completion time
        6. Specify if the task should repeat and at what interval
        7. The goal should be specific and achievable

        Example format:
        {
            "goal": "Launch a new mobile app for fitness tracking",
            "tasks": [
                {
                    "title": "Market research on fitness app competitors",
                    "estimated_time": "2h",
                    "repeat": {
                        "enabled": "no",
                    },
                    "due_date": "2024-04-15"
                },
                {
                    "title": "Beta testing with fitness enthusiasts",
                    "estimated_time": "2h",
                    "repeat": {
                        "enabled": "yes",
                        "interval": "1d"
                    },
                    "due_date": "2024-04-15"
                }
            ]
        }

        Important requirements:
        - All due dates must be in YYYY-MM-DD format
        - Due dates must be after today's date
        - Estimated time should be in format: Xh (hours) or Xm (minutes)
        - Repeat interval should be in format: Xd (days), Xh (hours), or Xm (minutes)
        - Tasks should be logically ordered
        - The goal should be clear and achievable
        """
        message = f"create a specific and actionable task for: ({message}) \n" + task_ending
    return message, flag

async def save_tasks_to_db(tasks_data, user_id):
    try:
        db = DatabaseManager.get_database()
        tasks = tasks_data.get("tasks", [])
        
        # Get the highest task_order for the user
        highest_task = await db.tasks.find_one(
            {"user_id": ObjectId(user_id)},
            sort=[("task_order", -1)]
        )
        current_task_order = 1 if highest_task is None else highest_task.get("task_order", 0) + 1
        
        for task in tasks:
            # Handle repeat field which might not have interval
            repeat_data = task.get("repeat", {})
            if isinstance(repeat_data, dict):
                repeat_enabled = repeat_data.get("enabled", "no")
                repeat_interval = repeat_data.get("interval", "")
            else:
                repeat_enabled = "no"
                repeat_interval = ""

            task_doc = {
                "user_id": ObjectId(user_id),
                "title": task["title"],
                "description": "",  # Empty description as user will add it
                "estimated_time": task.get("estimated_time", ""),
                "repeat": {
                    "enabled": repeat_enabled,
                    "interval": repeat_interval
                },
                "due_date": datetime.strptime(task["due_date"], "%Y-%m-%d"),
                "status": "pending",
                "task_order": current_task_order,
                "created_at": datetime.now(timezone.utc),
                "completed_at": datetime.now(timezone.utc)  # Set to current time, will be updated when task is completed
            }
            await db.tasks.insert_one(task_doc)
            current_task_order += 1
        
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