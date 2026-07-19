from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Any, Dict

# --- Skill Schemas ---
class SkillBase(BaseModel):
    name: str
    category: str

class SkillCreate(SkillBase):
    pass

class SkillOut(SkillBase):
    id: int
    class Config:
        from_attributes = True

class UserSkillOut(BaseModel):
    skill: SkillOut
    proficiency: int
    endorsed_count: int
    class Config:
        from_attributes = True

class UserSkillUpdate(BaseModel):
    skill_name: str
    proficiency: int

# --- Auth & User Schemas ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = Field(..., description="student or faculty or admin")
    name: str
    semester: Optional[int] = None
    branch: Optional[str] = None
    bio_short: Optional[str] = None
    bio_full: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[int] = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    role: str
    name: str
    semester: Optional[int] = None
    branch: Optional[str] = None
    bio_short: Optional[str] = None
    bio_full: Optional[str] = None
    avatar_url: Optional[str] = None
    streak_count: int
    streak_visibility: str
    created_at: datetime
    skills: List[UserSkillOut] = []

    class Config:
        from_attributes = True

# --- Faculty Specialization ---
class FacultySpecializationBase(BaseModel):
    domain: str
    publications_json: List[str] = []

class FacultySpecializationOut(FacultySpecializationBase):
    faculty_id: int
    class Config:
        from_attributes = True

# --- Achievement Schemas ---
class AchievementBase(BaseModel):
    type: str  # hackathon | paper | certification | project | internship
    title: str
    description: str
    skills: List[str] = []
    date: date

class AchievementCreate(AchievementBase):
    pass

class AchievementOut(AchievementBase):
    id: int
    user_id: int
    proof_file_url: Optional[str] = None
    verification_status: str
    verification_confidence: float
    created_at: datetime

    class Config:
        from_attributes = True

# --- Endorsement Schemas ---
class EndorsementCreate(BaseModel):
    student_id: int
    achievement_id: Optional[int] = None
    skill_id: Optional[int] = None
    comment: Optional[str] = None

class EndorsementOut(BaseModel):
    id: int
    faculty_id: int
    student_id: int
    achievement_id: Optional[int]
    skill_id: Optional[int]
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# --- Badge Schemas ---
class BadgeOut(BaseModel):
    id: int
    name: str
    description: str
    icon_url: str
    criteria_json: Dict[str, Any]

    class Config:
        from_attributes = True

class UserBadgeOut(BaseModel):
    badge: BadgeOut
    earned_at: datetime

    class Config:
        from_attributes = True

# --- Team Request Schemas ---
class TeamRequestCreate(BaseModel):
    title: str
    description: str
    required_skills: List[str]
    team_size: int
    deadline: date

class TeamRequestOut(BaseModel):
    id: int
    creator_id: int
    title: str
    description: str
    required_skills: List[str]
    team_size: int
    deadline: date
    status: str
    creator: Optional[UserOut] = None

    class Config:
        from_attributes = True

class TeamApplicationCreate(BaseModel):
    request_id: int

class TeamApplicationOut(BaseModel):
    id: int
    request_id: int
    applicant_id: int
    status: str
    match_score: float
    applicant: Optional[UserOut] = None

    class Config:
        from_attributes = True

# --- Mentor Request Schemas ---
class MentorRequestCreate(BaseModel):
    topic: str
    description: str
    required_specialization: List[str]

class MentorRequestOut(BaseModel):
    id: int
    student_id: int
    topic: str
    description: str
    required_specialization: List[str]
    status: str
    student: Optional[UserOut] = None

    class Config:
        from_attributes = True

# --- Connection Schemas ---
class ConnectionOut(BaseModel):
    user_a_id: int
    user_b_id: int
    context_type: str
    context_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Streak Log & Leaderboard ---
class StreakLogOut(BaseModel):
    id: int
    user_id: int
    date: date
    activity_type: str

    class Config:
        from_attributes = True

class LeaderboardOptInCreate(BaseModel):
    category: str
    external_handle: Optional[str] = None
    visible_to_friends: bool = True

class LeaderboardOptInOut(BaseModel):
    category: str
    external_handle: Optional[str]
    visible_to_friends: bool

    class Config:
        from_attributes = True

class LeaderboardEntry(BaseModel):
    user_id: int
    name: str
    score: int  # count of achievements or streak or overall activity
    avatar_url: Optional[str] = None
    semester: Optional[int] = None
    branch: Optional[str] = None

# --- Notification Schemas ---
class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: str
    payload_json: Dict[str, Any]
    read: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- Chat & Messaging Schemas ---
class MessageCreate(BaseModel):
    content: str

class MessageOut(BaseModel):
    id: int
    chat_id: int
    sender_id: Optional[int]
    content: str
    created_at: datetime
    sender: Optional[UserOut] = None

    class Config:
        from_attributes = True

class ChatParticipantOut(BaseModel):
    user_id: int
    joined_at: datetime
    user: Optional[UserOut] = None

    class Config:
        from_attributes = True

class ChatCreate(BaseModel):
    is_bot_chat: bool = False
    participant_ids: List[int] = []

class ChatOut(BaseModel):
    id: int
    is_bot_chat: bool
    created_at: datetime
    participants: List[ChatParticipantOut] = []

    class Config:
        from_attributes = True
