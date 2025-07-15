import os
from dotenv import load_dotenv
import openai

# Load environment variables from .env
load_dotenv()

# Set API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    raise ValueError("❌ OPENAI_API_KEY environment variable not set in .env file.")

def analyze_code_with_llm(file_content: str, filename: str) -> tuple[bool, str]:
    prompt = f"""
You are an expert AI code reviewer.

Analyze the following file: `{filename}`.
Your task:
- Identify bugs, code smells, security vulnerabilities
- Suggest improvements or refactorings
- Mention anything the code does well
- Respond clearly for a human reader

Code:
{filename}
{file_content[:3000]}  # truncate to avoid token limit
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        message = response.choices[0].message.content.strip()
        return True, message
    except Exception as e:
        return False, f"❌ LLM error: {str(e)}"
