import datetime
import json
from sqlalchemy.orm import Session
from .database import SessionLocal, engine
from .import models, auth

def seed_db():
    db = SessionLocal()
    try:
        # Check if already seeded (by counting users)
        user_count = db.query(models.User).count()
        if user_count > 0:
            print("Database already contains data. Seeding skipped.")
            return

        print("Executing clear and seed database...")
        
        # 1. Create Baseline Skills
        skills_data = [
            ("Python", "Languages"),
            ("JavaScript", "Languages"),
            ("TypeScript", "Languages"),
            ("Rust", "Languages"),
            ("C++", "Languages"),
            ("Go", "Languages"),
            ("Next.js", "Frameworks"),
            ("React", "Frameworks"),
            ("FastAPI", "Frameworks"),
            ("Tailwind CSS", "Frameworks"),
            ("PyTorch", "AI & ML"),
            ("TensorFlow", "AI & ML"),
            ("Computer Vision", "AI & ML"),
            ("Natural Language Processing", "AI & ML"),
            ("PostgreSQL", "Databases"),
            ("Redis", "Databases"),
            ("Supabase", "Databases"),
            ("Docker", "DevOps"),
            ("Kubernetes", "DevOps")
        ]
        
        skills_map = {}
        for name, cat in skills_data:
            skill = models.Skill(name=name, category=cat)
            db.add(skill)
            db.commit()
            db.refresh(skill)
            skills_map[name] = skill

        # 2. Create Base Badges
        badges_data = [
            ("First Step", "Earned on your first verified achievement", "✨", {"type": "first", "count": 1}),
            ("Hackathon Champ", "Obtained upon verifying 3 hackathons", "🚀", {"type": "hackathon", "count": 3}),
            ("Publishing Scholar", "Published at least 1 verified academic research paper", "📝", {"type": "paper", "count": 1}),
            ("Industry Apprentice", "Completed a verified professional internship", "💼", {"type": "internship", "count": 1}),
            ("Project Maverick", "Successfully completed 3 verified projects", "🛠️", {"type": "project", "count": 3}),
            ("Streak Prodigy", "Maintained an active streak of 7 consecutive days", "🔥", {"type": "streak", "count": 7}),
            ("Double Threat", "Completed verified achievements across 2 or more categories", "🌟", {"type": "diversity", "count": 2}),
            ("Master Endorsed", "Obtained 3 or more endorsements on any single skill", "🎖️", {"type": "endorsement", "count": 3})
        ]

        for name, desc, icon, criteria in badges_data:
            badge = models.Badge(name=name, description=desc, icon_url=icon, criteria_json=criteria)
            db.add(badge)
        db.commit()

        # 3. Create Users
        # Password hash
        pwd_hash = auth.get_password_hash("password123")

        # 5 Faculty
        faculty_users = []
        fac_specializations = [
            ("Dr. Angela Vance", "Machine Learning & NLP", ["Attention mechanisms in small text, 2025", "LLM-assisted student evaluations, 2026"]),
            ("Prof. Silas Ward", "Distributed Systems & Cloud", ["Scaling KV microservices, 2024", "State preservation across serverless clusters, 2025"]),
            ("Dr. Chloe Mercer", "Cybersecurity & Cryptography", ["Post-quantum signature lengths, 2025"]),
            ("Prof. Marcus Drake", "VLSI Design & Hardware architecture", ["Sub-5nm thermals on ARM cores, 2025"]),
            ("Dr. Keith Lawson", "Bioinformatics & Sequence Analysis", ["CRISPR target simulation speeds, 2025"])
        ]

        for name, domain, pubs in fac_specializations:
            email = name.lower().replace(" ", ".").replace("dr.", "dr").replace("prof.", "prof") + "@college.edu"
            fac = models.User(
                email=email,
                hashed_password=pwd_hash,
                role="faculty",
                name=name,
                bio_short=f"Faculty Researcher in {domain}",
                bio_full=f"Teaching upper undergraduate workshops. Leading advancements in {domain}.",
                streak_count=5
            )
            db.add(fac)
            db.commit()
            db.refresh(fac)
            faculty_users.append(fac)

            # Specialization
            spec = models.FacultySpecialization(
                faculty_id=fac.id,
                domain=domain,
                publications_json=pubs
            )
            db.add(spec)
            db.commit()

        # Add Admin
        admin_user = models.User(
            email="admin@college.edu",
            hashed_password=pwd_hash,
            role="admin",
            name="Principal Registrar Office",
            bio_short="TechSeek Institutional Administrator",
            streak_count=10
        )
        db.add(admin_user)
        db.commit()

        # 15 Students
        students_data = [
            ("Alice Smith", 8, "Computer Science", "Deep learning wizard", "Interested in AI ethics and vision pipelines."),
            ("Bob Jones", 6, "Computer Science", "Backend developer", "Building high throughput engines with Go & Rust."),
            ("Charlie Brown", 4, "Computer Science", "UI Designer", "Building interfaces with Tailwind CSS, React and Next.js."),
            ("Daniel Craig", 7, "ECE", "Hardware developer", "FPGA design and IoT microcontrollers."),
            ("Eva Long", 5, "ECE", "Embedded system dev", "Interested in robotics architectures."),
            ("Frank Castle", 8, "BioTech", "Genomic Researcher", "Applying AI to analyze genome variations."),
            ("Grace Hopper", 3, "Computer Science", "Compiler enthusiast", "Rebuilding parsers in Rust."),
            ("Henry Cavil", 5, "Computer Science", "Web3 engineer", "Decentralized state logs & transactions."),
            ("Ian Somer", 6, "ECE", "Signal analyst", "DSP algorithms & Fourier transformations."),
            ("Jack Reacher", 4, "BioTech", "Proteins engineer", "Simulating folded state structures."),
            ("Karen Page", 8, "Computer Science", "Cybersecurity researcher", "Vulnerability scanners & threat defense."),
            ("Leo Messi", 2, "Computer Science", "Junior Dev", "Learning JavaScript and web interfaces."),
            ("Mona Lisa", 1, "Computer Science", "First-year student", "Just started coding journey with Python."),
            ("Nathan Drake", 5, "ECE", "Radio engineer", "Exploring microwave frequencies and antenna arrays."),
            ("Olivia Wilde", 3, "BioTech", "Data scientist", "Analyzing health dataset distributions.")
        ]

        student_users = []
        today = datetime.date.today()

        for idx, (name, sem, branch, bio_s, bio_f) in enumerate(students_data):
            email = name.lower().replace(" ", ".") + "@college.edu"
            
            # Adjust streaks
            streak = 1 + (idx % 8)
            
            stud = models.User(
                email=email,
                hashed_password=pwd_hash,
                role="student",
                name=name,
                semester=sem,
                branch=branch,
                bio_short=bio_s,
                bio_full=bio_f,
                streak_count=streak,
                streak_visibility="public" if idx % 3 != 0 else "friends"
            )
            db.add(stud)
            db.commit()
            db.refresh(stud)
            student_users.append(stud)

            # Add streak logs
            for offset in range(streak):
                log_date = today - datetime.timedelta(days=offset)
                db.add(models.StreakLog(
                    user_id=stud.id,
                    date=log_date,
                    activity_type="login" if offset != 0 else "achievement_created"
                ))
            
            # Add skills
            # CS gets coding, ECE gets hardware, BioTech gets data/AI
            if branch == "Computer Science":
                db.add(models.UserSkill(user_id=stud.id, skill_id=skills_map["Python"].id, proficiency=4, endorsed_count=idx % 3))
                db.add(models.UserSkill(user_id=stud.id, skill_id=skills_map["TypeScript"].id, proficiency=3, endorsed_count=idx % 2))
                db.add(models.UserSkill(user_id=stud.id, skill_id=skills_map["Next.js"].id, proficiency=3, endorsed_count=0))
            elif branch == "ECE":
                db.add(models.UserSkill(user_id=stud.id, skill_id=skills_map["C++"].id, proficiency=4, endorsed_count=idx % 2))
                db.add(models.UserSkill(user_id=stud.id, skill_id=skills_map["Docker"].id, proficiency=3, endorsed_count=1))
            else: # BioTech
                db.add(models.UserSkill(user_id=stud.id, skill_id=skills_map["Python"].id, proficiency=3, endorsed_count=1))
                db.add(models.UserSkill(user_id=stud.id, skill_id=skills_map["Computer Vision"].id, proficiency=4, endorsed_count=idx % 3))

            db.commit()

        # 4. Create 30 achievements (mixed verification status)
        # 10 verified, 10 unverified/pending, 5 ai_flagged, 5 rejected
        ach_specs = [
            ("Alice Smith", "hackathon", "Inter-College Code Sprint", "First place in algorithmic challenges", ["Python", "C++"], "faculty_verified", 95.0),
            ("Alice Smith", "hackathon", "EcoHack 2026", "Developed carbon tracker", ["Python", "TypeScript"], "faculty_verified", 90.0),
            ("Alice Smith", "hackathon", "Global Dev Summit", "Best developer category", ["Next.js", "Docker"], "faculty_verified", 88.0), # qualifies for Champ
            ("Bob Jones", "paper", "Highly Scaling DB Architecture", "Research paper published in IEEE Systems", ["PostgreSQL", "Redis"], "faculty_verified", 92.0),
            ("Bob Jones", "project", "Self-Hosting Engine", "Recreating secure reverse proxies", ["Rust", "Docker"], "unverified", 70.0),
            ("Charlie Brown", "project", "Glassmorphic Design Library", "Open-source Tailwind CSS styling system", ["Tailwind CSS", "React"], "ai_flagged", 55.0),
            ("Daniel Craig", "certification", "Embedded FPGA Certificate", "Certified systems developer by ARM Labs", ["C++"], "faculty_verified", 96.0),
            ("Daniel Craig", "hackathon", "Hardware Hackathon 2025", "Built smart thermostat using radio logs", ["C++"], "unverified", 60.0),
            ("Eva Long", "internship", "Autopilot Labs Intern", "Assisted software integration on microchips", ["C++", "Docker"], "faculty_verified", 98.0),
            ("Frank Castle", "paper", "Genomic Variant Classifiers", "Identifying sequence mappings using CNNs", ["Computer Vision", "Python"], "faculty_verified", 93.0),
            ("Frank Castle", "project", "Fuzzy Sequence Aligner", "Fast C++ matchings for DNA strands", ["C++"], "rejected", 35.0),
            ("Grace Hopper", "project", "Simple Compiler frontend", "Parsing visual block flows to Rust code", ["Rust"], "faculty_verified", 90.0),
            ("Henry Cavil", "hackathon", "Web3 Decentralised Hack", "Winner of Best Smart Contract", ["Python", "Docker"], "ai_flagged", 62.0),
            ("Ian Somer", "project", "Continuous DSP Analysis", "Spectral analyzer toolkit", ["Python"], "unverified", 80.0),
            ("Jack Reacher", "project", "3D Protein Renderer", "Web app modeling folded node structures", ["React", "TypeScript"], "rejected", 40.0),
            
            # Simple list adding up to 30 general records
            ("Alice Smith", "project", "Intelligent Agent Antigravity", "Self-correcting code assistant integration", ["Python"], "unverified", 85.0),
            ("Bob Jones", "project", "Log Collector CLI", "Log aggregator in Go", ["Go"], "faculty_verified", 87.0),
            ("Charlie Brown", "certification", "React Patterns Certificate", "Issued by Frontend Academy", ["React"], "faculty_verified", 89.0),
            ("Daniel Craig", "project", "Smart Irrigation Controller", "Valves controller using humidity", ["C++"], "faculty_verified", 91.0),
            ("Eva Long", "project", "Bipedal Balance Simulator", "Reinforcement learning balance model", ["Python", "PyTorch"], "faculty_verified", 94.0),
            
            ("Frank Castle", "hackathon", "BioTech Research Hackathon", "First Prize mapping genomes", ["Python"], "unverified", 75.0),
            ("Grace Hopper", "project", "Babel Parser Engine", "Abstract syntax parser build", ["Python"], "unverified", 78.0),
            ("Henry Cavil", "project", "Token Swap Sandbox", "Local blockchain ledger mock", ["Go"], "unverified", 68.0),
            ("Ian Somer", "certification", "Signal Processing Badge", "Certified by Radio Research Board", ["C++"], "unverified", 72.0),
            ("Jack Reacher", "paper", "Cell Membrane Simulations", "Computational Biology paper", ["Python"], "unverified", 79.0),

            ("Karen Page", "project", "Port Scanner API", "Fast port scanner using async Python", ["Python"], "faculty_verified", 95.0),
            ("Karen Page", "certification", "OSCP Security Cert", "Offensive Security certified", ["Python"], "ai_flagged", 58.0),
            ("Leo Messi", "project", "Simple ToDo", "Interactive state list using JS", ["JavaScript"], "unverified", 48.0),
            ("Mona Lisa", "project", "HelloWorld Scripts", "Gathering programming scripts", ["Python"], "unverified", 46.0),
            ("Olivia Wilde", "project", "Disease Matrix Plots", "Plotting datasets distributions", ["Python"], "faculty_verified", 90.0)
        ]

        # Map student name to ID
        student_id_map = {s.name: s.id for s in student_users}
        faculty_id_map = {f.name: f.id for f in faculty_users}

        for stud_name, a_type, title, desc, skills, status, score in ach_specs:
            uid = student_id_map.get(stud_name)
            if not uid:
                continue

            ach = models.Achievement(
                user_id=uid,
                type=a_type,
                title=title,
                description=desc,
                skills=skills,
                date=today - datetime.timedelta(days=30),
                proof_file_url=f"/uploads/mock_cert.png",
                verification_status=status,
                verification_confidence=score
            )
            db.add(ach)
            db.commit()
            db.refresh(ach)

            # Faculty endorsements
            if status == "faculty_verified" and stud_name in ["Alice Smith", "Bob Jones", "Karen Page"]:
                fac_name = list(faculty_id_map.keys())[0] # Dr. Angela Vance
                fac_id = faculty_id_map[fac_name]
                
                # Choose one skill
                skill = db.query(models.Skill).filter(models.Skill.name == skills[0]).first()
                
                endor = models.Endorsement(
                    faculty_id=fac_id,
                    student_id=uid,
                    achievement_id=ach.id,
                    skill_id=skill.id if skill else None,
                    comment="Outstanding execution and robust presentation."
                )
                db.add(endor)
                
                # Update student skill endorsed count
                if skill:
                    us = db.query(models.UserSkill).filter(models.UserSkill.user_id == uid, models.UserSkill.skill_id == skill.id).first()
                    if us:
                        us.endorsed_count += 1
                        
                db.commit()

        # 5. Create Team Requests (5)
        team_specs = [
            ("Alice Smith", "Compiler for Embedded Systems", "Building a hardware execution backend. Need hackers.", ["C++", "Rust", "Docker"], 3),
            ("Bob Jones", "Distributed KV Database", "Need co-developers. Implementing RAFT protocol.", ["Go", "Python", "Docker"], 2),
            ("Daniel Craig", "Smart Home Hub Gateway", "Creating a physical circuit microchip interface.", ["C++", "Docker"], 4),
            ("Frank Castle", "Cancer Cell Classifier Project", "Developing computer vision grids to segment cells.", ["Python", "Computer Vision"], 3),
            ("Grace Hopper", "Rust Compiler Optimizations", "Optimizing LLVM compiler outputs.", ["Rust", "C++"], 2)
        ]

        for owner_name, title, desc, skills, size in team_specs:
            oid = student_id_map.get(owner_name)
            if not oid:
                continue

            req = models.TeamRequest(
                creator_id=oid,
                title=title,
                description=desc,
                required_skills=skills,
                team_size=size,
                deadline=today + datetime.timedelta(days=15),
                status="active"
            )
            db.add(req)
        db.commit()

        # 6. Create Mentor Requests (3)
        mentor_specs = [
            ("Alice Smith", "Neural Architecture Search", "Researching optimization of transformer attention layers.", ["Machine Learning & NLP"]),
            ("Bob Jones", "Consensus Protocol Performance", "Analyzing microservices throughput degradation.", ["Distributed Systems & Cloud"]),
            ("Daniel Craig", "Sub-nanometer thermo modeling", "Simulating temperature graphs on microchips.", ["VLSI Design & Hardware architecture"])
        ]

        for stud_name, topic, desc, spec_list in mentor_specs:
            sid = student_id_map.get(stud_name)
            if not sid:
                continue

            m_req = models.MentorRequest(
                student_id=sid,
                topic=topic,
                description=desc,
                required_specialization=spec_list,
                status="pending"
            )
            db.add(m_req)
        db.commit()

        # Auto-award badges for seeded students
        for sid in student_id_map.values():
            check_and_award_badges(sid, db)

        # Setup standard leaderboard opt-ins for students
        for sid in student_id_map.values():
            # Opt-in to overall and specific category based on department
            db.add(models.LeaderboardOptIn(user_id=sid, category="overall", visible_to_friends=True))
            
            s_obj = db.query(models.User).filter(models.User.id == sid).first()
            if s_obj.branch == "Computer Science":
                db.add(models.LeaderboardOptIn(user_id=sid, category="hackathons", visible_to_friends=True))
            if s_obj.name in ["Alice Smith", "Bob Jones"]:
                db.add(models.LeaderboardOptIn(user_id=sid, category="papers", visible_to_friends=True))

        db.commit()
        print("Database seeded successfully with dummy records!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
