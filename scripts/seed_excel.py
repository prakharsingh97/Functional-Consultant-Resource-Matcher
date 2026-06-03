"""Seed the Excel database with 35 consultants across diverse profiles.

Creates 4 sheets: users, skills, levels, user_skills.
Run: source .venv/bin/activate && python scripts/seed_excel.py
"""
import os
import random
import uuid
from datetime import datetime, timedelta

import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUTPUT = os.path.join(DATA_DIR, "consultant_database.xlsx")

# ---------------------------------------------------------------------------
# 1. SKILLS — ~35 skills across 7 categories
# ---------------------------------------------------------------------------
SKILLS = [
    # Engineering
    ("SK01", "Python", "Engineering", "Python programming language"),
    ("SK02", "JavaScript", "Engineering", "JavaScript / TypeScript development"),
    ("SK03", "Java", "Engineering", "Java enterprise development"),
    ("SK04", "Go", "Engineering", "Go language for backend services"),
    ("SK05", "C#", "Engineering", "C# and .NET development"),
    ("SK06", "FastAPI", "Engineering", "FastAPI web framework"),
    ("SK07", "Django", "Engineering", "Django web framework"),
    ("SK08", "React", "Engineering", "React frontend library"),
    ("SK09", "Node.js", "Engineering", "Node.js server-side runtime"),
    ("SK10", "SQL", "Engineering", "SQL query language and database design"),
    # Cloud / DevOps
    ("SK11", "AWS", "Cloud", "Amazon Web Services"),
    ("SK12", "Azure", "Cloud", "Microsoft Azure"),
    ("SK13", "GCP", "Cloud", "Google Cloud Platform"),
    ("SK14", "Docker", "Cloud", "Containerization with Docker"),
    ("SK15", "Kubernetes", "Cloud", "Container orchestration with K8s"),
    ("SK16", "Terraform", "Cloud", "Infrastructure as Code with Terraform"),
    ("SK17", "CI/CD", "Cloud", "Continuous Integration / Continuous Deployment"),
    # AI/ML
    ("SK18", "LangChain", "AI/ML", "LangChain framework for LLM apps"),
    ("SK19", "TensorFlow", "AI/ML", "TensorFlow machine learning framework"),
    ("SK20", "PyTorch", "AI/ML", "PyTorch machine learning framework"),
    ("SK21", "NLP", "AI/ML", "Natural Language Processing"),
    ("SK22", "Prompt Engineering", "AI/ML", "Crafting effective LLM prompts"),
    # Data
    ("SK23", "PostgreSQL", "Data", "PostgreSQL relational database"),
    ("SK24", "MongoDB", "Data", "MongoDB NoSQL database"),
    ("SK25", "Snowflake", "Data", "Snowflake cloud data warehouse"),
    ("SK26", "ETL Pipelines", "Data", "Extract Transform Load data pipelines"),
    ("SK27", "Power BI", "Data", "Power BI business intelligence"),
    # Product / Management
    ("SK28", "Scrum", "Management", "Scrum agile framework"),
    ("SK29", "Product Management", "Management", "Product strategy and roadmap"),
    ("SK30", "Program Management", "Management", "Multi-project program coordination"),
    ("SK31", "Jira", "Management", "Jira project tracking"),
    ("SK32", "Stakeholder Management", "Management", "Managing stakeholder expectations"),
    # Security / Sysadmin
    ("SK33", "Linux Admin", "Sysadmin", "Linux system administration"),
    ("SK34", "Cybersecurity", "Sysadmin", "Information security practices"),
    ("SK35", "Networking", "Sysadmin", "Network infrastructure and protocols"),
    # Domain
    ("SK36", "Legal Tech", "Domain", "Legal technology and regulatory compliance"),
    ("SK37", "FinTech", "Domain", "Financial technology systems"),
    ("SK38", "HealthTech", "Domain", "Healthcare technology and HIPAA"),
]

# ---------------------------------------------------------------------------
# 2. LEVELS — fixed 4-tier system
# ---------------------------------------------------------------------------
LEVELS = [
    (1, "Beginner", 0.25),
    (2, "Intermediate", 0.50),
    (3, "Advanced", 0.75),
    (4, "Expert", 1.00),
]

# ---------------------------------------------------------------------------
# 3. USERS — 35 consultants with Indian and American names, diverse roles
# ---------------------------------------------------------------------------
USERS = [
    # Indian names
    ("U01", "Aarav Sharma", "aarav.sharma@nexus.com", "Senior Backend Engineer", 35, "Asia/Kolkata"),
    ("U02", "Priya Patel", "priya.patel@nexus.com", "AI/ML Engineer", 30, "Asia/Kolkata"),
    ("U03", "Rohan Gupta", "rohan.gupta@nexus.com", "Cloud Architect", 40, "Asia/Kolkata"),
    ("U04", "Ananya Reddy", "ananya.reddy@nexus.com", "Full Stack Developer", 25, "Asia/Kolkata"),
    ("U05", "Vikram Singh", "vikram.singh@nexus.com", "DevOps Engineer", 30, "Asia/Kolkata"),
    ("U06", "Deepika Nair", "deepika.nair@nexus.com", "Data Engineer", 20, "Asia/Kolkata"),
    ("U07", "Arjun Kumar", "arjun.kumar@nexus.com", "Scrum Master", 40, "Asia/Kolkata"),
    ("U08", "Meera Iyer", "meera.iyer@nexus.com", "Product Manager", 35, "Asia/Kolkata"),
    ("U09", "Karthik Venkataraman", "karthik.v@nexus.com", "Security Engineer", 25, "Asia/Kolkata"),
    ("U10", "Shruti Deshmukh", "shruti.d@nexus.com", "QA Lead", 30, "Asia/Kolkata"),
    ("U11", "Rahul Joshi", "rahul.joshi@nexus.com", "Database Administrator", 35, "Asia/Kolkata"),
    ("U12", "Nisha Kulkarni", "nisha.k@nexus.com", "Frontend Engineer", 20, "Asia/Kolkata"),
    ("U13", "Suresh Menon", "suresh.menon@nexus.com", "Solutions Architect", 40, "Asia/Kolkata"),
    ("U14", "Pooja Chatterjee", "pooja.c@nexus.com", "NLP Researcher", 15, "Asia/Kolkata"),
    ("U15", "Amit Verma", "amit.verma@nexus.com", "Platform Engineer", 30, "Asia/Kolkata"),
    ("U16", "Divya Saxena", "divya.saxena@nexus.com", "Program Manager", 35, "Asia/Kolkata"),
    ("U17", "Nikhil Mehta", "nikhil.mehta@nexus.com", "ML Ops Engineer", 25, "Asia/Kolkata"),
    ("U18", "Kavita Rao", "kavita.rao@nexus.com", "BI Analyst", 30, "Asia/Kolkata"),
    # American names
    ("U19", "Sarah Mitchell", "sarah.mitchell@nexus.com", "Senior Frontend Engineer", 30, "US/Eastern"),
    ("U20", "James O'Brien", "james.obrien@nexus.com", "Staff Backend Engineer", 35, "US/Eastern"),
    ("U21", "Emily Chen", "emily.chen@nexus.com", "Data Scientist", 25, "US/Pacific"),
    ("U22", "Marcus Johnson", "marcus.johnson@nexus.com", "Cloud Engineer", 40, "US/Central"),
    ("U23", "Rachel Kim", "rachel.kim@nexus.com", "Product Manager", 30, "US/Pacific"),
    ("U24", "David Thompson", "david.thompson@nexus.com", "Systems Administrator", 35, "US/Eastern"),
    ("U25", "Lauren Williams", "lauren.williams@nexus.com", "Full Stack Developer", 20, "US/Pacific"),
    ("U26", "Chris Martinez", "chris.martinez@nexus.com", "Security Analyst", 30, "US/Central"),
    ("U27", "Amanda Foster", "amanda.foster@nexus.com", "Scrum Master", 40, "US/Eastern"),
    ("U28", "Tyler Brooks", "tyler.brooks@nexus.com", "DevOps Lead", 25, "US/Pacific"),
    ("U29", "Jessica Nguyen", "jessica.nguyen@nexus.com", "AI Engineer", 35, "US/Pacific"),
    ("U30", "Ryan Davis", "ryan.davis@nexus.com", "Database Engineer", 30, "US/Eastern"),
    ("U31", "Megan Parker", "megan.parker@nexus.com", "Technical Program Manager", 20, "US/Central"),
    ("U32", "Brandon Lee", "brandon.lee@nexus.com", "Backend Engineer", 35, "US/Pacific"),
    ("U33", "Samantha Scott", "samantha.scott@nexus.com", "FinTech Analyst", 25, "US/Eastern"),
    ("U34", "Kevin Wright", "kevin.wright@nexus.com", "Infrastructure Engineer", 40, "US/Central"),
    ("U35", "Olivia Hall", "olivia.hall@nexus.com", "UX Engineer", 30, "US/Pacific"),
]

# ---------------------------------------------------------------------------
# 4. USER_SKILLS — realistic skill assignments per role
# ---------------------------------------------------------------------------
# Format: (user_index_0based, [list of (skill_id, level_id, years_exp)])
ROLE_SKILLS = {
    # U01 - Aarav Sharma: Senior Backend Engineer
    0: [("SK01", 4, 8), ("SK06", 4, 5), ("SK10", 3, 6), ("SK23", 3, 5), ("SK09", 2, 3)],
    # U02 - Priya Patel: AI/ML Engineer
    1: [("SK01", 4, 7), ("SK19", 3, 4), ("SK20", 3, 3), ("SK21", 3, 4), ("SK18", 3, 2)],
    # U03 - Rohan Gupta: Cloud Architect
    2: [("SK11", 4, 8), ("SK12", 3, 4), ("SK14", 4, 6), ("SK15", 3, 4), ("SK16", 4, 5)],
    # U04 - Ananya Reddy: Full Stack Developer
    3: [("SK02", 3, 4), ("SK08", 3, 3), ("SK01", 3, 3), ("SK09", 3, 4), ("SK10", 2, 2)],
    # U05 - Vikram Singh: DevOps Engineer
    4: [("SK14", 4, 6), ("SK15", 3, 4), ("SK17", 4, 5), ("SK16", 3, 3), ("SK11", 3, 4)],
    # U06 - Deepika Nair: Data Engineer
    5: [("SK01", 3, 5), ("SK23", 3, 4), ("SK26", 3, 4), ("SK25", 2, 2), ("SK10", 4, 6)],
    # U07 - Arjun Kumar: Scrum Master
    6: [("SK28", 4, 7), ("SK31", 4, 6), ("SK32", 3, 5), ("SK29", 2, 3), ("SK30", 2, 2)],
    # U08 - Meera Iyer: Product Manager
    7: [("SK29", 4, 8), ("SK32", 4, 7), ("SK28", 3, 4), ("SK31", 3, 5), ("SK27", 2, 2)],
    # U09 - Karthik Venkataraman: Security Engineer
    8: [("SK34", 3, 4), ("SK33", 3, 4), ("SK11", 2, 3), ("SK35", 3, 5), ("SK15", 2, 2)],
    # U10 - Shruti Deshmukh: QA Lead
    9: [("SK01", 3, 4), ("SK06", 2, 2), ("SK28", 3, 3), ("SK31", 3, 4), ("SK10", 2, 3)],
    # U11 - Rahul Joshi: DBA
    10: [("SK23", 4, 10), ("SK10", 4, 10), ("SK24", 3, 4), ("SK26", 3, 5), ("SK11", 2, 3)],
    # U12 - Nisha Kulkarni: Frontend Engineer
    11: [("SK02", 3, 4), ("SK08", 4, 5), ("SK09", 2, 2), ("SK01", 2, 2)],
    # U13 - Suresh Menon: Solutions Architect
    12: [("SK11", 4, 9), ("SK12", 3, 5), ("SK13", 2, 3), ("SK16", 3, 4), ("SK03", 3, 7)],
    # U14 - Pooja Chatterjee: NLP Researcher
    13: [("SK21", 4, 6), ("SK01", 4, 5), ("SK20", 3, 3), ("SK22", 3, 3), ("SK18", 2, 2)],
    # U15 - Amit Verma: Platform Engineer
    14: [("SK11", 3, 5), ("SK14", 3, 4), ("SK15", 3, 4), ("SK01", 3, 5), ("SK04", 2, 2)],
    # U16 - Divya Saxena: Program Manager
    15: [("SK30", 4, 8), ("SK32", 4, 7), ("SK28", 3, 5), ("SK31", 3, 6), ("SK29", 2, 3)],
    # U17 - Nikhil Mehta: ML Ops Engineer
    16: [("SK01", 3, 4), ("SK14", 3, 3), ("SK19", 2, 2), ("SK17", 3, 3), ("SK11", 2, 3)],
    # U18 - Kavita Rao: BI Analyst
    17: [("SK27", 4, 6), ("SK10", 3, 5), ("SK25", 3, 4), ("SK26", 2, 3), ("SK23", 2, 3)],
    # U19 - Sarah Mitchell: Senior Frontend Engineer
    18: [("SK08", 4, 7), ("SK02", 4, 8), ("SK09", 3, 4), ("SK01", 2, 3)],
    # U20 - James O'Brien: Staff Backend Engineer
    19: [("SK01", 4, 10), ("SK03", 4, 8), ("SK06", 3, 4), ("SK23", 3, 6), ("SK11", 3, 5)],
    # U21 - Emily Chen: Data Scientist
    20: [("SK01", 4, 6), ("SK20", 4, 5), ("SK19", 3, 4), ("SK21", 3, 3), ("SK10", 3, 4)],
    # U22 - Marcus Johnson: Cloud Engineer
    21: [("SK11", 4, 7), ("SK14", 4, 6), ("SK15", 3, 5), ("SK16", 3, 4), ("SK17", 3, 5)],
    # U23 - Rachel Kim: Product Manager
    22: [("SK29", 4, 7), ("SK32", 3, 5), ("SK28", 3, 4), ("SK27", 2, 3), ("SK08", 2, 2)],
    # U24 - David Thompson: Sysadmin
    23: [("SK33", 4, 12), ("SK35", 4, 10), ("SK34", 3, 5), ("SK14", 3, 4), ("SK11", 2, 3)],
    # U25 - Lauren Williams: Full Stack Developer
    24: [("SK02", 3, 3), ("SK01", 3, 3), ("SK08", 3, 3), ("SK06", 2, 2), ("SK10", 2, 2)],
    # U26 - Chris Martinez: Security Analyst
    25: [("SK34", 3, 5), ("SK33", 3, 4), ("SK11", 2, 3), ("SK35", 2, 3), ("SK15", 2, 2)],
    # U27 - Amanda Foster: Scrum Master
    26: [("SK28", 4, 8), ("SK31", 4, 7), ("SK32", 3, 6), ("SK30", 3, 5)],
    # U28 - Tyler Brooks: DevOps Lead
    27: [("SK14", 4, 7), ("SK15", 4, 6), ("SK17", 4, 6), ("SK11", 3, 5), ("SK16", 3, 4)],
    # U29 - Jessica Nguyen: AI Engineer
    28: [("SK01", 4, 6), ("SK18", 4, 3), ("SK22", 4, 3), ("SK20", 3, 3), ("SK06", 3, 2)],
    # U30 - Ryan Davis: Database Engineer
    29: [("SK23", 4, 9), ("SK24", 3, 5), ("SK10", 4, 9), ("SK26", 3, 4), ("SK11", 2, 3)],
    # U31 - Megan Parker: Technical Program Manager
    30: [("SK30", 4, 6), ("SK28", 3, 4), ("SK32", 3, 5), ("SK31", 3, 4), ("SK37", 2, 2)],
    # U32 - Brandon Lee: Backend Engineer
    31: [("SK01", 4, 7), ("SK04", 3, 4), ("SK06", 4, 4), ("SK23", 3, 5), ("SK14", 2, 3)],
    # U33 - Samantha Scott: FinTech Analyst
    32: [("SK37", 4, 6), ("SK10", 3, 5), ("SK27", 3, 4), ("SK01", 2, 3), ("SK26", 2, 3)],
    # U34 - Kevin Wright: Infrastructure Engineer
    33: [("SK33", 4, 10), ("SK14", 3, 5), ("SK11", 3, 6), ("SK16", 3, 5), ("SK35", 4, 8)],
    # U35 - Olivia Hall: UX Engineer
    34: [("SK08", 3, 4), ("SK02", 3, 4), ("SK01", 2, 2), ("SK27", 2, 2)],
}


def _random_last_used() -> str:
    """Return a random date in the last 12 months as YYYY-MM-DD."""
    days_ago = random.randint(1, 365)
    dt = datetime.now() - timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%d")


def _random_created_at() -> str:
    """Return a random date in the last 3 years as YYYY-MM-DD."""
    days_ago = random.randint(30, 1100)
    dt = datetime.now() - timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%d")


def seed() -> None:
    """Write all 4 sheets to the Excel database file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    random.seed(42)

    # --- Skills sheet ---
    skills_df = pd.DataFrame(SKILLS, columns=["skill_id", "skill_name", "category", "description"])

    # --- Levels sheet ---
    levels_df = pd.DataFrame(LEVELS, columns=["level_id", "level_name", "score_weight"])

    # --- Users sheet ---
    users_rows = []
    for uid, name, email, role, avail, tz in USERS:
        users_rows.append({
            "user_id": uid,
            "full_name": name,
            "email": email,
            "role": role,
            "availability": avail,
            "timezone": tz,
            "created_at": _random_created_at(),
        })
    users_df = pd.DataFrame(users_rows)

    # --- User Skills sheet ---
    us_rows = []
    counter = 1
    for user_idx, skill_list in ROLE_SKILLS.items():
        uid = USERS[user_idx][0]
        for skill_id, level_id, years_exp in skill_list:
            us_rows.append({
                "id": f"US{counter:03d}",
                "user_id": uid,
                "skill_id": skill_id,
                "level_id": level_id,
                "years_exp": years_exp,
                "last_used": _random_last_used(),
            })
            counter += 1
    user_skills_df = pd.DataFrame(us_rows)

    # --- Write to Excel ---
    with pd.ExcelWriter(OUTPUT, engine="openpyxl") as writer:
        users_df.to_excel(writer, sheet_name="users", index=False)
        skills_df.to_excel(writer, sheet_name="skills", index=False)
        levels_df.to_excel(writer, sheet_name="levels", index=False)
        user_skills_df.to_excel(writer, sheet_name="user_skills", index=False)

    print(f"Seeded {OUTPUT}")
    print(f"  users:       {len(users_df)} rows")
    print(f"  skills:      {len(skills_df)} rows")
    print(f"  levels:      {len(levels_df)} rows")
    print(f"  user_skills: {len(user_skills_df)} rows")

    # Quick validation: print top skill strengths
    level_weights = dict(zip(levels_df["level_id"], levels_df["score_weight"]))
    user_skills_df["weight"] = user_skills_df["level_id"].map(level_weights)
    strength = user_skills_df.groupby("skill_id")["weight"].sum().reset_index()
    strength.columns = ["skill_id", "strength_score"]
    strength = strength.merge(skills_df, on="skill_id")
    strength = strength.sort_values("strength_score", ascending=False)
    print("\nTop 10 Skill Strength Scores:")
    for _, row in strength.head(10).iterrows():
        print(f"  {row['skill_name']:20s} {row['strength_score']:.2f}")


if __name__ == "__main__":
    seed()
