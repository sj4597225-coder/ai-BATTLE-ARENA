"""
Chat Handler Module
Manages general AI conversations with optional PDF context
"""
import ollama
from typing import List, Dict, Any, Optional
from datetime import datetime


class ChatSession:
    """Represents a chat session with conversation history"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: List[Dict[str, str]] = []
        self.pdf_context: Optional[str] = None
        self.pdf_url: Optional[str] = None
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_updated = datetime.now()
    
    def set_pdf_context(self, pdf_url: str, pdf_text: str):
        """Set PDF context for this session"""
        self.pdf_url = pdf_url
        self.pdf_context = pdf_text
        self.last_updated = datetime.now()
    
    def get_conversation_context(self, max_messages: int = 10) -> str:
        """Get recent conversation as context string"""
        recent_messages = self.messages[-max_messages:]
        context = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in recent_messages
        ])
        return context


class ChatHandler:
    """Handles AI chat conversations with DeepSeek"""
    
    def __init__(self, model_name: str = "deepseek-r1:1.5b"):
        self.model_name = model_name
        self.client = ollama.Client()
        self.sessions: Dict[str, ChatSession] = {}
    
    def create_session(self, session_id: str) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(session_id)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get existing session or None"""
        return self.sessions.get(session_id)
    
    def get_or_create_session(self, session_id: str) -> ChatSession:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            return self.create_session(session_id)
        return self.sessions[session_id]
    
    def chat(
        self, 
        session_id: str, 
        user_message: str,
        use_pdf_context: bool = True
    ) -> Dict[str, Any]:
        """
        Process a chat message and return AI response
        
        Args:
            session_id: Unique session identifier
            user_message: User's message
            use_pdf_context: Whether to use PDF context if available
            
        Returns:
            Response dictionary with message and metadata
        """
        session = self.get_or_create_session(session_id)
        
        # Add user message to history
        session.add_message("user", user_message)
        
        # Build prompt with context
        prompt = self._build_prompt(session, user_message, use_pdf_context)
        
        try:
            # Get AI response
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                options={
                    "temperature": 0.7,  # More creative for chat
                    "top_p": 0.9,
                    "num_predict": 500,
                }
            )
            
            ai_message = response['response'].strip()
            
            # Add AI response to history
            session.add_message("assistant", ai_message)
            
            return {
                "success": True,
                "message": ai_message,
                "session_id": session_id,
                "has_pdf_context": session.pdf_context is not None,
                "pdf_url": session.pdf_url,
                "conversation_length": len(session.messages)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Sorry, I encountered an error processing your message.",
                "session_id": session_id
            }
    
    def _build_prompt(
        self, 
        session: ChatSession, 
        current_message: str,
        use_pdf_context: bool
    ) -> str:
        """Build prompt with conversation history and optional PDF context"""
        
        prompt_parts = []
        
        # System instruction
        prompt_parts.append(
            "You are a helpful AI assistant. Provide clear, accurate, and friendly responses."
        )
        
        # Add PDF context if available and requested
        if use_pdf_context and session.pdf_context:
            # Truncate PDF context if too long
            pdf_context = session.pdf_context[:10000]
            prompt_parts.append(
                f"\n\nYou have access to the following document:\n"
                f"Document URL: {session.pdf_url}\n"
                f"Document Content:\n{pdf_context}\n"
                f"Use this document to answer questions when relevant."
            )
        
        # Add conversation history (last 5 exchanges)
        if len(session.messages) > 1:
            recent_context = session.get_conversation_context(max_messages=10)
            if recent_context:
                prompt_parts.append(f"\n\nConversation History:\n{recent_context}")
        
        # Add current message
        prompt_parts.append(f"\n\nUser: {current_message}\n\nAssistant:")
        
        return "\n".join(prompt_parts)
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a chat session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_session_history(self, session_id: str) -> Optional[List[Dict[str, str]]]:
        """Get conversation history for a session"""
        session = self.get_session(session_id)
        if session:
            return session.messages
        return None
