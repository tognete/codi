import logging
import click
from typing import Optional
from functools import wraps
import time
import asyncio

class WorkflowLogger:
    """Tracks and logs Codi's workflow and tool usage in a human-readable format"""
    
    def __init__(self):
        self.step_count = 0
        self.active_tasks = []
        
    def log_step(self, action: str, tool: Optional[str] = None, details: Optional[str] = None):
        """Log a workflow step with optional tool usage"""
        self.step_count += 1
        
        # Format the step number with emoji based on type
        if tool:
            prefix = f"🛠️  Step {self.step_count}"
            tool_info = f" using {tool}"
        else:
            prefix = f"💭 Step {self.step_count}"
            tool_info = ""
            
        # Build the log message
        message = f"{prefix}: {action}{tool_info}"
        if details:
            message += f"\n   └─ {details}"
            
        # Print with color
        click.echo(click.style(message, fg="blue"))
        
        # Track active task
        self.active_tasks.append(action)
        
    def log_working(self, message: str = "Still working..."):
        """Show that Codi is still actively working"""
        if self.active_tasks:
            current_task = self.active_tasks[-1]
            click.echo(click.style(f"   ⏳ {message} (on: {current_task})", fg="yellow"))
    
    def log_result(self, success: bool, message: str):
        """Log the result of a step"""
        # Remove the completed task
        if self.active_tasks:
            self.active_tasks.pop()
            
        if success:
            click.echo(click.style(f"   ✅ {message}", fg="green"))
        else:
            click.echo(click.style(f"   ❌ {message}", fg="red"))
    
    def reset(self):
        """Reset the step counter and active tasks"""
        self.step_count = 0
        self.active_tasks = []

def log_workflow(explanation: str):
    """Decorator to log tool usage with timing"""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # Get the tool name from the function name
            tool_name = func.__name__.replace('_', ' ').title()
            
            # Log the step
            self.workflow_logger.log_step(explanation, tool_name)
            
            # Time the operation
            start_time = time.time()
            last_update = time.time()
            
            try:
                # Create a task for the actual function
                task = asyncio.create_task(func(self, *args, **kwargs))
                
                # While waiting for the result, show progress
                while not task.done():
                    current_time = time.time()
                    if current_time - last_update >= 2.0:  # Update every 2 seconds
                        duration = current_time - start_time
                        self.workflow_logger.log_working(f"Working for {duration:.1f}s...")
                        last_update = current_time
                    await asyncio.sleep(0.1)  # Small sleep to prevent CPU spinning
                
                # Get the result
                result = await task
                duration = time.time() - start_time
                self.workflow_logger.log_result(True, f"Completed in {duration:.2f}s")
                return result
                
            except Exception as e:
                self.workflow_logger.log_result(False, str(e))
                raise
                
        return wrapper
    return decorator 