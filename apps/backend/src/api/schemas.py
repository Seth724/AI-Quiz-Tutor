"""
Pydantic schemas for API requests/responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============================================================================
# Document Schemas
# ============================================================================

class DocumentUploadResponse(BaseModel):
    """Response after uploading a document"""
    document_id: str
    title: str
    status: str  # "processing", "ready", "failed"
    message: str
    chunks_count: Optional[int] = None


class DocumentStatusResponse(BaseModel):
    """Async document processing status"""
    document_id: str
    status: str
    message: str
    chunks_count: Optional[int] = None
    processing_error: Optional[str] = None


class DocumentInfo(BaseModel):
    """Document information"""
    document_id: str
    title: str
    file_type: str
    supabase_url: Optional[str] = None
    pages: int = 0
    created_at: datetime
    status: str
    chunks_count: int = 0
    quizzes_generated: int = 0
    attempts_count: int = 0
    average_score: float = 0.0


class DocumentListResponse(BaseModel):
    """List of user's documents"""
    documents: List[DocumentInfo]
    total: int


# ============================================================================
# Quiz Schemas
# ============================================================================

class QuizGenerateRequest(BaseModel):
    """Request to generate a quiz"""
    document_id: str
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    question_type: str = Field(default="multiple_choice", pattern="^(multiple_choice|true_false|short_answer)$")


class QuizQuestion(BaseModel):
    """Single quiz question"""
    id: str
    question: str
    options: Optional[List[str]] = None
    correct_answer: str
    explanation: str
    topic: Optional[str] = None


class QuizGenerateResponse(BaseModel):
    """Generated quiz"""
    quiz_id: str
    document_id: str
    questions: List[QuizQuestion]
    total_questions: int
    created_at: datetime


class QuizSubmitRequest(BaseModel):
    """Submit quiz answers"""
    quiz_id: str
    answers: Dict[str, str]  # question_id -> answer
    user_id: Optional[str] = None


class QuizResult(BaseModel):
    """Quiz results"""
    quiz_id: str
    score: float  # 0.0 to 1.0
    correct_count: int
    total_questions: int
    time_taken_seconds: Optional[int] = None
    weak_areas: List[Dict[str, Any]]
    recommendations: List[str]


# ============================================================================
# Progress Schemas
# ============================================================================

class ProgressResponse(BaseModel):
    """User progress"""
    total_quizzes: int
    average_score: float
    quizzes_completed: int
    weak_areas: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    improvement_trend: str  # "improving", "stable", "needs_work"


class WeakArea(BaseModel):
    """Weak area identification"""
    topic: str
    accuracy: float
    attempts: int
    last_studied: Optional[datetime]
    priority: str  # "high", "medium", "low"


# ============================================================================
# Chat Schemas
# ============================================================================

class ChatMessage(BaseModel):
    """Chat message"""
    role: str  # "user", "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat request"""
    message: str
    document_id: Optional[str] = None  # Optional: limit to specific document
    user_id: Optional[str] = None
    conversation_history: Optional[List[ChatMessage]] = None


class ChatbotProxyRequest(BaseModel):
    """External chatbot request"""
    user_id: str
    message: str
    document_id: Optional[str] = None


class StudyPlanCreateRequest(BaseModel):
    """Create study plan / to-do item"""
    user_id: str
    title: str
    target_date: str  # ISO date string from frontend
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    notes: Optional[str] = None
    reminder_days_before: int = Field(default=2, ge=0, le=30)
    user_email: Optional[str] = None


class StudyPlanStatusRequest(BaseModel):
    """Update study plan status"""
    user_id: str
    status: str = Field(pattern="^(pending|done|in_progress|todo)$")


class StudyPlanGenerateRequest(BaseModel):
    """Generate a timetable for existing not-done plans"""
    user_id: str
    plan_ids: List[str]
    available_days: List[str]  # ["Monday", "Tuesday", etc.]
    study_days: int = Field(ge=1, le=120)  # total timetable entries to generate
    hours_per_day: float = Field(ge=0.5, le=12)
    preferred_start_time: Optional[str] = "09:00"  # HH:MM
    exam_date: str  # ISO date string (when exam is scheduled)
    learning_style: Optional[str] = "visual"  # visual, auditory, reading, kinesthetic
    difficulty_level: Optional[str] = "intermediate"  # beginner, intermediate, advanced


class AttemptInfo(BaseModel):
    """Saved quiz attempt"""
    attempt_id: str
    quiz_id: str
    document_id: Optional[str] = None
    user_id: str
    score: float
    correct_count: int
    total_questions: int
    percentage: str
    completed_at: datetime


class ChatResponse(BaseModel):
    """Chat response"""
    response: str
    sources: List[Dict[str, Any]]  # Retrieved documents
    confidence: float


class VisionResponse(BaseModel):
    """Vision model image analysis response"""
    content: str  # Image description or answer
    model: str  # "claude" or "blip"
    success: bool
    error: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None  # Token usage for claude


# ============================================================================
# Reminder Schemas
# ============================================================================

class ReminderCreateRequest(BaseModel):
    """Create review reminder"""
    topic: str
    review_after_hours: int = 24


class ReminderResponse(BaseModel):
    """Reminder information"""
    reminder_id: str
    topic: str
    scheduled_for: datetime
    status: str  # "pending", "sent", "completed"


# ============================================================================
# Error Response
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    status_code: int
