import os
from openai import OpenAI
from dotenv import load_dotenv

"""Check if our OpenAI API key is working properly and can make a basic request"""

load_dotenv()
# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print(f"API key loaded: {api_key[:15]}...{api_key[-10:]}")
else:
    print("No API key found")
    exit(1)

# Try a basic OpenAI request to confirm everything works
try:
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": "Say 'Hello, world!'"}
        ],
        max_tokens=10
    )
    print("OpenAI call successful")
    print("Response:", response.choices[0].message.content)

except Exception as e:
    print(f"OpenAI call failed: {e}")

    # Basic check for common auth issues
    error_text = str(e).lower()


    if "authentication" in error_text or "api key" in error_text:
        print("\nThis looks like an authentication issue.")
        print("Your API key may be invalid, missing, or expired.")
        print("You can generate a new one here: https://platform.openai.com/api-keys")