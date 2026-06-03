"""Pydantic data contracts for all API request/response models."""
from pydantic import BaseModel


class UserCreate(BaseModel):
    """Request body for creating a user."""
    full_name: str
    email: str
    role: str
    availability: int
    timezone: str = "UTC"


class User(BaseModel):
    """Full user record from the users sheet."""
    user_id: str
    full_name: str
    email: str
    role: str
    availability: int
    timezone: str
    created_at: str


class Skill(BaseModel):
    """Skill record from the skills sheet."""
    skill_id: str
    skill_name: str
    category: str
    description: str = ""


class Level(BaseModel):
    """Level record from the levels sheet."""
    level_id: int
    level_name: str
    score_weight: float


class UserSkillCreate(BaseModel):
    """Request body for creating a user-skill link."""
    user_id: str
    skill_id: str
    level_id: int
    years_exp: int | None = None
    last_used: str | None = None


class UserSkill(BaseModel):
    """User-skill join record."""
    id: str
    user_id: str
    skill_id: str
    level_id: int
    years_exp: int | None = None
    last_used: str | None = None


class UserWithSkills(BaseModel):
    """User enriched with their skill profiles."""
    user: User
    skills: list[UserSkill]


class SkillStrength(BaseModel):
    """Skill with its computed strength score."""
    skill_id: str
    skill_name: str
    category: str
    strength_score: float


class PipelineRequest(BaseModel):
    """Request body for running the pipeline."""
    problem_statement: str
    language: str = "English"
    cached_search_results: dict = {}
    override_steps: list[dict] = []
    translated_problem: str = ""


class SolutionStep(BaseModel):
    """A single step in the generated solution."""
    step: int
    action: str
    technology: str
    skill_strength_score: float
    effort: str = ""


class ResourceRecommendation(BaseModel):
    """A ranked resource recommendation."""
    user_id: str
    full_name: str
    fit_score: float
    priority: str
    availability: int
    matched_skills: list[str] = []


class TaskResourceAssignment(BaseModel):
    """A resource assigned or suggested for a specific project task."""
    user_id: str
    full_name: str
    role: str = ""
    fit_score: float
    availability: int
    matched_skills: list[str] = []
    recommendation: str


class TaskRecommendation(BaseModel):
    """Task-level staffing recommendation."""
    task_id: int
    task: str
    required_skills: list[str]
    strength_score: float
    resources: list[TaskResourceAssignment]
    rationale: str = ""


class RiskFlag(BaseModel):
    """A risk flag for a resource."""
    user_id: str
    reason: str


class PipelineResult(BaseModel):
    """Complete pipeline result (report_bytes is base64-encoded)."""
    problem: str
    model_name: str
    solution: list[SolutionStep]
    resources: list[ResourceRecommendation]
    task_recommendations: list[TaskRecommendation] = []
    risk_flags: list[RiskFlag]
    report_bytes: str
