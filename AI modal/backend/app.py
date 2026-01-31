"""
AI PDF Question Answering System - FastAPI Backend
Accepts PDF URLs and multiple questions, returns answers in strict JSON format
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import List, Dict, Any
import logging

from pdf_processor import PDFProcessor
from ai_handler import AIHandler
from chat_handler import ChatHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI PDF Question Answering System",
    description="Process PDF documents and answer questions using DeepSeek AI model",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files to serve the frontend (e.g., e:\AI modal)
# We mount the parent directory of 'backend' to serve chatbot.html
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=parent_dir), name="static")

# Initialize processors
pdf_processor = PDFProcessor(max_size_mb=50, timeout=30)
ai_handler = AIHandler(model_name="deepseek-r1:1.5b")
chat_handler = ChatHandler(model_name="deepseek-r1:1.5b")


# Request/Response Models
class QuestionRequest(BaseModel):
    """Request model for PDF question answering"""
    pdf_url: str = Field(..., description="URL of the PDF document to process")
    questions: List[str] = Field(..., min_items=1, max_items=20, description="List of questions (1-20)")
    
    @validator('pdf_url')
    def validate_pdf_url(cls, v):
        """Validate PDF URL format"""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        if not any(v.lower().endswith(ext) for ext in ['.pdf', '.PDF']) and 'pdf' not in v.lower():
            logger.warning(f"URL may not point to a PDF: {v}")
        return v
    
    @validator('questions')
    def validate_questions(cls, v):
        """Validate questions list"""
        if not v:
            raise ValueError('At least one question is required')
        
        # Remove empty questions
        v = [q.strip() for q in v if q.strip()]
        
        if not v:
            raise ValueError('Questions cannot be empty')
        
        if len(v) > 20:
            raise ValueError('Maximum 20 questions allowed')
        
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "pdf_url": "https://example.com/document.pdf",
                "questions": [
                    "What is the main topic of this document?",
                    "Who are the authors?",
                    "What are the key findings?"
                ]
            }
        }


class AnswerResponse(BaseModel):
    """Response model with strict JSON format"""
    answers: List[str]
    
    class Config:
        schema_extra = {
            "example": {
                "answers": [
                    "The document discusses...",
                    "The key findings are..."
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    error_type: str
    details: str = None


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI PDF Question Answering System",
        "version": "1.0.0",
        "endpoints": {
            "POST /aibattle": "Submit PDF URL and questions (Official Endpoint)",
            "GET /api/health": "Check system health",
            "GET /docs": "API documentation"
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    model_available = ai_handler.verify_model()
    
    return {
        "status": "healthy" if model_available else "degraded",
        "ollama_connected": model_available,
        "model": ai_handler.model_name,
        "model_available": model_available,
        "message": "System operational" if model_available else "DeepSeek model not found in Ollama"
    }


@app.post("/aibattle", response_model=AnswerResponse)
async def answer_questions(request: QuestionRequest):
    """
    Process PDF and answer questions
    
    Args:
        request: QuestionRequest with pdf_url and questions
        
    Returns:
        AnswerResponse with strict JSON format containing answers
        
    Raises:
        HTTPException: If processing fails
    """
    pdf_path = None
    
    try:
        logger.info(f"Processing PDF from URL: {request.pdf_url}")
        logger.info(f"Number of questions: {len(request.questions)}")
        
        # Step 1: Verify model availability
        if not ai_handler.verify_model():
            logger.warning("DeepSeek model verification failed - attempting to proceed anyway")
            # We don't raise error here to allow fallback strategies if implemented
        
        # Step 2: Download and process PDF
        try:
            pdf_path, pdf_text = pdf_processor.process_pdf_url(request.pdf_url)
            logger.info(f"PDF processed successfully. Text length: {len(pdf_text)} characters")
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process PDF: {str(e)}"
            )
        
        # Step 3: Answer questions using AI
        try:
            result = ai_handler.answer_questions(pdf_text, request.questions)
            logger.info(f"Questions answered successfully")
            return result
            
        except Exception as e:
            logger.error(f"AI processing error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": "Failed to generate answers",
                    "error_type": "AIProcessingError",
                    "details": str(e)
                }
            )
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error",
                "error_type": "UnexpectedError",
                "details": str(e)
            }
        )
    
    finally:
        # Cleanup: Delete temporary PDF file
        if pdf_path:
            pdf_processor.cleanup(pdf_path)
            logger.info("Temporary PDF file cleaned up")


@app.get("/api/models")
async def list_models():
    """List available Ollama models"""
    try:
        models = ai_handler.client.list()
        return {
            "success": True,
            "models": models.get('models', []),
            "current_model": ai_handler.model_name
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to connect to Ollama"
        }


# Chat Endpoints
class ChatRequest(BaseModel):
    """Request model for chat"""
    session_id: str = Field(default="default", description="Session ID for conversation")
    message: str = Field(..., min_length=1, description="User message")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "user123",
                "message": "Hello! How are you?"
            }
        }


class ChatPDFRequest(BaseModel):
    """Request model for chat with PDF"""
    session_id: str = Field(default="default", description="Session ID")
    pdf_url: str = Field(..., description="PDF URL to load as context")
    message: str = Field(..., min_length=1, description="User message")
    
    class Config:
        schema_extra = {
            "example": {
                "session_id": "user123",
                "pdf_url": "https://example.com/document.pdf",
                "message": "What is this document about?"
            }
        }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    General chat endpoint - no PDF required
    
    Args:
        request: ChatRequest with session_id and message
        
    Returns:
        AI response with conversation context
    """
    try:
        result = chat_handler.chat(
            session_id=request.session_id,
            user_message=request.message,
            use_pdf_context=True  # Use PDF if already loaded
        )
        return result
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Chat processing failed",
                "details": str(e)
            }
        )


@app.post("/api/chat/pdf")
async def chat_with_pdf(request: ChatPDFRequest):
    """
    Chat with PDF context
    
    Args:
        request: ChatPDFRequest with session_id, pdf_url, and message
        
    Returns:
        AI response with PDF context
    """
    try:
        # Get or create session
        session = chat_handler.get_or_create_session(request.session_id)
        
        # Load PDF if not already loaded or if URL changed
        if session.pdf_url != request.pdf_url:
            logger.info(f"Loading PDF: {request.pdf_url}")
            pdf_path, pdf_text = pdf_processor.process_pdf_url(request.pdf_url)
            session.set_pdf_context(request.pdf_url, pdf_text)
            pdf_processor.cleanup(pdf_path)
            logger.info(f"PDF loaded successfully")
        
        # Process chat message
        result = chat_handler.chat(
            session_id=request.session_id,
            user_message=request.message,
            use_pdf_context=True
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": str(e),
                "error_type": "PDFProcessingError"
            }
        )
    except Exception as e:
        logger.error(f"Chat with PDF error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Chat processing failed",
                "details": str(e)
            }
        )


@app.get("/api/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Get conversation history for a session
    
    Args:
        session_id: Session identifier
        
    Returns:
        List of messages in the conversation
    """
    history = chat_handler.get_session_history(session_id)
    
    if history is None:
        return {
            "success": False,
            "error": "Session not found",
            "session_id": session_id
        }
    
    return {
        "success": True,
        "session_id": session_id,
        "messages": history,
        "message_count": len(history)
    }


@app.delete("/api/chat/session/{session_id}")
async def clear_chat_session(session_id: str):
    """
    Clear a chat session
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success status
    """
    success = chat_handler.clear_session(session_id)
    
    return {
        "success": success,
        "session_id": session_id,
        "message": "Session cleared" if success else "Session not found"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
