import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import pytesseract
from PIL import Image

# Database imports to scoring logic
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-server")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password123@postgres:5432/techseek")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")

# Connect to database for match scoring
engine = None
SessionLocal = None
try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"Database connection failed: {e}")

app = FastAPI(title="TechSeek MCP Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "healthy", "server": "mcp-server"}

# --- REQUEST SCHEMAS ---
class CertificateVerifyRequest(BaseModel):
    image_url: str  # filepath on shared volume, e.g. /app/uploads/filename
    claimed_issuer: str
    claimed_event: str
    claimed_date: str

class TeamMatchRequest(BaseModel):
    request_id: int

class MentorMatchRequest(BaseModel):
    mentor_request_id: int

class EndorsementPromptRequest(BaseModel):
    student_id: int

class PortfolioSummaryRequest(BaseModel):
    student_id: int

class StreakRiskRequest(BaseModel):
    student_id: int

# --- CORE IMPLEMENTATION LOGIC ---

def run_certificate_verification(image_path: str, issuer: str, event: str, claimed_date_str: str) -> dict:
    # 1. Resolve path relative to shared upload dir if needed
    full_path = image_path
    if not os.path.isabs(full_path):
        full_path = os.path.join(UPLOAD_DIR, image_path)
    elif not full_path.startswith(UPLOAD_DIR) and not os.path.exists(full_path):
        # Match baseline app file structure if path starts with /uploads/
        if full_path.startswith("/uploads/"):
            full_path = os.path.join(UPLOAD_DIR, full_path.replace("/uploads/", ""))

    logger.info(f"Target verification image path: {full_path}")
    
    extracted_text = ""
    flags = []
    confidence = 50.0

    if not os.path.exists(full_path):
        flags.append("Verification proof file not found on disk")
        return {"confidence": 0.0, "flags": flags, "extracted_text": ""}

    try:
        # Load image and extract text
        img = Image.open(full_path)
        extracted_text = pytesseract.image_to_string(img)
        logger.info(f"OCR successfully completed: extracted {len(extracted_text)} chars")
    except Exception as e:
        flags.append(f"OCR process failed: {str(e)}")
        return {"confidence": 10.0, "flags": flags, "extracted_text": ""}

    text_lower = extracted_text.lower()
    
    # Check Issuer (Fuzzy matching)
    issuer_match = False
    for word in issuer.lower().split():
        if len(word) > 2 and word in text_lower:
            issuer_match = True
            confidence += 15.0

    if not issuer_match:
        flags.append("Claimed Certificate Issuer name not detected in certificate image text.")
    else:
        confidence += 10.0

    # Check Event/Title (Fuzzy matching)
    event_match = False
    for word in event.lower().split():
        if len(word) > 2 and word in text_lower:
            event_match = True
            confidence += 15.0

    if not event_match:
        flags.append("Event or certificate activity title not detected in proof document.")
    else:
        confidence += 10.0

    # Parse and check date
    try:
        claimed_date = datetime.strptime(claimed_date_str, "%Y-%m-%d").date()
        # Plausibility check: future date flag
        if claimed_date > date.today():
            flags.append("Claimed completion date is in the future.")
            confidence -= 30.0

        # Try to find dates in text
        # Simple date pattern scanning (e.g. 2026, 2025, or month name)
        year_str = str(claimed_date.year)
        if year_str in text_lower:
            confidence += 10.0
        else:
            flags.append(f"Year of completion ({year_str}) was not identified in extracting certificate text.")
            confidence -= 10.0
    except Exception as e:
        flags.append(f"Failed to validate date formats: {e}")

    # Clip confidence range
    confidence = max(0.0, min(100.0, confidence))
    
    return {
        "confidence": round(confidence, 1),
        "flags": flags,
        "extracted_text": extracted_text[:1500]  # truncate to safe limit
    }

def calculate_team_matches(request_id: int) -> dict:
    if not SessionLocal:
        return {"candidates": []}
    db = SessionLocal()
    try:
        # Fetch team request details
        req_res = db.execute(text("SELECT creator_id, required_skills, status FROM team_requests WHERE id = :rid"), {"rid": request_id}).fetchone()
        if not req_res:
            return {"error": "Team request not found", "candidates": []}
        
        creator_id, required_skills_json, status = req_res
        required_skills = required_skills_json if isinstance(required_skills_json, list) else json.loads(required_skills_json or "[]")
        
        # Query potential students (excluding the creator)
        students = db.execute(text("SELECT id, name, semester, branch, avatar_url FROM users WHERE role = 'student' AND id != :cid"), {"cid": creator_id}).fetchall()
        
        candidates = []
        for s in students:
            s_id, s_name, s_semester, s_branch, s_avatar = s
            # Fetch skills of student
            s_skills_res = db.execute(
                text("SELECT s.name, us.proficiency FROM user_skills us JOIN skills s ON us.skill_id = s.id WHERE us.user_id = :sid"),
                {"sid": s_id}
            ).fetchall()
            
            s_skill_names = {sk[0].lower(): sk[1] for sk in s_skills_res}
            
            # Match score: overlap in required skills
            overlap_count = 0
            proficiency_score = 0
            for r_skill in required_skills:
                r_skill_l = r_skill.lower()
                if r_skill_l in s_skill_names:
                    overlap_count += 1
                    proficiency_score += s_skill_names[r_skill_l]

            # Team match score out of 100
            denom = len(required_skills) if required_skills else 1
            overlap_ratio = overlap_count / denom
            base_score = overlap_ratio * 70.0  # 70% based on skill coverage
            prof_contrib = (proficiency_score / (denom * 5)) * 30.0 if overlap_count > 0 else 0.0 # 30% on proficiency
            
            total_score = base_score + prof_contrib
            
            candidates.append({
                "student_id": s_id,
                "name": s_name,
                "avatar_url": s_avatar,
                "semester": s_semester,
                "branch": s_branch,
                "match_score": round(total_score, 1),
                "matching_skills_count": overlap_count
            })
            
        candidates.sort(key=lambda x: x["match_score"], reverse=True)
        return {"candidates": candidates[:10]}
    finally:
        db.close()

def calculate_mentor_matches(mentor_request_id: int) -> dict:
    if not SessionLocal:
        return {"matches": []}
    db = SessionLocal()
    try:
        req_res = db.execute(text("SELECT student_id, topic, description, required_specialization FROM mentor_requests WHERE id = :rid"), {"rid": mentor_request_id}).fetchone()
        if not req_res:
            return {"error": "Mentor request not found", "matches": []}
        
        student_id, topic, description, req_spec_json = req_res
        req_specs = req_spec_json if isinstance(req_spec_json, list) else json.loads(req_spec_json or "[]")
        
        # Get all faculty and their specializations
        facs = db.execute(
            text("SELECT u.id, u.name, u.avatar_url, fs.domain, fs.publications_json FROM users u JOIN faculty_specializations fs ON u.id = fs.faculty_id WHERE u.role = 'faculty'")
        ).fetchall()
        
        matches = []
        for f in facs:
            f_id, f_name, f_avatar, f_domain, f_pub_json = f
            publications = f_pub_json if isinstance(f_pub_json, list) else json.loads(f_pub_json or "[]")
            
            # Simple keyword search between requests topic/description/specializations and faculty domain/publications
            score = 20.0 # Baseline match score
            
            # Match domain
            for r_spec in req_specs:
                if r_spec.lower() in f_domain.lower():
                    score += 30.0
            
            # Match topic and publications
            texts_to_search = topic.lower() + " " + description.lower()
            pub_matches = 0
            for pub in publications:
                if any(word in pub.lower() for word in texts_to_search.split() if len(word) > 4):
                    pub_matches += 1
            
            score += min(30.0, pub_matches * 10.0)
            score = min(100.0, score)
            
            matches.append({
                "faculty_id": f_id,
                "name": f_name,
                "avatar_url": f_avatar,
                "domain": f_domain,
                "match_score": round(score, 1)
            })
            
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        return {"matches": matches[:5]}
    finally:
        db.close()

def find_endorsement_prompts(student_id: int) -> dict:
    # Intelligently suggest skills faculty might endorse based on achievements count
    if not SessionLocal:
        return {"prompts": []}
    db = SessionLocal()
    try:
        # Check student achievements that are unendorsed
        achievements = db.execute(
            text("SELECT id, title, type, skills FROM achievements WHERE user_id = :sid AND verification_status = 'faculty_verified'"),
            {"sid": student_id}
        ).fetchall()
        
        prompts = []
        for ach in achievements:
            ach_id, ach_title, ach_type, ach_skills_json = ach
            ach_skills = ach_skills_json if isinstance(ach_skills_json, list) else json.loads(ach_skills_json or "[]")
            
            for skill in ach_skills:
                # Suggest endorsement of this specific skill with custom prompt
                prompts.append({
                    "skill_name": skill,
                    "achievement_id": ach_id,
                    "achievement_title": ach_title,
                    "suggested_comment": f"Enthusiastically endorsed for demonstrating excellence in {skill} through the {ach_type}: '{ach_title}'."
                })
        return {"prompts": prompts[:5]}
    finally:
        db.close()

def generate_portfolio_summary(student_id: int) -> dict:
    if not SessionLocal:
        return {"summary": "Service offline."}
    db = SessionLocal()
    try:
        user_res = db.execute(text("SELECT name, semester, branch, bio_short FROM users WHERE id = :sid"), {"sid": student_id}).fetchone()
        if not user_res:
            return {"summary": "Student profile not found"}
        
        name, sem, branch, bio = user_res
        
        # Fetch accomplishments counts
        achs = db.execute(
            text("SELECT type, count(id) FROM achievements WHERE user_id = :sid AND verification_status = 'faculty_verified' GROUP BY type"),
            {"sid": student_id}
        ).fetchall()
        
        ach_counts = {a[0]: a[1] for a in achs}
        
        # Skills
        skills_res = db.execute(
            text("SELECT s.name FROM user_skills us JOIN skills s ON us.skill_id = s.id WHERE us.user_id = :sid"),
            {"sid": student_id}
        ).fetchall()
        skills = [s[0] for s in skills_res]
        
        # Construct dynamic portfolio summary paragraph
        summary_intro = f"{name} is a student in Semester {sem or 'N/A'}, majoring in {branch or 'Engineering'}. "
        if bio:
            summary_intro += f"Their focus is: '{bio}'. "
            
        ach_sentences = []
        for ach_type, count in ach_counts.items():
            ach_sentences.append(f"{count} verified {ach_type}(s)")
            
        if ach_sentences:
            summary_intro += f"They have completed {', '.join(ach_sentences)}. "
        else:
            summary_intro += "They are cultivating their skills registry and preparing for their first verified accomplishments. "

        if skills:
            summary_intro += f"Their key skill endorsements cover: {', '.join(skills[:5])}."
            
        return {
            "summary": summary_intro,
            "skills": skills,
            "metrics": ach_counts
        }
    finally:
        db.close()

def evaluate_streak_risk(student_id: int) -> dict:
    if not SessionLocal:
        return {"at_risk": False}
    db = SessionLocal()
    try:
        user_res = db.execute(text("SELECT streak_count FROM users WHERE id = :sid"), {"sid": student_id}).fetchone()
        if not user_res:
            return {"error": "Student not found"}
        
        streak_count = user_res[0]
        if streak_count == 0:
            return {"at_risk": False, "days_since_last_activity": 0, "message": "No active streak."}

        # Check last log date
        last_log = db.execute(
            text("SELECT date FROM streak_logs WHERE user_id = :sid ORDER BY date DESC LIMIT 1"),
            {"sid": student_id}
        ).fetchone()

        if not last_log:
            return {"at_risk": True, "days_since_last_activity": 2, "message": "Streak is at risk. Send a nudge to log an activity!"}

        last_date = last_log[0]
        if isinstance(last_date, str):
            last_date = datetime.strptime(last_date, "%Y-%m-%d").date()
            
        today = date.today()
        diff = (today - last_date).days

        if diff >= 1:
            return {
                "at_risk": True,
                "days_since_last_activity": diff,
                "message": f"Streak of {streak_count} days is at risk of breaking! The last activity was logged {diff} day(s) ago."
            }
        
        return {
            "at_risk": False,
            "days_since_last_activity": diff,
            "message": "Streak is currently safe."
        }
    finally:
        db.close()

# --- REST APIS BOUND FOR BACKEND AND SIMPLE CALLING ---

@app.post("/verify_certificate")
def verify_cert(req: CertificateVerifyRequest):
    return run_certificate_verification(req.image_url, req.claimed_issuer, req.claimed_event, req.claimed_date)

@app.post("/suggest_team_matches")
def suggest_teams(req: TeamMatchRequest):
    return calculate_team_matches(req.request_id)

@app.post("/suggest_mentor_matches")
def suggest_mentors(req: MentorMatchRequest):
    return calculate_mentor_matches(req.mentor_request_id)

@app.post("/suggest_endorsement_prompts")
def suggest_endorsements(req: EndorsementPromptRequest):
    return find_endorsement_prompts(req.student_id)

@app.post("/summarize_achievement_portfolio")
def summarize_portfolio(req: PortfolioSummaryRequest):
    return generate_portfolio_summary(req.student_id)

@app.post("/detect_streak_risk")
def streak_risk(req: StreakRiskRequest):
    return evaluate_streak_risk(req.student_id)


# --- MCP PROTOCOL STANDARDS ---
# Allows independent testability using the Model Context Protocol JSON-RPC style.

@app.get("/tools")
def list_mcp_tools():
    # Return MCP compatible tools list
    return {
        "tools": [
            {
                "name": "verify_certificate",
                "description": "OCR verify a certificate proof file against issuer, event, and date details",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "image_url": {"type": "string", "description": "Absolute or relative path to certificate document image"},
                        "claimed_issuer": {"type": "string"},
                        "claimed_event": {"type": "string"},
                        "claimed_date": {"type": "string", "description": "YYYY-MM-DD completion date"}
                    },
                    "required": ["image_url", "claimed_issuer", "claimed_event", "claimed_date"]
                }
            },
            {
                "name": "suggest_team_matches",
                "description": "Find and rank students matching a team placement request requirements",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "request_id": {"type": "integer"}
                    },
                    "required": ["request_id"]
                }
            },
            {
                "name": "suggest_mentor_matches",
                "description": "Find and rank faculty specialities aligning with a research mentor request topic",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mentor_request_id": {"type": "integer"}
                    },
                    "required": ["mentor_request_id"]
                }
            },
            {
                "name": "suggest_endorsement_prompts",
                "description": "Suggest skill endorsement messaging for verified student accomplishments",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "integer"}
                    },
                    "required": ["student_id"]
                }
            },
            {
                "name": "summarize_achievement_portfolio",
                "description": "Create natural language bio/summary of a student's verification records and expertise",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "integer"}
                    },
                    "required": ["student_id"]
                }
            },
            {
                "name": "detect_streak_risk",
                "description": "Identify if a student activity streak is at risk of resetting",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "integer"}
                    },
                    "required": ["student_id"]
                }
            }
        ]
    }

@app.post("/tools/{tool_name}")
async def call_mcp_tool(tool_name: str, request: Request):
    try:
        body = await request.json()
        args = body.get("arguments", {})
    except Exception:
        args = {}

    logger.info(f"MCP tool call received: {tool_name} with args {args}")

    try:
        if tool_name == "verify_certificate":
            res = run_certificate_verification(
                args.get("image_url"), 
                args.get("claimed_issuer"), 
                args.get("claimed_event"), 
                args.get("claimed_date")
            )
        elif tool_name == "suggest_team_matches":
            res = calculate_team_matches(int(args.get("request_id")))
        elif tool_name == "suggest_mentor_matches":
            res = calculate_mentor_matches(int(args.get("mentor_request_id")))
        elif tool_name == "suggest_endorsement_prompts":
            res = find_endorsement_prompts(int(args.get("student_id")))
        elif tool_name == "summarize_achievement_portfolio":
            res = generate_portfolio_summary(int(args.get("student_id")))
        elif tool_name == "detect_streak_risk":
            res = evaluate_streak_risk(int(args.get("student_id")))
        else:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        # Wrap response in standard MCP structure
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(res)
                }
            ]
        }
    except Exception as e:
        logger.error(f"Error executing MCP tool: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
