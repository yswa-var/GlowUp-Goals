from dotenv import load_dotenv
import openai
import os
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv("/Users/apple/coach/GlowUp-Goals/.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_response(prompt):
    # Ensure the prompt asks for JSON format and is concise
    if not "json" in prompt.lower():
        prompt = f"{prompt} Return a concise answer in JSON format."
    
    logger.info(f"Sending prompt to OpenAI: {prompt}")
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that always responds in valid JSON format. Keep responses concise and complete."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,  # Increased from 100 to 500
            temperature=0.7  # Added temperature for more consistent responses
        )
        content = response.choices[0].message.content.strip()
        logger.info(f"Received response from OpenAI: {content}")
        return content
    except Exception as e:
        logger.error(f"Error calling OpenAI: {str(e)}")
        raise

def pars_response_json(content):
    try:
        logger.info(f"Parsing response: {content}")
        # Clean up the response
        if content.startswith("```"):
            content = content.split("```", 2)[1]
            if content.strip().startswith("json"):
                content = content.strip()[4:]
            content = content.strip()
        
        # Remove any trailing commas or incomplete objects
        content = content.rstrip(',')
        if content.endswith('...'):
            content = content[:-3]
        
        parsed = json.loads(content)
        logger.info(f"Successfully parsed JSON: {parsed}")
        return parsed
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {str(e)}")
        # Try to fix common JSON issues
        try:
            # If the response is incomplete, try to close any open brackets
            if content.count('{') > content.count('}'):
                content += '}'
            if content.count('[') > content.count(']'):
                content += ']'
            parsed = json.loads(content)
            logger.info(f"Successfully parsed JSON after fixing: {parsed}")
            return parsed
        except:
            # Return a simple error message in JSON format
            return {"error": "Failed to parse response as JSON", "raw_response": content}
    except Exception as e:
        logger.error(f"Unexpected error parsing response: {str(e)}")
        raise

# content = get_response("What is the capital of France? return answer in json format with key as capital and value as country")
# print(pars_response_json(content))