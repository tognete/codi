import os
import click
import asyncio
import json
from pathlib import Path

from .core.agent import CodiAgent
from .integrations.slack_bot import start_async_slack_bot

@click.group()
def cli():
    """Codi - AI Senior Software Developer"""
    pass

@cli.command()
def run():
    """Start Codi in interactive mode (CLI + Slack)"""
    try:
        # Initialize the agent
        agent = CodiAgent()
        
        # Print welcome message
        click.echo(click.style("\n🚀 Starting Codi...", fg="green", bold=True))
        click.echo(click.style("Your AI Senior Software Developer", fg="green"))
        
        click.echo("\nStarting services:")
        click.echo("1. CLI Chat Interface")
        click.echo("2. Slack Integration")
        
        # Start both CLI and Slack interfaces
        asyncio.run(start_services(agent))
        
    except Exception as e:
        click.echo(click.style(f"\nError: {str(e)}", fg="red"), err=True)

async def start_services(agent: CodiAgent):
    """Start both CLI and Slack services"""
    try:
        # Create tasks for both services
        cli_task = asyncio.create_task(interactive_chat(agent))
        slack_task = asyncio.create_task(start_async_slack_bot(agent))
        
        # Wait for both tasks
        await asyncio.gather(cli_task, slack_task)
    except KeyboardInterrupt:
        click.echo("\n\nShutting down Codi... 👋")
    except Exception as e:
        click.echo(f"\nError: {str(e)}", err=True)

async def interactive_chat(agent: CodiAgent):
    """Run the interactive chat loop"""
    click.echo(click.style("\n✨ CLI Chat Interface Ready!", fg="green"))
    click.echo(click.style("\nTips:", fg="yellow"))
    click.echo("• Chat with me as you would with a senior software developer")
    click.echo("• I'll automatically detect your project context")
    click.echo("• Use Ctrl+C to exit")
    click.echo("• Your conversation is synced with Slack")
    
    while True:
        try:
            # Get user input
            user_input = click.prompt("\nYou", prompt_suffix=" > ", type=str)
            
            # Process the message
            with click.progressbar(
                length=1,
                label=click.style("Thinking...", fg="blue"),
                show_eta=False
            ) as pb:
                response = await agent.chat(user_input)
                pb.update(1)
            
            # Print the response
            click.echo(click.style("\nCodi", fg="green", bold=True))
            click.echo(response)
            
        except click.exceptions.Abort:
            raise KeyboardInterrupt
        except Exception as e:
            click.echo(click.style(f"\nError: {str(e)}", fg="red"), err=True)

if __name__ == '__main__':
    cli() 