# app/schemas/course.py - Fixed for Pydantic v2
"""
CorePath Impact Course Schemas
Pydantic v2 compatible models for course system
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, field_validator, Field


# Base course schemas
class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    short_description: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    instructor: Optional[str] = Field(None, max_length=200)
    instructor_bio: Optional[str] = None
    duration_hours: Optional[float] = Field(None, ge=0)
    difficulty_level: str = Field("beginner", pattern="^(beginner|intermediate|advanced)$")
    age_group: Optional[str] = None
    price: float = Field(0.0, ge=0)
    compare_at_price: Optional[float] = Field(None, ge=0)
    is_free: bool = False


class CourseCreate(CourseBase):
    """Schema for creating a course"""
    objectives: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('compare_at_price')
    @classmethod
    def validate_compare_at_price(cls, v, info):
        if v is not None and 'price' in info.data and v <= info.data['price']:
            raise ValueError('compare_at_price must be greater than price')
        return v


class CourseUpdate(BaseModel):
    """Schema for updating a course"""
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    short_description: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    instructor: Optional[str] = Field(None, max_length=200)
    instructor_bio: Optional[str] = None
    duration_hours: Optional[float] = Field(None, ge=0)
    difficulty_level: Optional[str] = Field(None, pattern="^(beginner|intermediate|advanced)$")
    age_group: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    compare_at_price: Optional[float] = Field(None, ge=0)
    is_free: Optional[bool] = None
    is_featured: Optional[bool] = None
    certificate_available: Optional[bool] = None
    status: Optional[str] = None


class CourseResponse(CourseBase):
    """Schema for course response"""
    id: int
    slug: str
    status: str
    is_featured: bool
    requires_enrollment: bool
    certificate_available: bool
    total_lessons: int
    total_modules: int
    enrollment_count: int
    completion_count: int
    rating_average: float
    rating_count: int
    completion_rate: float
    discount_percentage: float
    thumbnail_url: Optional[str] = None
    intro_video_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# Module schemas
class CourseModuleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    description: Optional[str] = None
    sort_order: int = Field(0, ge=0)
    is_published: bool = True


class CourseModuleCreate(CourseModuleBase):
    course_id: int


class CourseModuleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    description: Optional[str] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_published: Optional[bool] = None


class CourseModuleResponse(CourseModuleBase):
    id: int
    course_id: int
    duration_minutes: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Lesson schemas
class CourseLessonBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    content: Optional[str] = None
    lesson_type: str = Field("text", pattern="^(text|video|quiz|download|interactive)$")
    sort_order: int = Field(0, ge=0)
    is_published: bool = True
    is_preview: bool = False


class CourseLessonCreate(CourseLessonBase):
    module_id: int
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    attachments: Optional[List[Dict[str, Any]]] = None
    quiz_data: Optional[Dict[str, Any]] = None
    passing_score: Optional[int] = Field(None, ge=0, le=100)


class CourseLessonUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    content: Optional[str] = None
    lesson_type: Optional[str] = Field(None, pattern="^(text|video|quiz|download|interactive)$")
    sort_order: Optional[int] = Field(None, ge=0)
    is_published: Optional[bool] = None
    is_preview: Optional[bool] = None
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    attachments: Optional[List[Dict[str, Any]]] = None
    quiz_data: Optional[Dict[str, Any]] = None
    passing_score: Optional[int] = Field(None, ge=0, le=100)


class CourseLessonResponse(CourseLessonBase):
    id: int
    module_id: int
    video_url: Optional[str] = None
    duration_minutes: Optional[int] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    quiz_data: Optional[Dict[str, Any]] = None
    passing_score: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Enrollment schemas
class CourseEnrollmentCreate(BaseModel):
    course_id: int


class CourseEnrollmentResponse(BaseModel):
    id: int
    course_id: int
    user_id: int
    status: str
    progress_percentage: float
    completed_lessons: int
    total_time_spent: int
    last_accessed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    certificate_issued: bool
    certificate_url: Optional[str] = None
    enrolled_at: datetime
    
    model_config = {"from_attributes": True}


# Progress schemas
class LessonProgressUpdate(BaseModel):
    completion_percentage: Optional[float] = Field(None, ge=0, le=100)
    time_spent: Optional[int] = Field(None, ge=0)
    quiz_score: Optional[float] = Field(None, ge=0, le=100)
    quiz_data: Optional[Dict[str, Any]] = None


class LessonProgressResponse(BaseModel):
    id: int
    enrollment_id: int
    lesson_id: int
    is_completed: bool
    completion_percentage: float
    time_spent: int
    quiz_score: Optional[float] = None
    quiz_attempts: int
    quiz_passed: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    last_accessed: datetime
    
    model_config = {"from_attributes": True}


# Review schemas
class CourseReviewCreate(BaseModel):
    course_id: int
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None


class CourseReviewResponse(BaseModel):
    id: int
    course_id: int
    user_id: int
    rating: int
    title: Optional[str] = None
    content: Optional[str] = None
    is_approved: bool
    is_verified_completion: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# Course with details (for detailed view)
class CourseDetailResponse(CourseResponse):
    modules: List[CourseModuleResponse] = []
    recent_reviews: List[CourseReviewResponse] = []
    objectives: Optional[List[str]] = None
    tags: Optional[List[str]] = None


# Search and filter schemas
class CourseSearchFilters(BaseModel):
    q: Optional[str] = None  # Search query
    difficulty_level: Optional[str] = None
    age_group: Optional[str] = None
    is_free: Optional[bool] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    min_rating: Optional[float] = Field(None, ge=1, le=5)
    is_featured: Optional[bool] = None
    instructor: Optional[str] = None
    tags: Optional[List[str]] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    
    @field_validator('sort_by')
    @classmethod
    def validate_sort_by(cls, v):
        allowed_fields = [
            'created_at', 'title', 'price', 'rating_average', 
            'enrollment_count', 'duration_hours'
        ]
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of: {", ".join(allowed_fields)}')
        return v
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v


# Analytics schemas
class CourseAnalytics(BaseModel):
    total_enrollments: int
    completed_enrollments: int
    completion_rate: float
    average_rating: float
    total_reviews: int
    average_time_to_complete: Optional[float] = None  # in hours
    enrollment_trend: List[Dict[str, Any]]
    popular_lessons: List[Dict[str, Any]]


class UserCourseAnalytics(BaseModel):
    total_enrolled: int
    total_completed: int
    total_hours_learned: float
    certificates_earned: int
    favorite_topics: List[str]
    recent_activity: List[Dict[str, Any]]


# Certificate schemas
class CourseCertificateResponse(BaseModel):
    id: int
    enrollment_id: int
    certificate_number: str
    certificate_url: Optional[str] = None
    verification_code: str
    is_valid: bool
    issued_at: datetime
    expires_at: Optional[datetime] = None
    is_expired: bool
    
    model_config = {"from_attributes": True}


# Quiz schemas (for lesson quizzes)
class QuizQuestion(BaseModel):
    question: str
    type: str = Field(..., pattern="^(multiple_choice|true_false|short_answer)$")
    options: Optional[List[str]] = None  # For multiple choice
    correct_answer: str
    explanation: Optional[str] = None
    points: int = Field(1, ge=1)


class QuizCreate(BaseModel):
    title: str
    description: Optional[str] = None
    questions: List[QuizQuestion] = Field(..., min_length=1)
    time_limit: Optional[int] = None  # in minutes
    passing_score: int = Field(70, ge=0, le=100)
    allow_retakes: bool = True
    max_attempts: Optional[int] = Field(None, ge=1)


class QuizSubmission(BaseModel):
    lesson_id: int
    answers: Dict[str, str]  # question_id: answer
    time_taken: Optional[int] = None  # in seconds


class QuizResult(BaseModel):
    score: float
    passed: bool
    correct_answers: int
    total_questions: int
    time_taken: int
    attempt_number: int
    feedback: Dict[str, Any]