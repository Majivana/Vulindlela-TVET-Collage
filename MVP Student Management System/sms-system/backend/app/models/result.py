"""
Result Model

Academic results and grade tracking for students.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, Float, Enum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.db.database import Base


if TYPE_CHECKING:
    from app.models.student_profile import StudentProfile
    from app.models.module import Module


class AssessmentType(str, enum.Enum):
    """Type of assessment."""
    TEST = "test"
    EXAM = "exam"
    ASSIGNMENT = "assignment"
    PRACTICAL = "practical"
    PROJECT = "project"
    QUIZ = "quiz"
    PRESENTATION = "presentation"
    PARTICIPATION = "participation"
    FINAL = "final"


class Result(Base):
    """
    Result model for student academic performance.
    
    Stores individual assessment results and calculates overall performance.
    
    Attributes:
        id: Primary key
        student_id: Student who received the result
        module_id: Associated module
        assessment_type: Type of assessment
        assessment_name: Name/title of assessment
        term: Academic term/semester
        academic_year: Academic year
        score: Raw score achieved
        max_score: Maximum possible score
        percentage: Calculated percentage
        grade: Letter grade
        weight: Weight towards final grade
        lecturer_notes: Internal notes
        student_feedback: Feedback visible to student
        published: Whether result is visible to student
        published_at: When result was published
    """
    
    __tablename__ = "results"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False
    )
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Assessment Details
    assessment_type: Mapped[AssessmentType] = mapped_column(
        Enum(AssessmentType),
        nullable=False
    )
    assessment_name: Mapped[str] = mapped_column(String(200), nullable=False)
    
    # Academic Period
    term: Mapped[str] = mapped_column(String(20), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Scoring
    score: Mapped[float] = mapped_column(nullable=False)
    max_score: Mapped[float] = mapped_column(default=100.0)
    percentage: Mapped[Optional[float]] = mapped_column(nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    
    # Weighting
    weight: Mapped[Optional[float]] = mapped_column(nullable=True)
    contributes_to_final: Mapped[bool] = mapped_column(default=True)
    
    # Feedback
    lecturer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    student_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Publication
    published: Mapped[bool] = mapped_column(default=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    student: Mapped["StudentProfile"] = relationship(
        "StudentProfile",
        back_populates="results"
    )
    module: Mapped["Module"] = relationship("Module", back_populates="results")
    
    def __repr__(self) -> str:
        return f"<Result(id={self.id}, student={self.student_id}, module={self.module_id}, score={self.score})>"
    
    def calculate_percentage(self) -> float:
        """Calculate percentage score."""
        if self.max_score > 0:
            return round((self.score / self.max_score) * 100, 2)
        return 0.0
    
    def calculate_grade(self) -> str:
        """
        Calculate letter grade based on percentage.
        
        Uses standard grading scale:
        A: 80-100%
        B: 70-79%
        C: 60-69%
        D: 50-59%
        F: Below 50%
        """
        pct = self.percentage or self.calculate_percentage()
        
        if pct >= 80:
            return "A"
        elif pct >= 70:
            return "B"
        elif pct >= 60:
            return "C"
        elif pct >= 50:
            return "D"
        else:
            return "F"
    
    def update_calculated_fields(self) -> None:
        """Update percentage and grade based on score."""
        self.percentage = self.calculate_percentage()
        self.grade = self.calculate_grade()
    
    def to_dict(self, include_private: bool = False) -> dict:
        """
        Convert result to dictionary.
        
        Args:
            include_private: Whether to include lecturer notes
            
        Returns:
            Dictionary representation
        """
        data = {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.user.full_name if self.student and self.student.user else None,
            "module_id": self.module_id,
            "module_code": self.module.code if self.module else None,
            "module_title": self.module.title if self.module else None,
            "assessment_type": self.assessment_type.value,
            "assessment_name": self.assessment_name,
            "term": self.term,
            "academic_year": self.academic_year,
            "score": self.score,
            "max_score": self.max_score,
            "percentage": self.percentage or self.calculate_percentage(),
            "grade": self.grade or self.calculate_grade(),
            "weight": self.weight,
            "contributes_to_final": self.contributes_to_final,
            "student_feedback": self.student_feedback,
            "published": self.published,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_private:
            data["lecturer_notes"] = self.lecturer_notes
            
        return data


class AcademicRecord(Base):
    """
    Summary academic record for a student.
    
    Stores cumulative GPA and academic standing.
    """
    
    __tablename__ = "academic_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    
    # Cumulative Statistics
    total_credits_attempted: Mapped[int] = mapped_column(default=0)
    total_credits_earned: Mapped[int] = mapped_column(default=0)
    cumulative_gpa: Mapped[float] = mapped_column(default=0.0)
    
    # Term Statistics
    current_term: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    current_year: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    term_gpa: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Academic Standing
    academic_standing: Mapped[str] = mapped_column(String(50), default="Good Standing")
    probation_count: Mapped[int] = mapped_column(default=0)
    
    # Honors
    dean_list_count: Mapped[int] = mapped_column(default=0)
    honors_awarded: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    def __repr__(self) -> str:
        return f"<AcademicRecord(student={self.student_id}, gpa={self.cumulative_gpa})>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "total_credits_attempted": self.total_credits_attempted,
            "total_credits_earned": self.total_credits_earned,
            "cumulative_gpa": self.cumulative_gpa,
            "current_term": self.current_term,
            "current_year": self.current_year,
            "term_gpa": self.term_gpa,
            "academic_standing": self.academic_standing,
            "probation_count": self.probation_count,
            "dean_list_count": self.dean_list_count,
            "honors_awarded": self.honors_awarded,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
