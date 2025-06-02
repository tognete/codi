from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import json
import os

class Message(BaseModel):
    """Represents a single message in the conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class Conversation(BaseModel):
    """Represents an ongoing conversation with context"""
    messages: List[Message]
    context: Dict[str, Any]
    workspace_path: Optional[str] = None
    current_file: Optional[str] = None
    active_task: Optional[str] = None

class ChatMemory:
    """Manages conversation history and context"""
    def __init__(self, storage_path: str = ".codi/conversations"):
        self.storage_path = storage_path
        self.current_conversation: Optional[Conversation] = None
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Ensure the storage directory exists"""
        os.makedirs(self.storage_path, exist_ok=True)
    
    def start_conversation(self, workspace_path: Optional[str] = None) -> Conversation:
        """Start a new conversation"""
        self.current_conversation = Conversation(
            messages=[],
            context={},
            workspace_path=workspace_path
        )
        return self.current_conversation
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Add a message to the current conversation"""
        if not self.current_conversation:
            self.start_conversation()
        
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.current_conversation.messages.append(message)
        return message
    
    def get_conversation_context(self) -> Dict[str, Any]:
        """Get the current conversation context"""
        if not self.current_conversation:
            return {}
        return self.current_conversation.context
    
    def update_context(self, updates: Dict[str, Any]):
        """Update the conversation context"""
        if not self.current_conversation:
            self.start_conversation()
        self.current_conversation.context.update(updates)
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """Get the most recent messages"""
        if not self.current_conversation:
            return []
        return self.current_conversation.messages[-limit:]
    
    def save_conversation(self) -> str:
        """Save the current conversation to disk"""
        if not self.current_conversation:
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.json"
        filepath = os.path.join(self.storage_path, filename)
        
        with open(filepath, 'w') as f:
            json.dump(self.current_conversation.dict(), f, default=str)
        
        return filepath
    
    def load_conversation(self, filepath: str) -> Conversation:
        """Load a conversation from disk"""
        with open(filepath, 'r') as f:
            data = json.load(f)
            conversation = Conversation(**data)
            self.current_conversation = conversation
            return conversation
    
    def clear_conversation(self):
        """Clear the current conversation"""
        self.current_conversation = None 