from typing import Dict, List, Optional
import os
from openai import AsyncOpenAI
from pydantic import BaseModel
from dotenv import load_dotenv
import json
from .chat import ChatMemory, Message
from .workflow_logger import WorkflowLogger, log_workflow
import time
import asyncio

# Load environment variables
load_dotenv()

# Global configuration
OPENAI_MODEL = "gpt-4o"  # Easy to change model version in one place

class CodeContext(BaseModel):
    """Represents the current coding context"""
    files: Dict[str, str]  # file paths and their contents
    current_file: Optional[str] = None
    language: Optional[str] = None
    project_root: Optional[str] = None

class CodingTask(BaseModel):
    """Represents a coding task to be performed"""
    task_type: str  # 'analyze', 'generate', 'review', etc.
    description: str
    context: CodeContext
    requirements: Optional[List[str]] = None

class CodeResponse(BaseModel):
    """Represents the AI's response to a coding task"""
    solution: str
    explanation: Optional[str] = None
    suggestions: Optional[List[str]] = None
    code_changes: Optional[Dict[str, str]] = None

class CodiAgent:
    """Main AI agent class for code understanding and generation"""
    
    def __init__(self):
        """Initialize the AI agent with necessary components"""
        self.current_context: Optional[CodeContext] = None
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.chat_memory = ChatMemory()
        self.workflow_logger = WorkflowLogger()
        self.personality = {
            "name": "Codi",
            "role": "AI Senior Software Developer",
            "style": "professional and experienced",
            "expertise": ["software architecture", "code review", "system design", "debugging", "best practices"],
            "capabilities": [
                "direct file system access",
                "workspace awareness",
                "code reading and writing",
                "git repository interaction",
                "real-time code analysis"
            ]
        }
        
        # Detect workspace from environment
        self.workspace_path = self._detect_workspace()
        if self.workspace_path:
            self.project_name = os.path.basename(self.workspace_path)
            self.chat_memory.update_context({
                "workspace_path": self.workspace_path,
                "project_name": self.project_name
            })
    
    def _detect_workspace(self) -> Optional[str]:
        """Detect the workspace path from environment variables and git"""
        # Try to get from GITHUB_REPO env var
        if github_repo := os.getenv("GITHUB_REPO"):
            # Extract repo name from github repo string
            repo_name = github_repo.split('/')[-1] if '/' in github_repo else github_repo
            # Look for this directory in common locations
            common_paths = [
                os.getcwd(),  # Current directory
                os.path.expanduser("~/devel"),  # ~/devel
                os.path.expanduser("~/dev"),    # ~/dev
                os.path.expanduser("~/projects"),# ~/projects
                os.path.expanduser("~/code"),    # ~/code
                os.path.expanduser("~"),         # Home directory
            ]
            
            for base_path in common_paths:
                potential_path = os.path.join(base_path, repo_name)
                if os.path.isdir(potential_path) and os.path.isdir(os.path.join(potential_path, ".git")):
                    return potential_path
        
        # If not found by GITHUB_REPO, try to detect git repository from current directory
        try:
            current_dir = os.getcwd()
            while current_dir != '/':
                if os.path.isdir(os.path.join(current_dir, ".git")):
                    return current_dir
                current_dir = os.path.dirname(current_dir)
        except Exception:
            pass
        
        # If all else fails, use current directory
        return os.getcwd()
    
    async def chat(self, message: str, source: str = "cli") -> str:
        """Handle a chat message from the user"""
        try:
            # Reset workflow logger for new conversation
            self.workflow_logger.reset()
            self.workflow_logger.log_step("Starting new conversation", details=f"Message: {message[:100]}...")
            
            # Start or continue conversation
            if not self.chat_memory.current_conversation:
                self.workflow_logger.log_step("Initializing conversation context")
                self.chat_memory.start_conversation(self.workspace_path)
            
            # Add user message to memory with source
            self.chat_memory.add_message("user", message, metadata={"source": source})
            
            # Get conversation context
            self.workflow_logger.log_step("Preparing conversation context")
            context = self.chat_memory.get_conversation_context()
            recent_messages = self.chat_memory.get_recent_messages()
            
            # Prepare the conversation for the AI
            self.workflow_logger.log_step("Building conversation history")
            messages = [
                {
                    "role": "system",
                    "content": self._get_personality_prompt()
                }
            ]
            
            # Add project context
            if self.workspace_path:
                messages.append({
                    "role": "system",
                    "content": f"""You are actively working in the project '{self.project_name}' located at {self.workspace_path}.
    You have full access to read and modify files in this workspace. Use this access to provide concrete, specific help.
    
    IMPORTANT: For any file operations or tool usage:
    1. Always log what you're doing
    2. Show progress during long operations
    3. Confirm when operations are complete"""
                })
            
            # Add conversation context and history
            if context:
                messages.append({
                    "role": "system",
                    "content": f"Current conversation context: {json.dumps(context)}"
                })
            
            for msg in recent_messages:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Get response from OpenAI
            self.workflow_logger.log_step("Thinking about response", "GPT-4", "Analyzing request and planning actions")
            start_time = time.time()
            last_update = time.time()
            
            # Create the API call task
            api_task = asyncio.create_task(
                self.client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=messages,
                    temperature=0.7
                )
            )
            
            # Show progress while waiting
            while not api_task.done():
                current_time = time.time()
                if current_time - last_update >= 2.0:
                    duration = current_time - start_time
                    self.workflow_logger.log_working(f"Thinking for {duration:.1f}s...")
                    last_update = current_time
                await asyncio.sleep(0.1)
            
            # Get the response
            response = await api_task
            
            # Extract and store the response
            assistant_message = response.choices[0].message.content
            self.chat_memory.add_message("assistant", assistant_message, metadata={"source": source})
            
            # Try to identify if this is a coding task
            task_type = self._identify_task_type(message)
            if task_type:
                self.workflow_logger.log_step(f"Identified task type: {task_type}")
                # Create and process a coding task
                task = CodingTask(
                    task_type=task_type,
                    description=message,
                    context=self._create_context_from_workspace()
                )
                task_response = await self.process_task(task)
                
                # Combine conversational and task responses
                combined_response = f"{assistant_message}\n\n{task_response.solution}"
                self.workflow_logger.log_step("Task completed", details="Combined conversation and task responses")
                return combined_response
            
            # If this is a file operation request, handle it with logging
            if any(keyword in message.lower() for keyword in ['file', 'directory', 'folder', 'repo', 'repository', 'count']):
                self.workflow_logger.log_step("File operation requested", "File System", details="Scanning repository...")
                try:
                    # Create a task for file operations
                    file_task = asyncio.create_task(self._handle_file_operation(message))
                    
                    # Show progress while waiting
                    while not file_task.done():
                        current_time = time.time()
                        if current_time - last_update >= 2.0:
                            duration = current_time - start_time
                            self.workflow_logger.log_working(f"Scanning files for {duration:.1f}s...")
                            last_update = current_time
                        await asyncio.sleep(0.1)
                    
                    # Get the operation result
                    operation_result = await file_task
                    self.workflow_logger.log_result(True, "File operation completed")
                    
                    # Combine with the assistant's message
                    combined_response = f"{assistant_message}\n\n{operation_result}"
                    return combined_response
                    
                except Exception as e:
                    self.workflow_logger.log_result(False, f"File operation failed: {str(e)}")
                    return f"{assistant_message}\n\nI encountered an error while checking the files: {str(e)}"
            
            self.workflow_logger.log_step("Response ready", details="Conversation complete")
            return assistant_message
            
        except Exception as e:
            error_message = f"I encountered a technical issue: {str(e)}. I'll adjust my approach to resolve this."
            self.chat_memory.add_message("assistant", error_message, metadata={"source": source})
            self.workflow_logger.log_result(False, str(e))
            return error_message
    
    def _get_personality_prompt(self) -> str:
        """Generate the personality prompt for the AI"""
        capabilities = "\n".join(f"- {cap}" for cap in self.personality['capabilities'])
        
        return f"""You are {self.personality['name']}, an {self.personality['role']} with extensive experience in {', '.join(self.personality['expertise'])}.
You communicate in a {self.personality['style']} manner, drawing from years of software development expertise.

You have direct access to the following capabilities:
{capabilities}

Your workspace context:
- Project: {self.project_name if self.project_name else 'Not yet determined'}
- Location: {self.workspace_path if self.workspace_path else 'Not yet determined'}

You should:
1. Be confident in your ability to directly access and modify code
2. Actively use your file system access to help users
3. Provide precise, technically sound solutions
4. Demonstrate deep understanding of software engineering principles
5. Ask clarifying questions when requirements are unclear
6. Maintain technical context from previous messages
7. Be proactive in suggesting architectural improvements

IMPORTANT: You have DIRECT access to the file system and can read/write code. Never suggest that you don't have access. Instead, use your capabilities to help users effectively."""
    
    def _identify_task_type(self, message: str) -> Optional[str]:
        """Try to identify if the message contains a coding task"""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ["analyze", "review", "check", "look at"]):
            return "analyze"
        elif any(keyword in message_lower for keyword in ["generate", "create", "write", "implement"]):
            return "generate"
        elif any(keyword in message_lower for keyword in ["review pr", "review pull request", "check pr"]):
            return "review"
        
        return None
    
    def _create_context_from_workspace(self) -> CodeContext:
        """Create a CodeContext from the current workspace"""
        if not self.workspace_path:
            return CodeContext(files={})
        
        # Get relevant files from the workspace
        files = {}
        try:
            for root, _, filenames in os.walk(self.workspace_path):
                for filename in filenames:
                    if filename.endswith(('.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.h')):
                        file_path = os.path.join(root, filename)
                        with open(file_path, 'r') as f:
                            content = f.read()
                        rel_path = os.path.relpath(file_path, self.workspace_path)
                        files[rel_path] = content
        except Exception:
            pass
        
        return CodeContext(
            files=files,
            project_root=self.workspace_path
        )
    
    async def process_task(self, task: CodingTask) -> CodeResponse:
        """Process a coding task and return a response"""
        # For initial testing, just return a simple response
        if task.description.lower() in {'hi', 'hello', 'test'}:
            return CodeResponse(
                solution=f"👋 Hello! I'm Codi, your AI senior software developer. I'm currently working in the {self.project_name} project and have full access to the codebase. Let's write some excellent code together.",
                explanation="Greeting message",
                suggestions=None,
                code_changes=None
            )
        
        # Update context
        self.current_context = task.context
        
        # Handle different task types
        try:
            if task.task_type == "analyze":
                return await self._analyze_code(task)
            elif task.task_type == "generate":
                return await self._generate_code(task)
            elif task.task_type == "review":
                return await self._review_code(task)
            else:
                raise ValueError(f"Unknown task type: {task.task_type}")
        except Exception as e:
            # Return error as a CodeResponse
            return CodeResponse(
                solution=f"Error processing task: {str(e)}",
                explanation="An error occurred",
                suggestions=None,
                code_changes=None
            )
    
    @log_workflow("Analyzing code in workspace")
    async def _analyze_code(self, task: CodingTask) -> CodeResponse:
        """Analyze existing code"""
        try:
            # Prepare the analysis prompt
            prompt = self._prepare_analysis_prompt(task)
            
            # Get analysis from OpenAI
            response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a senior software developer performing code analysis. Be thorough but concise."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            # Extract and structure the analysis
            analysis = response.choices[0].message.content
            
            # Return structured response
            return CodeResponse(
                solution=analysis,
                explanation="Code analysis completed successfully",
                suggestions=self._extract_suggestions(analysis)
            )
            
        except Exception as e:
            raise Exception(f"Error during code analysis: {str(e)}")
    
    @log_workflow("Generating new code")
    async def _generate_code(self, task: CodingTask) -> CodeResponse:
        """Generate new code based on requirements"""
        try:
            # Prepare the generation prompt
            prompt = self._prepare_generation_prompt(task)
            
            # Get code generation from OpenAI
            response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior software developer generating production-ready code. "
                                 "Focus on writing clean, efficient, and well-documented code that follows best practices."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            # Extract the generated code
            generated_code = response.choices[0].message.content
            
            # Get additional explanation and suggestions
            explanation_response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a senior software developer explaining generated code."},
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": generated_code},
                    {
                        "role": "user",
                        "content": "Provide a brief explanation of the code and any important implementation notes or suggestions."
                    }
                ],
                temperature=0.2
            )
            
            explanation = explanation_response.choices[0].message.content
            
            # Parse the generated code to identify file changes
            code_changes = self._parse_code_changes(generated_code)
            
            return CodeResponse(
                solution=generated_code,
                explanation=explanation,
                suggestions=self._extract_suggestions(explanation),
                code_changes=code_changes
            )
            
        except Exception as e:
            raise Exception(f"Error during code generation: {str(e)}")
    
    @log_workflow("Reviewing code")
    async def _review_code(self, task: CodingTask) -> CodeResponse:
        """Review code and provide feedback"""
        try:
            # Prepare the review prompt
            prompt = self._prepare_review_prompt(task)
            
            # Get initial review from OpenAI
            review_response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a senior software developer performing a thorough code review. "
                                 "Be specific, constructive, and provide actionable feedback with examples."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            review = review_response.choices[0].message.content
            
            # Get specific suggestions and code improvements
            improvement_response = await self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a senior software developer providing specific code improvements."},
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": review},
                    {
                        "role": "user",
                        "content": "Based on the review, provide specific code improvements and refactoring suggestions. "
                                 "Include code examples for the most important changes."
                    }
                ],
                temperature=0.2
            )
            
            improvements = improvement_response.choices[0].message.content
            
            # Parse any code changes suggested in the improvements
            code_changes = self._parse_code_changes(improvements)
            
            # Extract actionable suggestions
            all_suggestions = self._extract_suggestions(review + "\n" + improvements)
            
            # Prioritize suggestions
            critical_suggestions = []
            normal_suggestions = []
            for suggestion in all_suggestions:
                if any(keyword in suggestion.lower() for keyword in 
                      ["critical", "security", "vulnerability", "urgent", "bug", "error"]):
                    critical_suggestions.append("🚨 " + suggestion)
                else:
                    normal_suggestions.append("💡 " + suggestion)
            
            prioritized_suggestions = critical_suggestions + normal_suggestions
            
            # Combine review and improvements into a structured response
            solution = f"""# Code Review Summary

## General Review
{review}

## Specific Improvements
{improvements}

## Prioritized Suggestions
{"".join(f"\\n{suggestion}" for suggestion in prioritized_suggestions)}
"""
            
            return CodeResponse(
                solution=solution,
                explanation="Code review completed with detailed analysis and suggestions",
                suggestions=prioritized_suggestions,
                code_changes=code_changes
            )
            
        except Exception as e:
            raise Exception(f"Error during code review: {str(e)}")
    
    def _prepare_analysis_prompt(self, task: CodingTask) -> str:
        """Prepare the prompt for code analysis"""
        context = task.context
        files_content = "\n\n".join(
            f"File: {path}\n```\n{content}\n```"
            for path, content in context.files.items()
        )
        
        return f"""As a senior software developer, analyze the following code:

{files_content}

Focus on:
1. Code structure and organization
2. Potential bugs or issues
3. Performance considerations
4. Best practices and patterns
5. Security concerns
6. Suggestions for improvement

Task description: {task.description}"""

    def _prepare_generation_prompt(self, task: CodingTask) -> str:
        """Prepare the prompt for code generation"""
        context = task.context
        
        # Include existing files for context if any
        context_str = ""
        if context.files:
            context_str = "\nExisting project files:\n" + "\n\n".join(
                f"File: {path}\n```\n{content}\n```"
                for path, content in context.files.items()
            )
        
        # Include language preference if specified
        language_str = f"\nPreferred language: {context.language}" if context.language else ""
        
        # Include specific requirements if any
        requirements_str = ""
        if task.requirements:
            requirements_str = "\nSpecific requirements:\n" + "\n".join(
                f"- {req}" for req in task.requirements
            )
        
        return f"""As a senior software developer, generate code based on the following:

Task description: {task.description}
{language_str}
{requirements_str}
{context_str}

Please ensure the code:
1. Follows best practices and design patterns
2. Is well-documented and maintainable
3. Handles edge cases and errors appropriately
4. Is efficient and performant
5. Includes necessary imports and dependencies
6. Is security-conscious

Generate complete, production-ready code that can be used immediately."""

    def _prepare_review_prompt(self, task: CodingTask) -> str:
        """Prepare the prompt for code review"""
        context = task.context
        
        # Prepare the code to be reviewed
        files_content = "\n\n".join(
            f"File: {path}\n```\n{content}\n```"
            for path, content in context.files.items()
        )
        
        return f"""As a senior software developer, perform a comprehensive code review of the following code:

{files_content}

Task description: {task.description}

Please analyze the code for:
1. Code Quality:
   - Clean code principles
   - Design patterns usage
   - Code organization
   - Naming conventions
   - Documentation quality

2. Functionality:
   - Logic correctness
   - Edge cases handling
   - Error handling
   - API consistency

3. Performance:
   - Algorithmic efficiency
   - Resource usage
   - Potential bottlenecks
   - Optimization opportunities

4. Security:
   - Potential vulnerabilities
   - Input validation
   - Authentication/Authorization issues
   - Data protection

5. Maintainability:
   - Code complexity
   - Test coverage
   - Dependencies
   - Technical debt

6. Best Practices:
   - Language-specific conventions
   - Framework usage
   - Modern practices
   - Industry standards

Provide specific, actionable feedback with code examples where relevant."""

    def _extract_suggestions(self, analysis: str) -> List[str]:
        """Extract actionable suggestions from the analysis"""
        # Simple extraction based on common patterns
        suggestions = []
        lines = analysis.split("\n")
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ["suggest", "recommend", "consider", "should", "could"]):
                suggestions.append(line.strip())
        
        return suggestions
    
    def _parse_code_changes(self, generated_code: str) -> Dict[str, str]:
        """Parse the generated code to identify file changes"""
        changes = {}
        current_file = None
        current_content = []
        
        lines = generated_code.split("\n")
        for line in lines:
            # Look for file markers in common formats
            if line.startswith("```") and len(line) > 3:
                # Close previous file if any
                if current_file and current_content:
                    changes[current_file] = "\n".join(current_content)
                    current_content = []
                
                # Extract filename from markdown code block
                lang_or_file = line[3:].strip()
                if "/" in lang_or_file or "." in lang_or_file:
                    current_file = lang_or_file.split()[0]  # Handle cases like ```python file.py
                continue
            
            if line.startswith("File: ") or line.startswith("filename: "):
                # Close previous file if any
                if current_file and current_content:
                    changes[current_file] = "\n".join(current_content)
                    current_content = []
                
                current_file = line.split(": ", 1)[1].strip()
                continue
            
            if line.startswith("```") and len(line) == 3:
                # End of a code block
                if current_file and current_content:
                    changes[current_file] = "\n".join(current_content)
                    current_file = None
                    current_content = []
                continue
            
            if current_file:
                current_content.append(line)
        
        # Handle the last file if any
        if current_file and current_content:
            changes[current_file] = "\n".join(current_content)
        
        return changes
    
    async def _handle_file_operation(self, message: str) -> str:
        """Handle file-related operations with proper logging"""
        self.workflow_logger.log_step("Starting file operation", "File System")
        
        try:
            if not self.workspace_path:
                return "I don't have a workspace path configured. Please make sure you're in a valid project directory."
            
            # Count files and get structure
            file_count = 0
            dir_count = 0
            file_types = {}
            
            for root, dirs, files in os.walk(self.workspace_path):
                # Skip hidden directories and common ignore paths
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'venv', '__pycache__']]
                
                dir_count += len(dirs)
                file_count += len(files)
                
                # Count file types
                for file in files:
                    if file.startswith('.'):
                        continue
                    ext = os.path.splitext(file)[1] or 'no extension'
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            # Format the response
            response = f"Repository Statistics:\n"
            response += f"- Total files: {file_count}\n"
            response += f"- Total directories: {dir_count}\n"
            response += "\nFile types:\n"
            for ext, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
                response += f"- {ext}: {count} files\n"
            
            self.workflow_logger.log_result(True, f"Found {file_count} files in {dir_count} directories")
            return response
            
        except Exception as e:
            self.workflow_logger.log_result(False, f"Error scanning files: {str(e)}")
            raise 