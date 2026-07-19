from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, ForeignKey, JSON, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="student", nullable=False)  # student | faculty | admin
    name = Column(String, nullable=False)
    semester = Column(Integer, nullable=True) # Applicable to student
    branch = Column(String, nullable=True)     # Applicable to student
    bio_short = Column(String, nullable=True)
    bio_full = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    streak_count = Column(Integer, default=0)
    streak_visibility = Column(String, default="public")  # public | friends | private

    # Relationships
    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")
    sent_endorsements = relationship("Endorsement", foreign_keys="[Endorsement.faculty_id]", back_populates="faculty")
    received_endorsements = relationship("Endorsement", foreign_keys="[Endorsement.student_id]", back_populates="student")
    team_requests = relationship("TeamRequest", back_populates="creator")
    team_applications = relationship("TeamApplication", back_populates="applicant")
    mentor_requests = relationship("MentorRequest", back_populates="student")
    specialization = relationship("FacultySpecialization", uselist=False, back_populates="faculty")
    streak_logs = relationship("StreakLog", back_populates="user")
    leaderboard_opt_ins = relationship("LeaderboardOptIn", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    chats = relationship("ChatParticipant", back_populates="user")
    messages = relationship("Message", back_populates="sender")

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    category = Column(String, nullable=False)  # Languages, Frameworks, AI, Databases, etc.

    user_skills = relationship("UserSkill", back_populates="skill")

class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    proficiency = Column(Integer, default=1)  # 1 to 5
    endorsed_count = Column(Integer, default=0)

    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="user_skills")

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)  # hackathon | paper | certification | project | internship
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    skills = Column(JSON, default=list)  # List of skill names / ids
    date = Column(Date, nullable=False)
    proof_file_url = Column(String, nullable=True) # nullable for cases where there is no proof doc
    verification_status = Column(String, default="unverified") # unverified | ai_flagged | faculty_verified | rejected
    verification_confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="achievements")
    endorsements = relationship("Endorsement", back_populates="achievement", cascade="all, delete-orphan")

class Endorsement(Base):
    __tablename__ = "endorsements"

    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="SET NULL"), nullable=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="SET NULL"), nullable=True)
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    faculty = relationship("User", foreign_keys=[faculty_id], back_populates="sent_endorsements")
    student = relationship("User", foreign_keys=[student_id], back_populates="received_endorsements")
    achievement = relationship("Achievement", back_populates="endorsements")
    skill = relationship("Skill")

class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=False)
    icon_url = Column(String, nullable=False)
    criteria_json = Column(JSON, nullable=False)  # e.g., {"type": "hackathon", "count": 3}

    users = relationship("UserBadge", back_populates="badge")

class UserBadge(Base):
    __tablename__ = "user_badges"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    badge_id = Column(Integer, ForeignKey("badges.id", ondelete="CASCADE"), primary_key=True)
    earned_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="badges")
    badge = relationship("Badge", back_populates="users")

class TeamRequest(Base):
    __tablename__ = "team_requests"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    required_skills = Column(JSON, default=list)  # List of strings
    team_size = Column(Integer, nullable=False)
    deadline = Column(Date, nullable=False)
    status = Column(String, default="active")  # active | closed

    creator = relationship("User", back_populates="team_requests")
    applications = relationship("TeamApplication", back_populates="request", cascade="all, delete-orphan")

class TeamApplication(Base):
    __tablename__ = "team_applications"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("team_requests.id", ondelete="CASCADE"), nullable=False)
    applicant_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending")  # pending | accepted | rejected
    match_score = Column(Float, default=0.0)

    request = relationship("TeamRequest", back_populates="applications")
    applicant = relationship("User", back_populates="team_applications")

class MentorRequest(Base):
    __tablename__ = "mentor_requests"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String, nullable=False)
    description = Column(String, nullable=False)
    required_specialization = Column(JSON, default=list)  # List of strings
    status = Column(String, default="pending")  # pending | matched | closed

    student = relationship("User", back_populates="mentor_requests")

class FacultySpecialization(Base):
    __tablename__ = "faculty_specializations"

    faculty_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    domain = Column(String, nullable=False)
    publications_json = Column(JSON, default=list)  # List of strings/dicts

    faculty = relationship("User", back_populates="specialization")

class Connection(Base):
    __tablename__ = "connections"

    user_a_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    user_b_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    context_type = Column(String, nullable=False)  # team | mentor
    context_id = Column(Integer, nullable=False)   # team_application_id or mentor_request_id etc.
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_a_id", "user_b_id", name="uq_user_connections"),
    )

class StreakLog(Base):
    __tablename__ = "streak_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    activity_type = Column(String, nullable=False)  # login | achievement_created | endorsement

    user = relationship("User", back_populates="streak_logs")

class LeaderboardOptIn(Base):
    __tablename__ = "leaderboard_opt_ins"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    category = Column(String, primary_key=True)  # hackathons | leetcode | papers | overall
    external_handle = Column(String, nullable=True)
    visible_to_friends = Column(Boolean, default=True)

    user = relationship("User", back_populates="leaderboard_opt_ins")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type = Column(String, nullable=False)  # verified | flagged | match | endorsement | streak_risk
    payload_json = Column(JSON, default=dict)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    is_bot_chat = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    participants = relationship("ChatParticipant", back_populates="chat", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="participants")
    user = relationship("User", back_populates="chats")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True) # nullable for bot
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="messages")
