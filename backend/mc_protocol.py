from llm_connector import get_response, pars_response_json
from datetime import datetime

def classify_message(message):
    flag = "General"
    if "task" or "plan" or "goal" in message.lower():
        task_ending = """
        today's date is: """ + datetime.now().strftime("%Y-%m-%d") + """
        Please create a specific and actionable task list following these guidelines:
        1. Each task should be concrete and measurable
        2. All due dates MUST be in the future (after today's date)
        3. Due dates should be realistic and spaced appropriately
        4. Tasks should be broken down into specific, actionable steps
        5. Each task should have a clear, detailed description
        6. The goal should be specific and achievable

        Example format:
        {
            "goal": "Launch a new mobile app for fitness tracking",
            "tasks": [
                {
                    "title": "Design user interface mockups",
                    "description": "Create wireframes and mockups for all main screens including workout tracking, progress dashboard, and user profile",
                    "due_date": "2024-04-15"
                },
                {
                    "title": "Develop core features",
                    "description": "Implement user authentication, workout tracking functionality, and data storage system",
                    "due_date": "2024-05-30"
                }
            ]
        }

        Important requirements:
        - All due dates must be in YYYY-MM-DD format
        - Due dates must be after today's date
        - Each task description should be specific and detailed
        - Tasks should be logically ordered
        - The goal should be clear and achievable
        - Include 3-5 specific tasks that lead to the goal
        """
        message = "create a specific and actionable task list for: " + message + task_ending
        flag = "Task"
    return message, flag

def chat_with_mc(message):
    message, flag = classify_message(message)
    response = get_response(message)
    parsed_response = pars_response_json(response)
    return parsed_response