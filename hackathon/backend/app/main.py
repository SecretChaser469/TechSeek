import os
import json
import shutil
import requests
from datetime import datetime, date, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from .database import engine, get_db
from . import models, schemas, auth, privacy

# Setup upload dir
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="TechSeek API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)

@app.get("/api/health")
def health():
    return {"status": "healthy", "time": datetime.utcnow().isoformat()}

# --- UTILITIES: AUTO AWARD BADGES ---
def check_and_award_badges(user_id: int, db: Session):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return
    
    # Get user verified achievements
    verified_achs = db.query(models.Achievement).filter(
        models.Achievement.user_id == user_id,
        models.Achievement.verification_status == 'faculty_verified'
    ).all()

    # Get all badges
    all_badges = db.query(models.Badge).all()
    user_badges = {ub.badge_id for ub in user.badges}

    # Count achievements by type
    ach_counts = {}
    for a in verified_achs:
        ach_counts[a.type] = ach_counts.get(a.type, 0) + 1

    # Check each badge criteria
    for badge in all_badges:
        if badge.id in user_badges:
            continue
        
        criteria = badge.criteria_json or {}
        qualifies = False

        b_type = criteria.get("type")
        b_count = criteria.get("count", 1)

        if b_type == "first":
            if len(verified_achs) >= 1:
                qualifies = True
        elif b_type == "hackathon":
            if ach_counts.get("hackathon", 0) >= b_count:
                qualifies = True
        elif b_type == "paper":
            if ach_counts.get("paper", 0) >= b_count:
                qualifies = True
        elif b_type == "project":
            if ach_counts.get("project", 0) >= b_count:
                qualifies = True
        elif b_type == "internship":
            if ach_counts.get("internship", 0) >= b_count:
                qualifies = True
        elif b_type == "streak":
            if user.streak_count >= b_count:
                qualifies = True
        elif b_type == "diversity":
            # Multi-disciplinary badge (e.g. 3 distinct types)
            unique_types = len(ach_counts.keys())
            if unique_types >= b_count:
                qualifies = True
        elif b_type == "endorsement":
            # Check maximum endorsed skills
            max_endorsed = db.query(func.max(models.UserSkill.endorsed_count)).filter(
                models.UserSkill.user_id == user_id
            ).scalar() or 0
            if max_endorsed >= b_count:
                qualifies = True

        if qualifies:
            db.add(models.UserBadge(user_id=user_id, badge_id=badge.id, earned_at=datetime.utcnow()))
            # Send notification
            notif = models.Notification(
                user_id=user_id,
                type="badge_unlocked",
                payload_json={"badge_name": badge.name, "badge_icon": badge.icon_url},
                read=False
            )
            db.add(notif)
    
    db.commit()


# --- USERS / PROFILE ENDPOINTS ---

@app.get("/api/users/me", response_model=schemas.UserOut)
def get_current_user_profile(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    return current_user

@app.put("/api/users/me")
def update_profile(
    name: Optional[str] = Form(None),
    bio_short: Optional[str] = Form(None),
    bio_full: Optional[str] = Form(None),
    semester: Optional[int] = Form(None),
    branch: Optional[str] = Form(None),
    streak_visibility: Optional[str] = Form(None),
    avatar: Optional[UploadFile] = File(None),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if name is not None:
        current_user.name = name
    if bio_short is not None:
        current_user.bio_short = bio_short
    if bio_full is not None:
        current_user.bio_full = bio_full
    if semester is not None:
        current_user.semester = semester
    if branch is not None:
        current_user.branch = branch
    if streak_visibility is not None:
        current_user.streak_visibility = streak_visibility

    if avatar:
        filename = f"avatar_{current_user.id}_{int(datetime.utcnow().timestamp())}_{avatar.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(avatar.file, buffer)
        current_user.avatar_url = f"/uploads/{filename}"

    db.commit()
    db.refresh(current_user)
    return {"message": "Profile updated successfully"}

@app.get("/api/users/students", response_model=List[dict])
def list_students(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    students = db.query(models.User).filter(models.User.role == "student").all()
    return [privacy.redact_user_profile(s, current_user, db) for s in students]

@app.get("/api/users/students/{student_id}", response_model=dict)
def get_student_profile(
    student_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    student = db.query(models.User).filter(
        models.User.id == student_id,
        models.User.role == "student"
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return privacy.redact_user_profile(student, current_user, db)

@app.get("/api/users/faculty", response_model=List[dict])
def list_faculty(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    faculty = db.query(models.User).filter(models.User.role == "faculty").all()
    return [privacy.redact_user_profile(f, current_user, db) for f in faculty]

@app.put("/api/users/faculty/specialization")
def update_faculty_specialization(
    domain: str = Form(...),
    publications: str = Form("[]"),  # JSON array string
    current_user: models.User = Depends(auth.require_role(["faculty"])),
    db: Session = Depends(get_db)
):
    try:
        pubs = json.loads(publications)
    except Exception:
        pubs = []
        
    spec = db.query(models.FacultySpecialization).filter(
        models.FacultySpecialization.faculty_id == current_user.id
    ).first()
    if not spec:
        spec = models.FacultySpecialization(faculty_id=current_user.id, domain=domain, publications_json=pubs)
        db.add(spec)
    else:
        spec.domain = domain
        spec.publications_json = pubs
    
    db.commit()
    return {"message": "Faculty specialization updated successfully"}

# --- SKILLS ENDPOINTS ---

@app.get("/api/skills", response_model=List[schemas.SkillOut])
def get_all_skills(db: Session = Depends(get_db)):
    return db.query(models.Skill).all()

@app.post("/api/skills", response_model=schemas.SkillOut)
def add_new_skill(
    skill_in: schemas.SkillCreate, 
    current_user: models.User = Depends(auth.require_role(["admin", "faculty"])),
    db: Session = Depends(get_db)
):
    existing = db.query(models.Skill).filter(models.Skill.name == skill_in.name).first()
    if existing:
        return existing
    
    new_skill = models.Skill(name=skill_in.name, category=skill_in.category)
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    return new_skill

@app.post("/api/users/me/skills")
def add_user_skill(
    skill_up: schemas.UserSkillUpdate,
    current_user: models.User = Depends(auth.require_role(["student"])),
    db: Session = Depends(get_db)
):
    skill = db.query(models.Skill).filter(models.Skill.name == skill_up.skill_name).first()
    if not skill:
        skill = models.Skill(name=skill_up.skill_name, category="Other")
        db.add(skill)
        db.commit()
        db.refresh(skill)

    user_skill = db.query(models.UserSkill).filter(
        models.UserSkill.user_id == current_user.id,
        models.UserSkill.skill_id == skill.id
    ).first()

    if user_skill:
        user_skill.proficiency = skill_up.proficiency
    else:
        user_skill = models.UserSkill(
            user_id=current_user.id,
            skill_id=skill.id,
            proficiency=skill_up.proficiency,
            endorsed_count=0
        )
        db.add(user_skill)

    db.commit()
    return {"message": "Skill added/updated successfully"}

@app.delete("/api/users/me/skills/{skill_name}")
def delete_user_skill(
    skill_name: str,
    current_user: models.User = Depends(auth.require_role(["student"])),
    db: Session = Depends(get_db)
):
    skill = db.query(models.Skill).filter(models.Skill.name == skill_name).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    
    user_skill = db.query(models.UserSkill).filter(
        models.UserSkill.user_id == current_user.id,
        models.UserSkill.skill_id == skill.id
    ).first()

    if user_skill:
        db.delete(user_skill)
        db.commit()
    return {"message": "Skill removed from profile"}


# --- ACHIEVEMENTS & VERIFICATION ---

@app.post("/api/achievements", response_model=schemas.AchievementOut)
def create_achievement(
    type: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    skills: str = Form("[]"),
    date_str: str = Form(...),
    proof: Optional[UploadFile] = File(None),
    current_user: models.User = Depends(auth.require_role(["student"])),
    db: Session = Depends(get_db)
):
    try:
        skills_list = json.loads(skills)
    except Exception:
        skills_list = []

    try:
        ach_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD")

    proof_url = None
    verification_status = "unverified"
    verification_confidence = 0.0

    if proof:
        filename = f"proof_{current_user.id}_{int(datetime.utcnow().timestamp())}_{proof.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(proof.file, buffer)
        proof_url = f"/uploads/{filename}"

        # Call MCP server OCR verification
        mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:5000")
        try:
            mcp_res = requests.post(f"{mcp_url}/verify_certificate", json={
                "image_url": filename,
                "claimed_issuer": current_user.name,
                "claimed_event": title,
                "claimed_date": date_str
            }, timeout=10)
            
            if mcp_res.status_code == 200:
                result = mcp_res.json()
                verification_confidence = result.get("confidence", 50.0)
                
                # Check for flags to trigger review
                if len(result.get("flags", [])) > 0 or verification_confidence < 75.0:
                    verification_status = "ai_flagged"
                else:
                    verification_status = "unverified"
        except Exception as e:
            # Fallback when MCP service is loading/offline
            print(f"Error calling MCP verification: {e}")
            verification_status = "unverified"
            verification_confidence = 45.0

    new_achievement = models.Achievement(
        user_id=current_user.id,
        type=type,
        title=title,
        description=description,
        skills=skills_list,
        date=ach_date,
        proof_file_url=proof_url,
        verification_status=verification_status,
        verification_confidence=verification_confidence
    )
    db.add(new_achievement)
    db.commit()
    db.refresh(new_achievement)

    # Log/update activity log for streaks
    today = datetime.utcnow().date()
    streak_log_exists = db.query(models.StreakLog).filter(
        models.StreakLog.user_id == current_user.id,
        models.StreakLog.date == today,
        models.StreakLog.activity_type == "achievement_created"
    ).first()
    
    if not streak_log_exists:
        db.add(models.StreakLog(
            user_id=current_user.id,
            date=today,
            activity_type="achievement_created"
        ))
        db.commit()

    return new_achievement

@app.get("/api/achievements", response_model=List[schemas.AchievementOut])
def get_my_achievements(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(models.Achievement).filter(models.Achievement.user_id == current_user.id).all()

@app.get("/api/achievements/queue")
def get_verification_queue(
    current_user: models.User = Depends(auth.require_role(["faculty", "admin"])),
    db: Session = Depends(db_session := get_db)
):
    # Fetch achievements requiring review: unverified or ai_flagged
    achs = db.query(models.Achievement).filter(
        models.Achievement.verification_status.in_(["unverified", "ai_flagged"])
    ).all()
    
    # Enrich achievement listing with user names for review ease
    res = []
    for a in achs:
        res.append({
            "id": a.id,
            "user_id": a.user_id,
            "student_name": a.user.name,
            "type": a.type,
            "title": a.title,
            "description": a.description,
            "skills": a.skills,
            "date": a.date.isoformat(),
            "proof_file_url": a.proof_file_url,
            "verification_status": a.verification_status,
            "verification_confidence": a.verification_confidence
        })
    return res

@app.post("/api/achievements/{achievement_id}/verify")
def verify_achievement(
    achievement_id: int,
    approve: bool,  # Query or post body
    current_user: models.User = Depends(auth.require_role(["faculty", "admin"])),
    db: Session = Depends(get_db)
):
    ach = db.query(models.Achievement).filter(models.Achievement.id == achievement_id).first()
    if not ach:
        raise HTTPException(status_code=404, detail="Achievement not found")

    old_status = ach.verification_status
    ach.verification_status = "faculty_verified" if approve else "rejected"
    db.commit()

    # Dynamic notifications
    notif = models.Notification(
        user_id=ach.user_id,
        type="verification_approved" if approve else "verification_rejected",
        payload_json={"achievement_title": ach.title, "reviewer_name": current_user.name},
        read=False
    )
    db.add(notif)
    db.commit()

    if approve:
        # Check and update badges
        check_and_award_badges(ach.user_id, db)
        
        # Auto-award skill points structure (add to student profile default 1 proficiency if verified)
        for skill_name in ach.skills:
            skill = db.query(models.Skill).filter(models.Skill.name == skill_name).first()
            if not skill:
                skill = models.Skill(name=skill_name, category="Other")
                db.add(skill)
                db.commit()
                db.refresh(skill)

            user_skill = db.query(models.UserSkill).filter(
                models.UserSkill.user_id == ach.user_id,
                models.UserSkill.skill_id == skill.id
            ).first()

            if not user_skill:
                new_us = models.UserSkill(
                    user_id=ach.user_id,
                    skill_id=skill.id,
                    proficiency=2, # auto-set to 2 since verified
                    endorsed_count=0
                )
                db.add(new_us)
            else:
                user_skill.proficiency = min(5, user_skill.proficiency + 1)
            
            db.commit()

    return {"message": f"Achievement {ach.title} verified status updated.", "status": ach.verification_status}

@app.post("/api/achievements/{achievement_id}/endorse")
def endorse_achievement(
    achievement_id: int,
    comment: Optional[str] = Form(None),
    skill_name: Optional[str] = Form(None),
    current_user: models.User = Depends(auth.require_role(["faculty"])),
    db: Session = Depends(get_db)
):
    ach = db.query(models.Achievement).filter(models.Achievement.id == achievement_id).first()
    if not ach:
        raise HTTPException(status_code=404, detail="Achievement not found")

    target_skill_id = None
    if skill_name:
        skill = db.query(models.Skill).filter(models.Skill.name == skill_name).first()
        if skill:
            target_skill_id = skill.id
            
            # Increment endorsed count
            user_skill = db.query(models.UserSkill).filter(
                models.UserSkill.user_id == ach.user_id,
                models.UserSkill.skill_id == skill.id
            ).first()
            if user_skill:
                user_skill.endorsed_count += 1
                db.commit()

    # Create endorsement
    endorsement = models.Endorsement(
        faculty_id=current_user.id,
        student_id=ach.user_id,
        achievement_id=ach.id,
        skill_id=target_skill_id,
        comment=comment
    )
    db.add(endorsement)
    
    # Notify student
    notif = models.Notification(
        user_id=ach.user_id,
        type="endorsement_received",
        payload_json={"achievement_title": ach.title, "faculty_name": current_user.name, "comment": comment},
        read=False
    )
    db.add(notif)
    db.commit()

    # Recheck badges
    check_and_award_badges(ach.user_id, db)

    return {"message": "Endorsement recorded successfully"}


# --- TEAMS COLLABORATION ---

@app.post("/api/teams/requests", response_model=schemas.TeamRequestOut)
def create_team_request(
    req_in: schemas.TeamRequestCreate,
    current_user: models.User = Depends(auth.require_role(["student"])),
    db: Session = Depends(get_db)
):
    new_req = models.TeamRequest(
        creator_id=current_user.id,
        title=req_in.title,
        description=req_in.description,
        required_skills=req_in.required_skills,
        team_size=req_in.team_size,
        deadline=req_in.deadline,
        status="active"
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return new_req

@app.get("/api/teams/requests", response_model=List[schemas.TeamRequestOut])
def get_team_requests(db: Session = Depends(get_db)):
    return db.query(models.TeamRequest).filter(models.TeamRequest.status == "active").all()

@app.get("/api/teams/requests/{request_id}", response_model=schemas.TeamRequestOut)
def get_team_request_details(request_id: int, db: Session = Depends(get_db)):
    req = db.query(models.TeamRequest).filter(models.TeamRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    return req

@app.post("/api/teams/requests/{request_id}/apply", response_model=schemas.TeamApplicationOut)
def apply_to_team(
    request_id: int,
    current_user: models.User = Depends(auth.require_role(["student"])),
    db: Session = Depends(get_db)
):
    req = db.query(models.TeamRequest).filter(models.TeamRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Team request not found")

    if req.creator_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot apply to your own team request")

    # Check duplicate application
    dup = db.query(models.TeamApplication).filter(
        models.TeamApplication.request_id == request_id,
        models.TeamApplication.applicant_id == current_user.id
    ).first()
    if dup:
        return dup

    # Retrieve match score from MCP
    mcp_url = os.getenv("MCP_SERVER_URL", "http://mcp-server:5000")
    match_score = 40.0
    try:
        # We query the suggests_team_matches from MCP and filter for this student
        mcp_res = requests.post(f"{mcp_url}/suggest_team_matches", json={"request_id": request_id}, timeout=5)
        if mcp_res.status_code == 200:
            candidates = mcp_res.json().get("candidates", [])
            for cand in candidates:
                if cand["student_id"] == current_user.id:
                    match_score = cand["match_score"]
                    break
    except Exception:
        # Match score fallback logic
        intersection = len(set(req.required_skills) & {us.skill.name for us in current_user.skills})
        match_score = (intersection / len(req.required_skills) * 100.0) if req.required_skills else 50.0

    new_app = models.TeamApplication(
        request_id=request_id,
        applicant_id=current_user.id,
        status="pending",
        match_score=match_score
    )
    db.add(new_app)
    
    # Notify creator
    notif = models.Notification(
        user_id=req.creator_id,
        type="team_application",
        payload_json={"request_title": req.title, "applicant_name": current_user.name},
        read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(new_app)
    return new_app

@app.get("/api/teams/requests/{request_id}/applications", response_model=List[schemas.TeamApplicationOut])
def get_request_applications(
    request_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(models.TeamRequest).filter(models.TeamRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    if req.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can inspect applications")
    
    return db.query(models.TeamApplication).filter(models.TeamApplication.request_id == request_id).all()

@app.put("/api/teams/applications/{application_id}/status")
def update_application_status(
    application_id: int,
    status: str,  # "accepted" or "rejected"
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    app_record = db.query(models.TeamApplication).filter(models.TeamApplication.id == application_id).first()
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")
    
    req = app_record.request
    if req.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorised status alteration")
    
    app_record.status = status
    db.commit()

    # Dynamic Connection Unlock on Approval
    if status == "accepted":
        # Check connection existense
        a_id = min(req.creator_id, app_record.applicant_id)
        b_id = max(req.creator_id, app_record.applicant_id)

        existing_conn = db.query(models.Connection).filter(
            models.Connection.user_a_id == a_id,
            models.Connection.user_b_id == b_id
        ).first()

        if not existing_conn:
            db.add(models.Connection(
                user_a_id=a_id,
                user_b_id=b_id,
                context_type="team",
                context_id=req.id
            ))
            
        # Send connection notification
        db.add(models.Notification(
            user_id=app_record.applicant_id,
            type="connection_unlocked",
            payload_json={"partner_name": current_user.name, "context": f"team request: {req.title}"},
            read=False
        ))
        db.commit()

    return {"message": f"Application status set to {status}."}


# --- MENTOR MATCHES ---

@app.post("/api/mentors/requests", response_model=schemas.MentorRequestOut)
def create_mentor_request(
    req_in: schemas.MentorRequestCreate,
    current_user: models.User = Depends(auth.require_role(["student"])),
    db: Session = Depends(get_db)
):
    new_req = models.MentorRequest(
        student_id=current_user.id,
        topic=req_in.topic,
        description=req_in.description,
        required_specialization=req_in.required_specialization,
        status="pending"
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return new_req

@app.get("/api/mentors/requests", response_model=List[schemas.MentorRequestOut])
def get_mentor_requests(db: Session = Depends(get_db)):
    return db.query(models.MentorRequest).all()

@app.post("/api/mentors/requests/{request_id}/match")
def match_mentor_request(
    request_id: int,
    current_user: models.User = Depends(auth.require_role(["faculty"])),
    db: Session = Depends(get_db)
):
    req = db.query(models.MentorRequest).filter(models.MentorRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Mentor request not found")

    req.status = "matched"
    
    # Establish connection
    a_id = min(req.student_id, current_user.id)
    b_id = max(req.student_id, current_user.id)
    
    existing = db.query(models.Connection).filter(
        models.Connection.user_a_id == a_id,
        models.Connection.user_b_id == b_id
    ).first()
    
    if not existing:
        db.add(models.Connection(
            user_a_id=a_id,
            user_b_id=b_id,
            context_type="mentor",
            context_id=req.id
        ))

    db.add(models.Notification(
        user_id=req.student_id,
        type="connection_unlocked",
        payload_json={"partner_name": current_user.name, "context": f"faculty mentoring topic: {req.topic}"},
        read=False
    ))
    db.commit()

    return {"message": "Mentorship accepted. Profile unlocked."}

# --- CONNECTIONS ---

@app.get("/api/connections")
def list_my_connections(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    conns = db.query(models.Connection).filter(
        (models.Connection.user_a_id == current_user.id) | 
        (models.Connection.user_b_id == current_user.id)
    ).all()

    res = []
    for c in conns:
        partner_id = c.user_b_id if c.user_a_id == current_user.id else c.user_a_id
        partner = db.query(models.User).filter(models.User.id == partner_id).first()
        if partner:
            res.append({
                "partner_id": partner.id,
                "name": partner.name,
                "role": partner.role,
                "email": partner.email,
                "avatar_url": partner.avatar_url,
                "bio_short": partner.bio_short,
                "context_type": c.context_type
            })
    return res


# --- GAMIFICATION ---

@app.get("/api/gamification/badges")
def list_badges(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    badges = db.query(models.Badge).all()
    user_badges = {ub.badge_id: ub.earned_at for ub in current_user.badges}

    res = []
    for b in badges:
        res.append({
            "id": b.id,
            "name": b.name,
            "description": b.description,
            "icon_url": b.icon_url,
            "earned_at": user_badges.get(b.id, None)
        })
    return res

@app.get("/api/gamification/leaderboard")
def get_leaderboard(
    category: str = "overall",  # overall | hackathons | papers | leetcode
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Query for students who registered (opted-in) for leaderboards
    # Category matches leaderboard opt-in category
    opt_ins = db.query(models.LeaderboardOptIn).filter(
        models.LeaderboardOptIn.category == category
    ).all()
    
    opted_in_user_ids = {o.user_id for o in opt_ins}

    # Fetch all students
    students = db.query(models.User).filter(models.User.role == "student").all()
    
    leaderboard_data = []

    for s in students:
        # Check standard leaderboard opt-in constraints
        # By default, overall is open to all students, others depend on handles setup
        # If category requires handle check:
        # LeetCode category is only open if handle is linked
        if category != "overall" and s.id not in opted_in_user_ids:
            continue
        
        # Check visibility
        opt_in_record = db.query(models.LeaderboardOptIn).filter(
            models.LeaderboardOptIn.user_id == s.id,
            models.LeaderboardOptIn.category == category
        ).first()

        if opt_in_record and not opt_in_record.visible_to_friends:
            # Check friendship relation
            is_friend = privacy.check_connection(db, s.id, current_user.id)
            if not is_friend and s.id != current_user.id:
                # Omit/skip if user visible_to_friends is active and assessor isn't connected
                continue

        score = 0
        if category == "overall":
            # Count total verified achievements + streak
            score = len([a for a in s.achievements if a.verification_status == 'faculty_verified']) * 10 + s.streak_count
        elif category == "hackathons":
            score = len([a for a in s.achievements if a.verification_status == 'faculty_verified' and a.type == 'hackathon'])
        elif category == "papers":
            score = len([a for a in s.achievements if a.verification_status == 'faculty_verified' and a.type == 'paper'])
        elif category == "leetcode":
            # LeetCode score can mock external stats or count coding streaks
            score = s.streak_count * 2

        leaderboard_data.append({
            "user_id": s.id,
            "name": s.name,
            "avatar_url": s.avatar_url,
            "semester": s.semester,
            "branch": s.branch,
            "score": score
        })

    # Sort score descending
    leaderboard_data.sort(key=lambda x: x["score"], reverse=True)
    return leaderboard_data

@app.post("/api/gamification/leaderboard/opt-in")
def opt_in_leaderboard(
    opt: schemas.LeaderboardOptInCreate,
    current_user: models.User = Depends(auth.require_role(["student"])),
    db: Session = Depends(get_db)
):
    entry = db.query(models.LeaderboardOptIn).filter(
        models.LeaderboardOptIn.user_id == current_user.id,
        models.LeaderboardOptIn.category == opt.category
    ).first()

    if not entry:
        entry = models.LeaderboardOptIn(
            user_id=current_user.id,
            category=opt.category,
            external_handle=opt.external_handle,
            visible_to_friends=opt.visible_to_friends
        )
        db.add(entry)
    else:
        entry.external_handle = opt.external_handle
        entry.visible_to_friends = opt.visible_to_friends
    
    db.commit()
    return {"message": "Configuration registered successfully"}


# --- NOTIFICATIONS ---

@app.get("/api/notifications", response_model=List[schemas.NotificationOut])
def get_my_notifications(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(models.Notification).filter(models.Notification.user_id == current_user.id).order_by(models.Notification.created_at.desc()).all()

@app.put("/api/notifications/{notification_id}/read")
def read_notification(
    notification_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    notif = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).first()
    if notif:
        notif.read = True
        db.commit()
    return {"message": "Notification marked as read."}


# --- ACCREDITATION / ADMIN METRICS ---

@app.get("/api/admin/metrics")
def get_admin_metrics(
    current_user: models.User = Depends(auth.require_role(["admin"])),
    db: Session = Depends(get_db)
):
    # Total students and faculty counts
    total_students = db.query(models.User).filter(models.User.role == "student").count()
    total_faculty = db.query(models.User).filter(models.User.role == "faculty").count()

    # Total accomplishments verified vs total registered
    verified = db.query(models.Achievement).filter(models.Achievement.verification_status == "faculty_verified").count()
    flagged = db.query(models.Achievement).filter(models.Achievement.verification_status == "ai_flagged").count()
    unverified = db.query(models.Achievement).filter(models.Achievement.verification_status == "unverified").count()

    # Categories breakdown
    cats = db.query(models.Achievement.type, func.count(models.Achievement.id)).filter(
        models.Achievement.verification_status == "faculty_verified"
    ).group_by(models.Achievement.type).all()
    breakdown = {c[0]: c[1] for c in cats}

    # Department/Branch breakdowns
    dept_achs = db.query(models.User.branch, func.count(models.Achievement.id)).join(
        models.Achievement, models.User.id == models.Achievement.user_id
    ).filter(
        models.Achievement.verification_status == "faculty_verified"
    ).group_by(models.User.branch).all()
    dept_breakdown = {d[0]: d[1] for d in dept_achs if d[0]}

    return {
        "users": {
            "students": total_students,
            "faculty": total_faculty
        },
        "achievements": {
            "verified": verified,
            "flagged": flagged,
            "unverified_pending": unverified,
            "total": verified + flagged + unverified
        },
        "achievements_by_type": breakdown,
        "achievements_by_department": dept_breakdown
    }

# --- CHAT & MESSAGING ---
@app.get("/api/chats", response_model=List[schemas.ChatOut])
def list_my_chats(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    chats = db.query(models.Chat).join(models.ChatParticipant).filter(models.ChatParticipant.user_id == current_user.id).all()
    return chats

@app.post("/api/chats", response_model=schemas.ChatOut)
def create_chat(
    chat_in: schemas.ChatCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    participant_ids = set(chat_in.participant_ids)
    participant_ids.add(current_user.id)
    
    new_chat = models.Chat(is_bot_chat=chat_in.is_bot_chat)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    
    for uid in participant_ids:
        # Check if user exists
        u = db.query(models.User).filter_by(id=uid).first()
        if u:
            cp = models.ChatParticipant(chat_id=new_chat.id, user_id=uid)
            db.add(cp)
    
    db.commit()
    db.refresh(new_chat)
    return new_chat

@app.get("/api/chats/{chat_id}/messages", response_model=List[schemas.MessageOut])
def get_chat_messages(
    chat_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    cp = db.query(models.ChatParticipant).filter_by(chat_id=chat_id, user_id=current_user.id).first()
    if not cp:
        raise HTTPException(status_code=403, detail="Not authorized to view this chat.")
        
    messages = db.query(models.Message).filter_by(chat_id=chat_id).order_by(models.Message.created_at.asc()).all()
    return messages

@app.post("/api/chats/{chat_id}/messages", response_model=schemas.MessageOut)
def send_message(
    chat_id: int,
    msg_in: schemas.MessageCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    chat = db.query(models.Chat).filter_by(id=chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found.")
        
    cp = db.query(models.ChatParticipant).filter_by(chat_id=chat_id, user_id=current_user.id).first()
    if not cp:
        raise HTTPException(status_code=403, detail="Not a participant.")
        
    new_msg = models.Message(
        chat_id=chat_id,
        sender_id=current_user.id,
        content=msg_in.content
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)
    
    # Very basic AI response for bot
    if chat.is_bot_chat:
        resp_text = "I am the TechSeek Assistant. I see you said: " + msg_in.content
        if "portfolio" in msg_in.content.lower():
            try:
                mcp_resp = requests.post("http://mcp-server:5000/summarize_achievement_portfolio", json={"student_id": current_user.id}).json()
                resp_text += f"\n\nHere is your portfolio summary:\n{mcp_resp.get('summary', '')}"
            except:
                pass
        
        bot_msg = models.Message(
            chat_id=chat_id,
            sender_id=None,
            content=resp_text
        )
        db.add(bot_msg)
        db.commit()
    
    return new_msg
