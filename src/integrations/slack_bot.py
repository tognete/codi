import os
import logging
import asyncio
from typing import Optional
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Disable noisy loggers
logging.getLogger("slack_bolt").setLevel(logging.WARNING)
logging.getLogger("slack_sdk").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

# Initialize the Slack app with your bot token
bot_token = os.environ.get("SLACK_BOT_TOKEN")
if not bot_token:
    raise ValueError("SLACK_BOT_TOKEN not found in environment variables")

# Enable debug mode for the Slack app
app = AsyncApp(token=bot_token)

def format_slack_message(text: str, suggestions: Optional[list] = None, code_changes: Optional[dict] = None) -> list:
    """Format a message for Slack with proper blocks"""
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text[:3000]  # Slack has a limit on text block size
            }
        }
    ]
    
    if suggestions:
        suggestions_text = "\n".join(f"• {suggestion}" for suggestion in suggestions)
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Suggestions:*\n{suggestions_text}"
            }
        })
    
    if code_changes:
        for file, content in code_changes.items():
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Changes to {file}:*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{content[:1000]}```"
                    }
                }
            ])
    
    return blocks

@app.event("app_mention")
async def handle_mention(body, say, logger):
    """Handle when the bot is mentioned in a channel"""
    try:
        event = body["event"]
        user = event.get('user')
        text = event.get("text", "").split(">", 1)[1].strip()
        
        logger.info(f"[Message through Slack] User {user}: {text}")
        
        # Get response from the agent
        response = await app.agent.chat(text, source="slack")
        
        # Format and send the response
        blocks = format_slack_message(response)
        await say(blocks=blocks)
        
        logger.info(f"[Message through Slack] Codi: {response[:100]}...")
        
    except Exception as e:
        error_msg = f"I encountered a technical issue while processing your request: {str(e)}. Let me know if you'd like me to try a different approach."
        logger.error(f"Error in handle_mention: {str(e)}", exc_info=True)
        await say(error_msg)

async def start_async_slack_bot(agent):
    """Start the Slack bot in socket mode"""
    try:
        app_token = os.environ.get("SLACK_APP_TOKEN")
        if not app_token:
            raise ValueError("SLACK_APP_TOKEN not found in environment variables")
        
        # Store the agent instance
        app.agent = agent
        
        logger.info("Starting Slack bot...")
        handler = AsyncSocketModeHandler(app, app_token)
        
        logger.info("✨ Slack Interface Ready!")
        await handler.start_async()
        
        # Keep the bot running
        await asyncio.Future()  # run forever
        
    except Exception as e:
        logger.error(f"Error starting Slack bot: {str(e)}", exc_info=True)
        raise

def start_slack_bot():
    """Synchronous wrapper to start the async Slack bot"""
    asyncio.run(start_async_slack_bot(agent)) 