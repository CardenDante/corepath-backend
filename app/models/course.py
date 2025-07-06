# app/models/course.py - Created by setup script
# app/models/course.py - Phase 5 Course Models
"""
CorePath Impact Course Models
Database models for courses and enrollments
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum

from app.core.database import Base


class CourseStatus(PyEnum):
    """Course status enumeration"""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class EnrollmentStatus(PyEnum):
    """Enrollment status enumeration"""
    ENROLLED = "enrolled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DROPPED = "dropped"


class Course(Base):
    """Main course model"""
    __tablename__ = "courses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False, index=True)
    slug = Column(String(320), unique=True, nullable=False, index=True)
    
    # Course content
    short_description = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    objectives = Column(JSON, nullable=True)  # Learning objectives
    
    # Course metadata
    instructor = Column(String(200), nullable=True)
    instructor_bio = Column(Text, nullable=True)
    duration_hours = Column(Float, nullable=True)
    difficulty_level = Column(String(50), default="beginner")  # beginner, intermediate, advanced
    age_group = Column(String(50), nullable=True)  # 4-9, 10-14, 15-18, all
    
    # Pricing
    price = Column(Float, nullable=False, default=0.0)
    compare_at_price = Column(Float, nullable=True)
    is_free = Column(Boolean, default=False)
    
    # Content and media
    thumbnail_url = Column(String(500), nullable=True)
    intro_video_url = Column(String(500), nullable=True)
    
    # Course structure
    total_lessons = Column(Integer, default=0)
    total_modules = Column(Integer, default=0)
    
    # Settings
    status = Column(String(20), default=CourseStatus.DRAFT.value)
    is_featured = Column(Boolean, default=False)
    requires_enrollment = Column(Boolean, default=True)
    certificate_available = Column(Boolean, default=False)
    
    # Analytics
    enrollment_count = Column(Integer, default=0)
    completion_count = Column(Integer, default=0)
    rating_average = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    
    # SEO
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(500), nullable=True)
    tags = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    modules = relationship("CourseModule", back_populates="course", cascade="all, delete-orphan", order_by="CourseModule.sort_order")
    enrollments = relationship("CourseEnrollment", back_populates="course", cascade="all, delete-orphan")
    reviews = relationship("CourseReview", back_populates="course", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Course(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    @property
    def completion_rate(self) -> float:
        """Calculate course completion rate"""
        if self.enrollment_count == 0:
            return 0.0
        return (self.completion_count / self.enrollment_count) * 100
    
    @property
    def discount_percentage(self) -> float:
        """Calculate discount percentage"""
        if self.compare_at_price and self.compare_at_price > self.price:
            return round(((self.compare_at_price - self.price) / self.compare_at_price) * 100, 2)
        return 0.0
    
    def increment_enrollment(self):
        """Increment enrollment count"""
        self.enrollment_count += 1
    
    def increment_completion(self):
        """Increment completion count"""
        self.completion_count += 1
    
    def update_rating(self, new_rating: float):
        """Update average rating with new rating"""
        total_points = self.rating_average * self.rating_count
        self.rating_count += 1
        self.rating_average = (total_points + new_rating) / self.rating_count


class CourseModule(Base):
    """Course module/chapter model"""
    __tablename__ = "course_modules"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    
    # Module details
    title = Column(String(300), nullable=False)
    description = Column(Text, nullable=True)
    
    # Organization
    sort_order = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    
    # Content
    duration_minutes = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="modules")
    lessons = relationship("CourseLesson", back_populates="module", cascade="all, delete-orphan", order_by="CourseLesson.sort_order")
    
    def __repr__(self):
        return f"<CourseModule(id={self.id}, title='{self.title}', course_id={self.course_id})>"


class CourseLesson(Base):
    """Course lesson model"""
    __tablename__ = "course_lessons"
    
    id = Column(Integer, primary_key=True, index=True)
    module_id = Column(Integer, ForeignKey("course_modules.id"), nullable=False)
    
    # Lesson details
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=True)
    lesson_type = Column(String(50), default="text")  # text, video, quiz, download, etc.
    
    # Organization
    sort_order = Column(Integer, default=0)
    is_published = Column(Boolean, default=True)
    is_preview = Column(Boolean, default=False)  # Can be viewed without enrollment
    
    # Content and media
    video_url = Column(String(500), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    attachments = Column(JSON, nullable=True)  # File attachments
    
    # Quiz data (if lesson_type is quiz)
    quiz_data = Column(JSON, nullable=True)
    passing_score = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    module = relationship("CourseModule", back_populates="lessons")
    progress = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CourseLesson(id={self.id}, title='{self.title}', type='{self.lesson_type}')>"


class CourseEnrollment(Base):
    """Course enrollment model"""
    __tablename__ = "course_enrollments"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Enrollment details
    status = Column(String(20), default=EnrollmentStatus.ENROLLED.value)
    progress_percentage = Column(Float, default=0.0)
    
    # Tracking
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    completed_lessons = Column(Integer, default=0)
    total_time_spent = Column(Integer, default=0)  # in minutes
    
    # Completion
    completed_at = Column(DateTime(timezone=True), nullable=True)
    certificate_issued = Column(Boolean, default=False)
    certificate_url = Column(String(500), nullable=True)
    
    # Timestamps
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="enrollments")
    user = relationship("User", backref="course_enrollments")
    progress = relationship("LessonProgress", back_populates="enrollment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<CourseEnrollment(id={self.id}, user_id={self.user_id}, course_id={self.course_id})>"
    
    @property
    def is_completed(self) -> bool:
        """Check if course is completed"""
        return self.status == EnrollmentStatus.COMPLETED.value
    
    def update_progress(self):
        """Recalculate progress percentage"""
        if not self.course.total_lessons:
            return
        
        self.progress_percentage = (self.completed_lessons / self.course.total_lessons) * 100
        
        # Mark as completed if all lessons are done
        if self.progress_percentage >= 100 and self.status != EnrollmentStatus.COMPLETED.value:
            self.status = EnrollmentStatus.COMPLETED.value
            self.completed_at = datetime.utcnow()


class LessonProgress(Base):
    """Individual lesson progress tracking"""
    __tablename__ = "lesson_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("course_enrollments.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("course_lessons.id"), nullable=False)
    
    # Progress tracking
    is_completed = Column(Boolean, default=False)
    completion_percentage = Column(Float, default=0.0)
    time_spent = Column(Integer, default=0)  # in seconds
    
    # Quiz results (if applicable)
    quiz_score = Column(Float, nullable=True)
    quiz_attempts = Column(Integer, default=0)
    quiz_passed = Column(Boolean, default=False)
    quiz_data = Column(JSON, nullable=True)  # User's quiz responses
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    enrollment = relationship("CourseEnrollment", back_populates="progress")
    lesson = relationship("CourseLesson", back_populates="progress")
    
    def __repr__(self):
        return f"<LessonProgress(enrollment_id={self.enrollment_id}, lesson_id={self.lesson_id}, completed={self.is_completed})>"
    
    def mark_completed(self):
        """Mark lesson as completed"""
        self.is_completed = True
        self.completion_percentage = 100.0
        self.completed_at = datetime.utcnow()


class CourseReview(Base):
    """Course review and rating model"""
    __tablename__ = "course_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Review content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)
    
    # Moderation
    is_approved = Column(Boolean, default=False)
    is_verified_completion = Column(Boolean, default=False)  # User completed the course
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    course = relationship("Course", back_populates="reviews")
    user = relationship("User", backref="course_reviews")
    
    def __repr__(self):
        return f"<CourseReview(id={self.id}, course_id={self.course_id}, rating={self.rating})>"


class CourseCategory(Base):
    """Course category model"""
    __tablename__ = "course_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    slug = Column(String(120), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Display
    icon = Column(String(100), nullable=True)
    color = Column(String(7), nullable=True)  # Hex color
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # SEO
    meta_title = Column(String(200), nullable=True)
    meta_description = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<CourseCategory(id={self.id}, name='{self.name}')>"


class CourseCertificate(Base):
    """Course completion certificate model"""
    __tablename__ = "course_certificates"
    
    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey("course_enrollments.id"), unique=True, nullable=False)
    
    # Certificate details
    certificate_number = Column(String(100), unique=True, nullable=False, index=True)
    certificate_url = Column(String(500), nullable=True)
    
    # Verification
    verification_code = Column(String(50), unique=True, nullable=False)
    is_valid = Column(Boolean, default=True)
    
    # Timestamps
    issued_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    enrollment = relationship("CourseEnrollment", backref="certificate")
    
    def __repr__(self):
        return f"<CourseCertificate(id={self.id}, number='{self.certificate_number}')>"
    
    @property
    def is_expired(self) -> bool:
        """Check if certificate is expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at