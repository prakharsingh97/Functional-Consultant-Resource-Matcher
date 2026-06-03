"""Mock API client returning fixture data matching backend Pydantic models.

Used when env=TESTING. All data shapes match the contracts in
src/models/schemas.py: User, Skill, Level, SkillStrength, UserSkill.
"""

MOCK_USERS = [
    {
        "user_id": "U01",
        "full_name": "Alice Chen",
        "email": "alice.chen@nexus.com",
        "role": "Senior Consultant",
        "availability": 35,
        "timezone": "America/New_York",
        "created_at": "2025-01-15T09:00:00+00:00",
    },
    {
        "user_id": "U02",
        "full_name": "Bob Kumar",
        "email": "bob.kumar@nexus.com",
        "role": "Lead Architect",
        "availability": 30,
        "timezone": "Asia/Singapore",
        "created_at": "2025-01-15T09:00:00+00:00",
    },
]

MOCK_SKILLS = [
    {
        "skill_id": "SK01",
        "skill_name": "Python",
        "category": "Engineering",
        "description": "General-purpose programming",
    },
    {
        "skill_id": "SK02",
        "skill_name": "AWS",
        "category": "Cloud",
        "description": "Amazon Web Services cloud platform",
    },
]

MOCK_LEVELS = [
    {"level_id": 1, "level_name": "Beginner", "score_weight": 0.25},
    {"level_id": 2, "level_name": "Intermediate", "score_weight": 0.50},
    {"level_id": 3, "level_name": "Advanced", "score_weight": 0.75},
    {"level_id": 4, "level_name": "Expert", "score_weight": 1.00},
]

MOCK_STRENGTH = [
    {
        "skill_id": "SK01",
        "skill_name": "Python",
        "category": "Engineering",
        "strength_score": 5.25,
    },
    {
        "skill_id": "SK02",
        "skill_name": "AWS",
        "category": "Cloud",
        "strength_score": 4.50,
    },
]


class MockAPIClient:
    """Returns fixture data for all API calls. No network required."""

    def get_users(self) -> list[dict]:
        """Return mock users. Shape matches User model."""
        return MOCK_USERS

    def get_skills(self) -> list[dict]:
        """Return mock skills. Shape matches Skill model."""
        return MOCK_SKILLS

    def get_levels(self) -> list[dict]:
        """Return mock levels. Shape matches Level model."""
        return MOCK_LEVELS

    def get_skill_strength(self) -> list[dict]:
        """Return mock skill strength scores. Shape matches SkillStrength."""
        return MOCK_STRENGTH

    def run_pipeline(self, problem_statement: str) -> dict:
        """Return a mock pipeline result for the given problem."""
        solution = [
            {
                "step": 1,
                "action": "Set up backend API",
                "technology": "FastAPI",
                "skill_strength_score": 5.50,
                "effort": "2 days",
            },
            {
                "step": 2,
                "action": "Deploy to cloud",
                "technology": "AWS",
                "skill_strength_score": 4.50,
                "effort": "1 day",
            },
        ]
        resources = [
            {
                "user_id": "U01",
                "full_name": "Alice Chen",
                "fit_score": 0.85,
                "priority": "P1",
                "availability": 35,
                "matched_skills": ["Python", "AWS"],
            },
            {
                "user_id": "U02",
                "full_name": "Bob Kumar",
                "fit_score": 0.60,
                "priority": "P2",
                "availability": 30,
                "matched_skills": ["Python"],
            },
        ]
        return {
            "problem": problem_statement,
            "model_name": "mock-llm",
            "solution": solution,
            "resources": resources,
            "risk_flags": [],
            "report_bytes": self.generate_report({
                "problem": problem_statement,
                "solution": solution,
                "resources": resources,
                "risk_flags": [],
            }),
        }

    def generate_report(self, data: dict) -> bytes:
        """Generate a .docx report using the report generator."""
        from src.reports.docx_generator import generate_report_bytes
        return generate_report_bytes(data)
