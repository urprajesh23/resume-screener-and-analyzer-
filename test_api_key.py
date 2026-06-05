import google.genai as genai
import sys
import argparse

def verify_api_key(api_key: str):
    print(f"Testing API Key: {api_key[:10]}...")
    
    try:
        # Initialize client
        client = genai.Client(api_key=api_key)
        
        # Test basic question
        print("\nSending a basic question to the model...")
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Answer this with one word: What is the color of a clear daytime sky?'
        )
        print("Success! Model response:", response.text.strip())
        print("\n✅ The API key is VALID and functional.")
        
    except Exception as e:
        error_msg = str(e)
        print("\n❌ Failed to generate response.")
        print(f"Error details: {error_msg}")
        
        if "leaked" in error_msg.lower() or "permission_denied" in error_msg.lower():
            print("\nDiagnosis: Your API key has been flagged by Google as leaked or you don't have permission.")
        elif "api_key" in error_msg.lower() or "invalid" in error_msg.lower():
            print("\nDiagnosis: Your API key is likely invalid or malformed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test a Gemini API Key")
    parser.add_argument("api_key", help="The Gemini API key to test")
    args = parser.parse_args()
    
    verify_api_key(args.api_key)
