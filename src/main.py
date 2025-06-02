import os
import asyncio
from dotenv import load_dotenv
from src.integrations.slack_bot import start_slack_bot

def main():
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    required_vars = ['OPENAI_API_KEY', 'SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        return
    
    # Print token prefixes for verification (safely)
    bot_token = os.getenv('SLACK_BOT_TOKEN', '')
    app_token = os.getenv('SLACK_APP_TOKEN', '')
    print("\nToken verification:")
    print(f"SLACK_BOT_TOKEN starts with: {bot_token[:10]}...")
    print(f"SLACK_APP_TOKEN starts with: {app_token[:10]}...")
    
    print("\nStarting Codi Slack bot...")
    try:
        # Start the bot
        start_slack_bot()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"\nError starting bot: {str(e)}")
        print("\nPlease verify:")
        print("1. Your Slack App is properly configured at https://api.slack.com/apps")
        print("2. Socket Mode is enabled")
        print("3. Bot Token Scopes include: app_mentions:read, chat:write, channels:history")
        print("4. The app is installed to your workspace")
        print("5. You're using the correct tokens from the Slack App settings")

if __name__ == "__main__":
    main() 