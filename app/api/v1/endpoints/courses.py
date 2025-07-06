# app/api/v1/endpoints/courses.py - Phase 5 Course Endpoints
"""
CorePath Impact Course API Endpoints
Phase 5: Course management and learning system
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_current_admin, get_optional_user
from app.models.user import User
from app.models.course import Course, CourseEnrollment
from app.services.course_service import CourseService
from app.services.file_service import FileService
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse, CourseDetailResponse,
    CourseModuleCreate, CourseModuleResponse, CourseLessonCreate, CourseLessonResponse,
    CourseEnrollmentCreate, CourseEnrollmentResponse, LessonProgressUpdate, LessonProgressResponse,
    CourseReviewCreate, CourseReviewResponse, CourseSearchFilters, CourseAnalytics,
    UserCourseAnalytics, CourseCertificateResponse, QuizSubmission, QuizResult
)
from app.utils.helpers import create_response

router = APIRouter()

# Public Course Routes
@router.get("/", response_model=Dict[str, Any])
async def get_courses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None),
    difficulty_level: Optional[str] = Query(None),
    age_group: Optional[str] = Query(None),
    is_free: Optional[bool] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_rating: Optional[float] = Query(None, ge=1, le=5),
    is_featured: Optional[bool] = Query(None),
    instructor: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get courses with search and filtering"""
    
    filters = CourseSearchFilters(
        q=q,
        difficulty_level=difficulty_level,
        age_group=age_group,
        is_free=is_free,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        is_featured=is_featured,
        instructor=instructor,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    course_service = CourseService(db)
    user_id = current_user.id if current_user else None
    
    courses = course_service.search_courses(filters, page, per_page, user_id)
    
    return create_response(data=courses, message="Courses retrieved successfully")

@router.get("/featured", response_model=List[CourseResponse])
async def get_featured_courses(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get featured courses"""
    
    course_service = CourseService(db)
    courses = course_service.get_featured_courses(limit)
    
    return courses

@router.get("/popular", response_model=List[CourseResponse])
async def get_popular_courses(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get popular courses by enrollment"""
    
    course_service = CourseService(db)
    courses = course_service.get_popular_courses(limit)
    
    return courses

@router.get("/{course_id}", response_model=CourseDetailResponse)
async def get_course(
    course_id: int,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Get course details by ID"""
    
    course_service = CourseService(db)
    course = course_service.get_course_by_id(course_id, include_modules=True)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Check if course is published (unless user is admin)
    if course.status != "published":
        if not current_user or not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found"
            )
    
    # Get recent reviews
    reviews_result = course_service.get_course_reviews(course_id, page=1, per_page=5)
    course.recent_reviews = reviews_result["items"]
    
    return course

@router.get("/{course_id}/reviews", response_model=Dict[str, Any])
async def get_course_reviews(
    course_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get course reviews with pagination"""
    
    course_service = CourseService(db)
    reviews = course_service.get_course_reviews(course_id, page, per_page)
    
    return create_response(data=reviews, message="Reviews retrieved successfully")

# Enrollment Routes
@router.post("/{course_id}/enroll", response_model=CourseEnrollmentResponse)
async def enroll_in_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enroll user in a course"""
    
    course_service = CourseService(db)
    
    try:
        enrollment = course_service.enroll_user(current_user.id, course_id)
        return enrollment
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enroll in course: {str(e)}"
        )

@router.get("/enrollments/my", response_model=Dict[str, Any])
async def get_my_enrollments(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's course enrollments"""
    
    course_service = CourseService(db)
    enrollments = course_service.get_user_enrollments(current_user.id, page, per_page, status)
    
    return create_response(data=enrollments, message="Enrollments retrieved successfully")

@router.get("/{course_id}/progress", response_model=Dict[str, Any])
async def get_course_progress(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's progress in a course"""
    
    course_service = CourseService(db)
    progress = course_service.get_course_progress(current_user.id, course_id)
    
    return create_response(data=progress, message="Course progress retrieved successfully")

# Learning Routes
@router.put("/lessons/{lesson_id}/progress", response_model=LessonProgressResponse)
async def update_lesson_progress(
    lesson_id: int,
    progress_data: LessonProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update lesson progress"""
    
    course_service = CourseService(db)
    
    try:
        progress = course_service.update_lesson_progress(
            current_user.id, lesson_id, progress_data
        )
        return progress
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update progress: {str(e)}"
        )

@router.post("/lessons/{lesson_id}/quiz", response_model=QuizResult)
async def submit_quiz(
    lesson_id: int,
    quiz_submission: QuizSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit quiz answers"""
    
    course_service = CourseService(db)
    
    try:
        result = course_service.submit_quiz(current_user.id, lesson_id, quiz_submission)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit quiz: {str(e)}"
        )

# Review Routes
@router.post("/{course_id}/reviews", response_model=CourseReviewResponse)
async def create_course_review(
    course_id: int,
    review_data: CourseReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a course review"""
    
    # Set course_id from URL parameter
    review_data.course_id = course_id
    
    course_service = CourseService(db)
    
    try:
        review = course_service.create_review(current_user.id, review_data)
        return review
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create review: {str(e)}"
        )

# Certificate Routes
@router.get("/{course_id}/certificate", response_model=CourseCertificateResponse)
async def get_course_certificate(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get course completion certificate"""
    
    course_service = CourseService(db)
    enrollment = course_service.get_enrollment(current_user.id, course_id)
    
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enrollment not found"
        )
    
    try:
        certificate = course_service.generate_certificate(enrollment.id)
        return certificate
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate certificate: {str(e)}"
        )

@router.get("/certificates/verify/{verification_code}", response_model=Dict[str, Any])
async def verify_certificate(
    verification_code: str,
    db: Session = Depends(get_db)
):
    """Verify a course certificate"""
    
    course_service = CourseService(db)
    certificate = course_service.verify_certificate(verification_code)
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found or invalid"
        )
    
    return create_response(
        data={
            "valid": True,
            "certificate": {
                "number": certificate.certificate_number,
                "course_title": certificate.enrollment.course.title,
                "student_name": certificate.enrollment.user.full_name,
                "completion_date": certificate.enrollment.completed_at.isoformat(),
                "issued_date": certificate.issued_at.isoformat()
            }
        },
        message="Certificate verified successfully"
    )

# Analytics Routes
@router.get("/analytics/my-learning", response_model=UserCourseAnalytics)
async def get_my_learning_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's learning analytics"""
    
    course_service = CourseService(db)
    analytics = course_service.get_user_learning_analytics(current_user.id)
    
    return analytics

# Admin Routes
@router.post("/", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a new course (admin only)"""
    
    course_service = CourseService(db)
    
    try:
        course = course_service.create_course(course_data, current_admin.id)
        return course
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create course: {str(e)}"
        )

@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update a course (admin only)"""
    
    course_service = CourseService(db)
    
    try:
        course = course_service.update_course(course_id, course_data)
        return course
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update course: {str(e)}"
        )

@router.delete("/{course_id}", response_model=Dict[str, Any])
async def delete_course(
    course_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete a course (admin only)"""
    
    course_service = CourseService(db)
    
    try:
        success = course_service.delete_course(course_id)
        return create_response(
            data={"deleted": success},
            message="Course deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete course: {str(e)}"
        )

@router.post("/{course_id}/upload-thumbnail", response_model=Dict[str, Any])
async def upload_course_thumbnail(
    course_id: int,
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Upload course thumbnail image (admin only)"""
    
    # Verify course exists
    course_service = CourseService(db)
    course = course_service.get_course_by_id(course_id)
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    # Upload file
    file_service = FileService()
    
    try:
        file_info = await file_service.upload_image(
            file=file,
            directory="courses",
            user_id=current_admin.id
        )
        
        # Update course thumbnail
        course.thumbnail_url = file_info["file_url"]
        db.commit()
        
        return create_response(
            data=file_info,
            message="Thumbnail uploaded successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload thumbnail: {str(e)}"
        )

# Module Management Routes (Admin)
@router.post("/{course_id}/modules", response_model=CourseModuleResponse)
async def create_course_module(
    course_id: int,
    module_data: CourseModuleCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a course module (admin only)"""
    
    # Set course_id from URL parameter
    module_data.course_id = course_id
    
    course_service = CourseService(db)
    
    try:
        module = course_service.create_module(module_data)
        return module
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create module: {str(e)}"
        )

@router.post("/modules/{module_id}/lessons", response_model=CourseLessonResponse)
async def create_course_lesson(
    module_id: int,
    lesson_data: CourseLessonCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create a course lesson (admin only)"""
    
    # Set module_id from URL parameter
    lesson_data.module_id = module_id
    
    course_service = CourseService(db)
    
    try:
        lesson = course_service.create_lesson(lesson_data)
        return lesson
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create lesson: {str(e)}"
        )

# Course Analytics (Admin)
@router.get("/{course_id}/analytics", response_model=CourseAnalytics)
async def get_course_analytics(
    course_id: int,
    days: int = Query(30, ge=1, le=365),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get course analytics (admin only)"""
    
    course_service = CourseService(db)
    
    try:
        analytics = course_service.get_course_analytics(course_id, days)
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics: {str(e)}"
        )

@router.get("/admin/enrollments", response_model=Dict[str, Any])
async def get_all_enrollments(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    course_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all course enrollments (admin only)"""
    
    query = db.query(CourseEnrollment).options(
        joinedload(CourseEnrollment.course),
        joinedload(CourseEnrollment.user)
    )
    
    if course_id:
        query = query.filter(CourseEnrollment.course_id == course_id)
    
    if status:
        query = query.filter(CourseEnrollment.status == status)
    
    query = query.order_by(desc(CourseEnrollment.enrolled_at))
    
    from app.utils.helpers import paginate_query
    enrollments = paginate_query(query, page, per_page)
    
    return create_response(data=enrollments, message="Enrollments retrieved successfully")

@router.get("/admin/reviews", response_model=Dict[str, Any])
async def get_all_reviews(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    course_id: Optional[int] = Query(None),
    is_approved: Optional[bool] = Query(None),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all course reviews (admin only)"""
    
    from app.models.course import CourseReview
    
    query = db.query(CourseReview).options(
        joinedload(CourseReview.course),
        joinedload(CourseReview.user)
    )
    
    if course_id:
        query = query.filter(CourseReview.course_id == course_id)
    
    if is_approved is not None:
        query = query.filter(CourseReview.is_approved == is_approved)
    
    query = query.order_by(desc(CourseReview.created_at))
    
    from app.utils.helpers import paginate_query
    reviews = paginate_query(query, page, per_page)
    
    return create_response(data=reviews, message="Reviews retrieved successfully")

@router.put("/admin/reviews/{review_id}/approve", response_model=Dict[str, Any])
async def approve_review(
    review_id: int,
    approved: bool,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Approve or reject a course review (admin only)"""
    
    from app.models.course import CourseReview
    
    review = db.query(CourseReview).filter(CourseReview.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    review.is_approved = approved
    db.commit()
    
    return create_response(
        data={
            "review_id": review_id,
            "approved": approved
        },
        message=f"Review {'approved' if approved else 'rejected'} successfully"
    )

# Bulk Operations (Admin)
@router.post("/admin/bulk-publish", response_model=Dict[str, Any])
async def bulk_publish_courses(
    course_ids: List[int],
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Bulk publish courses (admin only)"""
    
    updated_count = 0
    
    for course_id in course_ids:
        course = db.query(Course).filter(Course.id == course_id).first()
        if course:
            course.status = "published"
            if not course.published_at:
                course.published_at = datetime.utcnow()
            updated_count += 1
    
    db.commit()
    
    return create_response(
        data={
            "updated_count": updated_count,
            "total_requested": len(course_ids)
        },
        message=f"Successfully published {updated_count} courses"
    )

# Search and Discovery
@router.get("/search/my-courses", response_model=List[CourseResponse])
async def search_my_courses(
    q: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search user's enrolled courses"""
    
    course_service = CourseService(db)
    courses = course_service.search_user_courses(current_user.id, q)
    
    return courses

# Course Statistics (Admin)
@router.get("/admin/stats", response_model=Dict[str, Any])
async def get_course_system_stats(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get course system statistics (admin only)"""
    
    total_courses = db.query(Course).count()
    published_courses = db.query(Course).filter(Course.status == "published").count()
    draft_courses = db.query(Course).filter(Course.status == "draft").count()
    
    total_enrollments = db.query(CourseEnrollment).count()
    completed_enrollments = db.query(CourseEnrollment).filter(
        CourseEnrollment.status == "completed"
    ).count()
    
    from app.models.course import CourseReview
    total_reviews = db.query(CourseReview).count()
    approved_reviews = db.query(CourseReview).filter(
        CourseReview.is_approved == True
    ).count()
    
    # Top performing courses
    top_courses = db.query(Course).filter(
        Course.status == "published"
    ).order_by(desc(Course.enrollment_count)).limit(5).all()
    
    return create_response(
        data={
            "courses": {
                "total": total_courses,
                "published": published_courses,
                "draft": draft_courses
            },
            "enrollments": {
                "total": total_enrollments,
                "completed": completed_enrollments,
                "completion_rate": (completed_enrollments / total_enrollments * 100) if total_enrollments > 0 else 0
            },
            "reviews": {
                "total": total_reviews,
                "approved": approved_reviews,
                "approval_rate": (approved_reviews / total_reviews * 100) if total_reviews > 0 else 0
            },
            "top_courses": [
                {
                    "id": course.id,
                    "title": course.title,
                    "enrollments": course.enrollment_count,
                    "rating": course.rating_average,
                    "completion_rate": course.completion_rate
                }
                for course in top_courses
            ]
        },
        message="Course system statistics retrieved successfully"
    )