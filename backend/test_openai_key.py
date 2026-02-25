"""
Simple standalone test for OpenAI API key
Run: python test_openai_key.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import sys

# Try to load .env from current directory
env_path = Path('.env')
print(f"Looking for .env at: {env_path.absolute()}")
print(f".env exists: {env_path.exists()}")

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print("✅ .env file loaded")
else:
    print("❌ .env file not found!")
    print("Please create a .env file with: OPENAI_API_KEY=your-key-here")
    sys.exit(1)

# Get the API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    print("❌ OPENAI_API_KEY not found in environment variables!")
    sys.exit(1)

# Show key info (masked for security)
key_prefix = api_key[:15] if len(api_key) > 15 else api_key
key_suffix = api_key[-10:] if len(api_key) > 10 else api_key
print(f"✅ API Key found: {key_prefix}...{key_suffix}")
print(f"Key length: {len(api_key)} characters")
print(f"Key format: {'Starts with sk-proj' if api_key.startswith('sk-proj') else 'Unexpected format'}")

# Test OpenAI connection
print("\n" + "="*50)
print("TESTING OPENAI CONNECTION")
print("="*50)

try:
    from openai import OpenAI
    
    # Initialize client
    client = OpenAI(api_key=api_key)
    
    # Test 1: Simple model list (tests authentication)
    print("\n📡 Test 1: Listing models...")
    models = client.models.list()
    print(f"✅ Success! Connected to OpenAI")
    print(f"   Available models include: {models.data[0].id}, {models.data[1].id}...")
    
    # Test 2: Simple chat completion
    print("\n📡 Test 2: Sending test message...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # You can also try "gpt-4" if you have access
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello! Your OpenAI key is working perfectly!' in one sentence."}
        ],
        max_tokens=20,
        temperature=0.7
    )
    
    print("✅ Test message successful!")
    print(f"\n🤖 Response: {response.choices[0].message.content}")
    print(f"\n📊 Usage: {response.usage.total_tokens} tokens used")
    
    # Test 3: Test with a Zheng He question (like your app would use)
    print("\n" + "="*50)
    print("TESTING WITH ZHENG HE QUESTION")
    print("="*50)
    
    response2 = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a historian specializing in Chinese maritime exploration."},
            {"role": "user", "content": "In one sentence, who was Zheng He?"}
        ],
        max_tokens=50
    )
    
    print(f"🤖 Response: {response2.choices[0].message.content}")
    print(f"\n✅ All tests passed! Your OpenAI key is working correctly.")
    
except ImportError:
    print("❌ Error: openai package not installed!")
    print("   Run: pip install openai")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Error connecting to OpenAI:")
    print(f"   {str(e)}")
    
    # Provide helpful error messages
    error_str = str(e).lower()
    if "authentication" in error_str or "api key" in error_str:
        print("\n🔍 This is an AUTHENTICATION error:")
        print("   - Your API key is invalid or expired")
        print("   - Go to https://platform.openai.com/api-keys to create a new key")
        print("   - Make sure you're copying the entire key with no spaces")
    elif "rate limit" in error_str:
        print("\n⏱️  RATE LIMIT error:")
        print("   - You've made too many requests. Wait a minute and try again.")
    elif "billing" in error_str or "quota" in error_str or "insufficient_quota" in error_str:
        print("\n💰 BILLING error:")
        print("   - Your OpenAI account has no credits or billing is not set up")
        print("   - Go to https://platform.openai.com/account/billing to add credits")
    elif "connection" in error_str:
        print("\n🌐 CONNECTION error:")
        print("   - Check your internet connection")
        print("   - OpenAI might be down: https://status.openai.com")
    else:
        print("\n🔧 Unknown error. Check your key and try again.")