# 🎓 CampusConnect
### Privacy-First AI-Powered Student Achievement & Collaboration Platform

<p align="center">
  <img src="./assets/logo.png" alt="CampusConnect Logo" width="180"/>
</p>

> **Connecting Talent. Enabling Collaboration. Building the Future of Campus Innovation.**

---

## 📖 Overview

CampusConnect is a next-generation campus networking platform designed to digitally connect students, faculty, research opportunities, hackathons, and institutional achievements under one secure ecosystem.

Unlike conventional professional networking platforms, CampusConnect focuses on **verified academic achievements**, **privacy-first networking**, **AI-powered matchmaking**, and **institutional collaboration**.

The platform enables students to build a verified academic portfolio throughout their college journey while helping faculty discover talented students, create research collaborations, and simplify institutional reporting for accreditation and placements.

---

# 🌟 Inspiration

Every college has thousands of talented students.

Some excel in hackathons.

Some publish research papers.

Some build incredible projects.

Some win competitions.

Yet discovering these students is surprisingly difficult.

Most opportunities today happen because someone "knows someone."

Finding teammates usually depends on:

- Friend circles
- WhatsApp groups
- Existing club networks
- Word-of-mouth

This unintentionally excludes many capable students who simply lack visibility.

Similarly,

Faculty members often struggle to identify students interested in their research.

Students don't know which professors share their research interests.

Meanwhile colleges spend weeks manually collecting student achievements whenever NAAC, NBA, placement drives, or annual reports require them.

CampusConnect was built to solve these disconnected problems through one integrated platform.

---

# ❗ Problem Statement

## 1. Fragmented Student Achievements

Student achievements are scattered across:

- LinkedIn
- GitHub
- Google Drive
- PDF resumes
- Certificates
- Emails

There is no centralized institutional record.

---

## 2. Unverified Claims

Most achievements are self-reported.

Anyone can claim:

- Hackathons
- Workshops
- Certifications
- Competitions

without any institutional verification.

This reduces trust.

---

## 3. Team Formation is Network-Based

Students usually find teammates through

- Friends
- Clubs
- WhatsApp Groups

instead of actual skill compatibility.

Talented but less-connected students often miss opportunities.

---

## 4. Faculty-Student Gap

Students struggle to discover

- Research supervisors
- Faculty expertise
- Ongoing projects

Faculty also struggle to discover interested students.

---

## 5. Institutional Data Management

Colleges manually prepare reports for

- NAAC
- NBA
- Placements
- Rankings
- Annual Reports

This process is repetitive and time-consuming.

---

# 💡 Solution

CampusConnect creates a verified institutional talent graph.

Every achievement, project, publication, internship, and certification becomes structured, searchable data.

Students discover opportunities.

Faculty discover talent.

Colleges discover insights.

---

# ✨ Key Features

---

# 👤 Student Profiles

Every student receives a dynamic profile from Semester 1.

The profile includes:

- Basic Information
- Academic Details
- Skills
- Projects
- Hackathons
- Certifications
- Research Papers
- Internships
- Clubs
- Leadership Roles
- Awards
- Portfolio Links

Unlike traditional resumes, profiles continuously evolve throughout college.

---

# 🔒 Privacy-First Design

One of the biggest differentiators.

### Faculty → Student

Faculty can view:

- Complete profile
- Projects
- Achievements
- Publications
- Contact Information

This enables mentorship and research.

---

### Student → Student

Students only see

- Name
- Photo
- Semester
- Branch
- Skill Tags
- Short Bio

Achievements remain hidden until:

- Team request accepted
- Mentor request accepted
- Mutual connection established

This prevents unhealthy competition while enabling collaboration.

---

# 🏆 Verified Achievement System

Achievements can be verified through:

- Faculty approval
- Club approval
- Event coordinators
- RFID attendance
- NFC Student ID
- QR Verification

Examples

✅ Hackathon Participation

✅ Workshop Attendance

✅ Seminar Participation

✅ Research Publication

✅ Internship Completion

Verified achievements receive an institutional verification badge.

---

# 🤝 Smart Team Matching

Students can create team requests.

Example:

Need:

- Flutter Developer
- ML Engineer
- UI Designer

Deadline:

July 20

The platform recommends suitable teammates using:

- Skill overlap
- Previous experience
- Achievement similarity
- Project history
- Domain expertise

Future versions will use AI embeddings for semantic similarity.

---

# 👨‍🏫 Faculty Mentorship Portal

Faculty create profiles including:

- Research Interests
- Publications
- Current Projects
- Office Hours
- Areas of Expertise

Students can request mentorship directly.

Faculty can also invite students to collaborate.

---

# 📚 Research Collaboration

Students can

- Find research opportunities
- Apply for ongoing projects
- Join faculty research groups
- Upload publications

Faculty can recruit researchers based on skills.

---

# 🎯 Internship Discovery

Based on:

- Skills
- Projects
- Achievements
- Certifications

CampusConnect recommends

- Internships
- Fellowships
- Student Ambassador Programs
- Competitions

---

# 📈 Institutional Dashboard

Admins receive analytics including

- Department-wise achievements
- Publications
- Certifications
- Internship Statistics
- Placement Readiness
- Student Skills
- Hackathon Participation
- Club Activities

Useful for:

- NAAC
- NBA
- Rankings
- Accreditation
- Reports

---

# 🤖 AI Features

CampusConnect uses AI for

### Smart Matching

Matching students based on

- Skills
- Domain
- Interests

---

### Resume Generation

Automatically generate resumes using verified achievements.

---

### Skill Gap Analysis

Suggest

- Courses
- Certifications
- Projects

based on career goals.

---

### Career Recommendations

Personalized recommendations for

- Hackathons
- Competitions
- Internships
- Research

---

### AI Career Mentor *(Future)*

Students can ask:

"What should I learn next?"

"Which hackathon should I join?"

"Which faculty should I approach?"

---

# 🏛️ Institutional Benefits

## Students

- Digital verified portfolio
- Better networking
- Discover teammates
- Research opportunities
- Career growth

---

## Faculty

- Find talented students
- Recruit researchers
- Mentor efficiently
- Track student progress

---

## Colleges

- Centralized achievement records
- Accreditation reports
- Placement analytics
- Student engagement insights

---

# 🏗️ System Architecture

```
Student
     │
     ▼
Frontend (Next.js)

     │
REST API

     ▼
FastAPI Backend

     │
     ├──────── Authentication
     ├──────── Matching Engine
     ├──────── Privacy Layer
     ├──────── Recommendation Engine
     └──────── Achievement Verification

     ▼

PostgreSQL Database

     │

     ▼

Storage
(Images, Certificates, PDFs)
```

---

# 🛠️ Tech Stack

## Frontend

- Next.js
- React
- Tailwind CSS
- TypeScript
- Shadcn UI

---

## Backend

- FastAPI
- Python
- SQLAlchemy
- Pydantic

---

## Database

- PostgreSQL

---

## Authentication

- JWT
- OAuth
- College Email Verification

---

## AI

- Sentence Transformers
- OpenAI API / Gemini API
- Skill Recommendation Engine

---

## Deployment

- Docker
- Docker Compose
- Vercel
- Railway / Render

---

# 📂 Database Design

Main tables include

```
Users

Achievements

Skills

UserSkills

Projects

Research

Faculty

TeamRequests

MentorRequests

Connections

Notifications

Institutions

Departments

Events

Certificates

Reports
```

---

# 🔐 Security

- JWT Authentication
- Role Based Access Control
- College Email Verification
- Privacy Layer
- Secure File Uploads
- Encrypted Password Storage
- Audit Logs

---

# 🚀 Future Scope

- Multi-college ecosystem
- AI interview preparation
- AI project evaluator
- Automatic GitHub syncing
- LinkedIn integration
- Kaggle integration
- Smart attendance
- Blockchain-based certificate verification
- Digital student identity
- Industry mentor onboarding
- Campus recruitment portal
- Alumni mentorship network
- AI chatbot for academic guidance
- Mobile application
- Cross-campus hackathon collaboration

---

# 📊 Scalability

The platform is designed to support

- Departments
- Colleges
- Universities
- Multi-campus institutions

Future architecture supports multi-tenancy using `college_id`, allowing a single deployment to securely serve multiple institutions.

---

# 🎯 Impact

CampusConnect transforms isolated academic achievements into a connected ecosystem where:

- Students discover opportunities.
- Faculty discover talent.
- Colleges discover insights.

By combining privacy, verification, AI-powered recommendations, and institutional analytics, CampusConnect aims to become the digital backbone of modern higher education.

---

# 👥 Contributors

- **Srijita Sarkar**
- **Manas Vishnu**
- **Anvita De**
- **Shreya**

---

# 📜 License

This project is licensed under the **MIT License**.

---

# ❤️ Vision

> *"Every student deserves to be discovered for their talent—not just their network."*

CampusConnect is more than a portfolio platform.

It is the foundation of a connected, collaborative, and data-driven campus ecosystem that empowers students, faculty, and institutions alike.
