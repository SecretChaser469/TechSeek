from sqlalchemy.orm import Session
from . import models

def check_connection(db: Session, user_a_id: int, user_b_id: int) -> bool:
    if user_a_id == user_b_id:
        return True
    conn = db.query(models.Connection).filter(
        ((models.Connection.user_a_id == user_a_id) & (models.Connection.user_b_id == user_b_id)) |
        ((models.Connection.user_a_id == user_b_id) & (models.Connection.user_b_id == user_a_id))
    ).first()
    return conn is not None

def redact_user_profile(target_user: models.User, accessor: models.User, db: Session) -> dict:
    # If the target user is NOT a student (e.g. they are faculty or admin), their profile is fully visible
    if target_user.role != "student":
        # Formulate faculty/admin public response
        spec_data = None
        if target_user.specialization:
            spec_data = {
                "domain": target_user.specialization.domain,
                "publications_json": target_user.specialization.publications_json
            }
        
        return {
            "id": target_user.id,
            "email": target_user.email,
            "role": target_user.role,
            "name": target_user.name,
            "bio_short": target_user.bio_short,
            "bio_full": target_user.bio_full,
            "avatar_url": target_user.avatar_url,
            "created_at": target_user.created_at,
            "streak_count": target_user.streak_count,
            "streak_visibility": target_user.streak_visibility,
            "specialization": spec_data,
            "skills": [],
            "achievements": [],
            "is_connected": True
        }

    # If accessor is faculty, admin, self, or connected, view full student profile
    is_connected = check_connection(db, target_user.id, accessor.id)
    can_view_full = (
        accessor.role in ["faculty", "admin"] or 
        target_user.id == accessor.id or
        is_connected
    )
    
    # Map basic details
    res = {
        "id": target_user.id,
        "name": target_user.name,
        "role": target_user.role,
        "semester": target_user.semester,
        "branch": target_user.branch,
        "bio_short": target_user.bio_short,
        "avatar_url": target_user.avatar_url,
        "streak_count": target_user.streak_count,
        "streak_visibility": target_user.streak_visibility if can_view_full or target_user.streak_visibility == "public" or (target_user.streak_visibility == "friends" and is_connected) else "private",
        "created_at": target_user.created_at,
        "is_connected": is_connected,
        "skills": []
    }

    # Map skills
    for us in target_user.skills:
        res["skills"].append({
            "skill": {
                "id": us.skill.id,
                "name": us.skill.name,
                "category": us.skill.category
            },
            "proficiency": us.proficiency,
            "endorsed_count": us.endorsed_count
        })

    if can_view_full:
        res["email"] = target_user.email
        res["bio_full"] = target_user.bio_full
        
        # Achievements (fully visible)
        ach_list = []
        for ach in target_user.achievements:
            ach_list.append({
                "id": ach.id,
                "user_id": ach.user_id,
                "type": ach.type,
                "title": ach.title,
                "description": ach.description,
                "skills": ach.skills,
                "date": ach.date.isoformat() if ach.date else None,
                "proof_file_url": ach.proof_file_url,
                "verification_status": ach.verification_status,
                "verification_confidence": ach.verification_confidence,
                "created_at": ach.created_at
            })
        res["achievements"] = ach_list
    else:
        # Redacted card fields
        res["email"] = "[Redacted]"
        res["bio_full"] = "[Redacted - Connect to view bio]"
        
        # Achievements are omitted or simplified
        res["achievements"] = []
        
    return res
