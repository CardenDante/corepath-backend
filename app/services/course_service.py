# app/services/course_service.py
"""
CorePath Impact Course Service
Phase 5: Course management and learning system
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import and_, or_, desc, func
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
import uuid

from app.models.course import (
    Course, CourseModule, CourseLesson, CourseEnrollment, 
    LessonProgress, CourseReview, CourseCertificate
)
from app.models.user import User
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseSearchFilters,
    CourseModuleCreate, CourseLessonCreate, LessonProgressUpdate,
    CourseReviewCreate, QuizSubmission, QuizResult,
    CourseAnalytics, UserCourseAnalytics
)
from app.utils.helpers import paginate_query

if TYPE_CHECKING:
    pass


class CourseService:
    def __init__(self, db: Session):
        self.db = db

    # Course Management Methods
    def create_course(self, course_data: CourseCreate, instructor_id: int) -> Course:
        """Create a new course"""
        course = Course(
            **course_data.dict(),
            instructor_id=instructor_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(course)
        self.db.commit()
        self.db.refresh(course)
        return course

    def get_course_by_id(self, course_id: int, include_modules: bool = False) -> Optional[Course]:
        """Get course by ID"""
        query = self.db.query(Course)
        
        if include_modules:
            query = query.options(
                joinedload(Course.modules).joinedload(CourseModule.lessons)
            )
        
        return query.filter(Course.id == course_id).first()

    def update_course(self, course_id: int, course_data: CourseUpdate) -> Course:
        """Update a course"""
        course = self.get_course_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        update_data = course_data.dict(exclude_unset=True)
        update_data['updated_at'] = datetime.utcnow()
        
        for field, value in update_data.items():
            setattr(course, field, value)
        
        self.db.commit()
        self.db.refresh(course)
        return course

    def delete_course(self, course_id: int) -> bool:
        """Delete a course"""
        course = self.get_course_by_id(course_id)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
        
        # Check if course has enrollments
        enrollment_count = self.db.query(CourseEnrollment).filter(
            CourseEnrollment.course_id == course_id
        ).count()
        
        if enrollment_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete course with existing enrollments"
            )
        
        self.db.delete(course)
        self.db.commit()
        return True

    def search_courses(self, filters: CourseSearchFilters, page: int, per_page: int, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Search courses with filters"""
        query = self.db.query(Course).filter(Course.status == "published")
        
        # Apply filters
        if filters.q:
            search_term = f"%{filters.q}%"
            query = query.filter(
                or_(
                    Course.title.ilike(search_term),
                    Course.description.ilike(search_term),
                    Course.tags.ilike(search_term)
                )
            )
        
        if filters.difficulty_level:
            query = query.filter(Course.difficulty_level == filters.difficulty_level)
        
        if filters.age_group:
            query = query.filter(Course.age_group == filters.age_group)
        
        if filters.is_free is not None:
            if filters.is_free:
                query = query.filter(Course.price == 0)
            else:
                query = query.filter(Course.price > 0)
        
        if filters.min_price is not None:
            query = query.filter(Course.price >= filters.min_price)
        
        if filters.max_price is not None:
            query = query.filter(Course.price <= filters.max_price)
        
        if filters.min_rating is not None:
            query = query.filter(Course.rating_average >= filters.min_rating)
        
        if filters.is_featured is not None:
            query = query.filter(Course.is_featured == filters.is_featured)
        
        if filters.instructor:
            query = query.join(User).filter(
                User.full_name.ilike(f"%{filters.instructor}%")
            )
        
        # Apply sorting
        if filters.sort_by == "rating":
            order_col = Course.rating_average
        elif filters.sort_by == "price":
            order_col = Course.price
        elif filters.sort_by == "enrollment_count":
            order_col = Course.enrollment_count
        else:
            order_col = Course.created_at
        
        if filters.sort_order == "asc":
            query = query.order_by(order_col)
        else:
            query = query.order_by(desc(order_col))
        
        return paginate_query(query, page, per_page)

    def get_featured_courses(self, limit: int = 10) -> List[Course]:
        """Get featured courses"""
        return self.db.query(Course).filter(
            and_(Course.status == "published", Course.is_featured == True)
        ).order_by(desc(Course.rating_average)).limit(limit).all()

    def get_popular_courses(self, limit: int = 10) -> List[Course]:
        """Get popular courses by enrollment count"""
        return self.db.query(Course).filter(
            Course.status == "published"
        ).order_by(desc(Course.enrollment_count)).limit(limit).all()

    # Enrollment Methods
    def enroll_user(self, user_id: int, course_id: int) -> CourseEnrollment:
        """Enroll a user in a course"""
        # Check if course exists and is published
        course = self.get_course_by_id(course_id)
        if not course or course.status != "published":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found or not available"
            )
        
        # Check if user is already enrolled
        existing_enrollment = self.db.query(CourseEnrollment).filter(
            and_(
                CourseEnrollment.user_id == user_id,
                CourseEnrollment.course_id == course_id
            )
        ).first()
        
        if existing_enrollment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already enrolled in this course"
            )
        
        # Create enrollment
        enrollment = CourseEnrollment(
            user_id=user_id,
            course_id=course_id,
            enrolled_at=datetime.utcnow(),
            status="active"
        )
        
        self.db.add(enrollment)
        
        # Update course enrollment count
        course.enrollment_count += 1
        
        self.db.commit()
        self.db.refresh(enrollment)
        return enrollment

    def get_enrollment(self, user_id: int, course_id: int) -> Optional[CourseEnrollment]:
        """Get user enrollment for a course"""
        return self.db.query(CourseEnrollment).filter(
            and_(
                CourseEnrollment.user_id == user_id,
                CourseEnrollment.course_id == course_id
            )
        ).first()

    def get_user_enrollments(self, user_id: int, page: int, per_page: int, status: Optional[str] = None) -> Dict[str, Any]:
        """Get user's course enrollments"""
        query = self.db.query(CourseEnrollment).options(
            joinedload(CourseEnrollment.course)
        ).filter(CourseEnrollment.user_id == user_id)
        
        if status:
            query = query.filter(CourseEnrollment.status == status)
        
        query = query.order_by(desc(CourseEnrollment.enrolled_at))
        
        return paginate_query(query, page, per_page)

    # Progress Tracking Methods
    def get_course_progress(self, user_id: int, course_id: int) -> Dict[str, Any]:
        """Get user's progress in a course"""
        enrollment = self.get_enrollment(user_id, course_id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enrollment not found"
            )
        
        course = self.get_course_by_id(course_id, include_modules=True)
        
        # Get all lessons in the course
        total_lessons = 0
        completed_lessons = 0
        
        for module in course.modules:
            for lesson in module.lessons:
                total_lessons += 1
                
                # Check if lesson is completed
                progress = self.db.query(LessonProgress).filter(
                    and_(
                        LessonProgress.user_id == user_id,
                        LessonProgress.lesson_id == lesson.id,
                        LessonProgress.is_completed == True
                    )
                ).first()
                
                if progress:
                    completed_lessons += 1
        
        progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        return {
            "enrollment_id": enrollment.id,
            "course_id": course_id,
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "progress_percentage": round(progress_percentage, 2),
            "status": enrollment.status,
            "enrolled_at": enrollment.enrolled_at,
            "last_accessed": enrollment.last_accessed_at
        }

    def update_lesson_progress(self, user_id: int, lesson_id: int, progress_data: LessonProgressUpdate) -> LessonProgress:
        """Update lesson progress"""
        # Check if lesson exists
        lesson = self.db.query(CourseLesson).filter(CourseLesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        # Check if user is enrolled in the course
        enrollment = self.get_enrollment(user_id, lesson.module.course_id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not enrolled in this course"
            )
        
        # Get or create lesson progress
        progress = self.db.query(LessonProgress).filter(
            and_(
                LessonProgress.user_id == user_id,
                LessonProgress.lesson_id == lesson_id
            )
        ).first()
        
        if not progress:
            progress = LessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                started_at=datetime.utcnow()
            )
            self.db.add(progress)
        
        # Update progress
        update_data = progress_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(progress, field, value)
        
        if progress_data.is_completed and not progress.completed_at:
            progress.completed_at = datetime.utcnow()
        
        progress.updated_at = datetime.utcnow()
        
        # Update enrollment last accessed
        enrollment.last_accessed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(progress)
        return progress

    # Quiz Methods
    def submit_quiz(self, user_id: int, lesson_id: int, quiz_submission: QuizSubmission) -> QuizResult:
        """Submit quiz answers and calculate score"""
        # Check if user has access to the lesson
        lesson = self.db.query(CourseLesson).filter(CourseLesson.id == lesson_id).first()
        if not lesson:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        enrollment = self.get_enrollment(user_id, lesson.module.course_id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not enrolled in this course"
            )
        
        # Calculate score (this is a simplified version)
        total_questions = len(quiz_submission.answers)
        correct_answers = 0
        
        # Here you would typically compare with stored correct answers
        # For now, we'll assume a simple scoring mechanism
        for answer in quiz_submission.answers:
            # This is where you'd implement your quiz scoring logic
            # For example, checking against stored correct answers
            pass
        
        score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        passed = score_percentage >= 70  # 70% passing grade
        
        # Update lesson progress if quiz is passed
        if passed:
            self.update_lesson_progress(
                user_id, 
                lesson_id, 
                LessonProgressUpdate(is_completed=True, quiz_score=score_percentage)
            )
        
        return QuizResult(
            lesson_id=lesson_id,
            score=score_percentage,
            total_questions=total_questions,
            correct_answers=correct_answers,
            passed=passed,
            submitted_at=datetime.utcnow()
        )

    # Review Methods
    def create_review(self, user_id: int, review_data: CourseReviewCreate) -> CourseReview:
        """Create a course review"""
        # Check if user is enrolled in the course
        enrollment = self.get_enrollment(user_id, review_data.course_id)
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be enrolled in the course to leave a review"
            )
        
        # Check if user has already reviewed this course
        existing_review = self.db.query(CourseReview).filter(
            and_(
                CourseReview.user_id == user_id,
                CourseReview.course_id == review_data.course_id
            )
        ).first()
        
        if existing_review:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already reviewed this course"
            )
        
        review = CourseReview(
            **review_data.dict(),
            user_id=user_id,
            created_at=datetime.utcnow()
        )
        
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        
        # Update course rating average
        self._update_course_rating(review_data.course_id)
        
        return review

    def get_course_reviews(self, course_id: int, page: int, per_page: int) -> Dict[str, Any]:
        """Get course reviews with pagination"""
        query = self.db.query(CourseReview).options(
            joinedload(CourseReview.user)
        ).filter(
            and_(
                CourseReview.course_id == course_id,
                CourseReview.is_approved == True
            )
        ).order_by(desc(CourseReview.created_at))
        
        return paginate_query(query, page, per_page)

    def _update_course_rating(self, course_id: int):
        """Update course average rating"""
        avg_rating = self.db.query(func.avg(CourseReview.rating)).filter(
            and_(
                CourseReview.course_id == course_id,
                CourseReview.is_approved == True
            )
        ).scalar()
        
        review_count = self.db.query(CourseReview).filter(
            and_(
                CourseReview.course_id == course_id,
                CourseReview.is_approved == True
            )
        ).count()
        
        course = self.get_course_by_id(course_id)
        if course:
            course.rating_average = round(avg_rating, 2) if avg_rating else 0.0
            course.rating_count = review_count
            self.db.commit()

    # Certificate Methods
    def generate_certificate(self, enrollment_id: int) -> CourseCertificate:
        """Generate course completion certificate"""
        enrollment = self.db.query(CourseEnrollment).filter(
            CourseEnrollment.id == enrollment_id
        ).first()
        
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enrollment not found"
            )
        
        if enrollment.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Course not completed yet"
            )
        
        # Check if certificate already exists
        existing_cert = self.db.query(CourseCertificate).filter(
            CourseCertificate.enrollment_id == enrollment_id
        ).first()
        
        if existing_cert:
            return existing_cert
        
        # Generate certificate
        certificate = CourseCertificate(
            enrollment_id=enrollment_id,
            certificate_number=f"CERT-{uuid.uuid4().hex[:12].upper()}",
            verification_code=uuid.uuid4().hex,
            issued_at=datetime.utcnow()
        )
        
        self.db.add(certificate)
        self.db.commit()
        self.db.refresh(certificate)
        return certificate

    def verify_certificate(self, verification_code: str) -> Optional[CourseCertificate]:
        """Verify a course certificate"""
        return self.db.query(CourseCertificate).filter(
            CourseCertificate.verification_code == verification_code
        ).first()

    # Module and Lesson Methods
    def create_module(self, module_data: CourseModuleCreate) -> CourseModule:
        """Create a course module"""
        module = CourseModule(
            **module_data.dict(),
            created_at=datetime.utcnow()
        )
        
        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)
        return module

    def create_lesson(self, lesson_data: CourseLessonCreate) -> CourseLesson:
        """Create a course lesson"""
        lesson = CourseLesson(
            **lesson_data.dict(),
            created_at=datetime.utcnow()
        )
        
        self.db.add(lesson)
        self.db.commit()
        self.db.refresh(lesson)
        return lesson

    # Analytics Methods
    def get_course_analytics(self, course_id: int, days: int = 30) -> CourseAnalytics:
        """Get course analytics"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get enrollments in date range
        enrollments = self.db.query(CourseEnrollment).filter(
            and_(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.enrolled_at >= start_date
            )
        ).count()
        
        # Get completions in date range
        completions = self.db.query(CourseEnrollment).filter(
            and_(
                CourseEnrollment.course_id == course_id,
                CourseEnrollment.status == "completed",
                CourseEnrollment.completed_at >= start_date
            )
        ).count()
        
        # Get total enrollments
        total_enrollments = self.db.query(CourseEnrollment).filter(
            CourseEnrollment.course_id == course_id
        ).count()
        
        # Get average rating
        avg_rating = self.db.query(func.avg(CourseReview.rating)).filter(
            and_(
                CourseReview.course_id == course_id,
                CourseReview.is_approved == True
            )
        ).scalar()
        
        return CourseAnalytics(
            course_id=course_id,
            period_days=days,
            new_enrollments=enrollments,
            completions=completions,
            total_enrollments=total_enrollments,
            completion_rate=(completions / total_enrollments * 100) if total_enrollments > 0 else 0,
            average_rating=round(avg_rating, 2) if avg_rating else 0.0
        )

    def get_user_learning_analytics(self, user_id: int) -> UserCourseAnalytics:
        """Get user's learning analytics"""
        # Get user's enrollments
        enrollments = self.db.query(CourseEnrollment).filter(
            CourseEnrollment.user_id == user_id
        ).all()
        
        total_courses = len(enrollments)
        completed_courses = len([e for e in enrollments if e.status == "completed"])
        in_progress_courses = len([e for e in enrollments if e.status == "active"])
        
        # Calculate total learning time (simplified)
        total_learning_time = 0
        for enrollment in enrollments:
            if enrollment.last_accessed_at and enrollment.enrolled_at:
                total_learning_time += (enrollment.last_accessed_at - enrollment.enrolled_at).total_seconds()
        
        return UserCourseAnalytics(
            user_id=user_id,
            total_courses_enrolled=total_courses,
            courses_completed=completed_courses,
            courses_in_progress=in_progress_courses,
            total_learning_time_hours=round(total_learning_time / 3600, 2),
            completion_rate=(completed_courses / total_courses * 100) if total_courses > 0 else 0
        )

    def search_user_courses(self, user_id: int, query: str) -> List[Course]:
        """Search user's enrolled courses"""
        search_term = f"%{query}%"
        
        courses = self.db.query(Course).join(CourseEnrollment).filter(
            and_(
                CourseEnrollment.user_id == user_id,
                or_(
                    Course.title.ilike(search_term),
                    Course.description.ilike(search_term)
                )
            )
        ).all()
        
        return courses