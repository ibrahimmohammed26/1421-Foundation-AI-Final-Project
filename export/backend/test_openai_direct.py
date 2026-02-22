import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key loaded: {api_key[:15]}...{api_key[-10:] if api_key else 'NOT FOUND'}")

if not api_key:
    print("❌ No API key found!")
    exit(1)

# Try direct OpenAI call
try:
    client = OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'Hello, world!'"}],
        max_tokens=10
    )
    
    print(f"✅ OpenAI direct call successful!")
    print(f"Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ OpenAI direct call failed: {e}")
    
    # Check if it's an authentication error
    if "authentication" in str(e).lower() or "api key" in str(e).lower():
        print("\nThis is an AUTHENTICATION error. Your API key is likely invalid or expired.")
        print("Try generating a new API key at: https://platform.openai.com/api-keys")