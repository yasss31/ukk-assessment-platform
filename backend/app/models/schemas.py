"""
app/models/schemas.py - Model Data Pydantic untuk UKK Assessment Platform
"""
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    EXAMINER = "examiner"


class User(BaseModel):
    id: str
    username: str
    full_name: str
    role: UserRole = UserRole.EXAMINER
    email: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User


class Participant(BaseModel):
    id: str
    name: str
    participant_number: str
    student_class: str
    school: str = "SMK Negeri 1 Banyumas"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ParticipantCreate(BaseModel):
    name: str
    participant_number: str
    student_class: str
    school: str = "SMK Negeri 1 Banyumas"


class IndicatorStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    ERROR = "ERROR"
    WARNING = "WARNING"


class RubricIndicator(BaseModel):
    id: str
    code: str  # e.g., "01.01", "NET.01"
    name: str
    category: str  # e.g., "Network", "Security", "Compute", "Database", "Storage", "SNS", "Application"
    expected_value: str
    weight: float = 1.0
    check_method: str  # e.g., "aws_api_vpc", "aws_api_subnet", "http_health"
    description: Optional[str] = ""
    is_active: bool = True


class RubricProfile(BaseModel):
    id: str
    name: str
    version: str = "1.0"
    description: str
    indicators: List[RubricIndicator]
    total_weight: float = 100.0
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class RubricProfileCreate(BaseModel):
    name: str
    version: str = "1.0"
    description: str
    indicators: List[RubricIndicator]


class AWSCredentialInput(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_session_token: str
    aws_region: str = "us-east-1"


class AWSCredentialValidationResult(BaseModel):
    is_valid: bool
    account_id: Optional[str] = None
    arn: Optional[str] = None
    region: str
    error_message: Optional[str] = None


class AssessmentCreate(BaseModel):
    participant_id: str
    rubric_profile_id: str
    aws_credentials: AWSCredentialInput
    notes: Optional[str] = None
    run_app_tests: bool = True


class AssessmentStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class IndicatorResult(BaseModel):
    indicator_id: str
    code: str
    name: str
    category: str
    expected: str
    actual: str
    status: IndicatorStatus
    score: float
    weight: float
    evidence: str
    error_message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AssessmentSession(BaseModel):
    id: str
    participant: Participant
    rubric_id: str
    rubric_name: str
    rubric_version: str
    examiner_name: str
    aws_account_id: Optional[str] = None
    aws_region: str = "us-east-1"
    status: AssessmentStatus = AssessmentStatus.PENDING
    total_score: float = 0.0
    max_score: float = 100.0
    pass_count: int = 0
    fail_count: int = 0
    skip_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    completion_percentage: float = 0.0
    results: List[IndicatorResult] = []
    notes: Optional[str] = None
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None


class AutoPlayTargetInstance(BaseModel):
    instance_id: str
    name: str
    region: str = "us-east-1"
    is_allowed: bool = True


class AutoPlayConfig(BaseModel):
    is_enabled: bool = False
    interval_minutes: int = 180
    max_retries: int = 3
    target_instances: List[AutoPlayTargetInstance] = []
    last_run: Optional[str] = None
    next_run: Optional[str] = None
    last_status: str = "IDLE"
    last_error: Optional[str] = None
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AutoPlayLog(BaseModel):
    id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    action: str
    status: str
    account_id: Optional[str] = None
    target_instance_id: Optional[str] = None
    details: str


class ServiceHealthStatus(BaseModel):
    backend_status: str = "HEALTHY"
    google_sheets_status: str  # "CONNECTED", "NEEDS_CONFIGURATION", "ERROR"
    storage_mode: str
    active_assessments_count: int = 0
    auto_play_status: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
