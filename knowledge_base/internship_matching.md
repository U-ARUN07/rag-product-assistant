# Internship Matching: Mechanism, Scoring & Usage Guide

## Overview
The Internship Matching engine bridges candidate qualifications with active internship vacancies. Rather than relying on simple keyword matching—which frequently misses qualified candidates who use synonymous phrasing—the platform utilizes **semantic similarity embeddings** to understand the deeper contextual meaning of a candidate's background and match it with employer requirements.

## How Semantic Matching Works
1. **Candidate Profile Representation**: The system compiles the candidate's skills, academic background, project descriptions, and prior experiences into a contextual candidate summary.
2. **Dense Vector Embeddings**: Using high-dimensional sentence transformer embeddings (e.g., `sentence-transformers/all-MiniLM-L6-v2`), the system maps both the candidate summary and all available internship job descriptions into a shared semantic vector space.
3. **Similarity Calculation**: For each available internship, the system computes the cosine similarity between the candidate vector and the internship requirement vector.
4. **Ranking & Augmentation**: Results are augmented with explicit hard-filter checks (such as required graduation year, minimum GPA if mandated, or mandatory language proficiency) and sorted in descending order of match relevance.

## Understanding the Match Score
- **Score Range**: The match score is displayed as a normalized percentage from **0% to 100%** (or a decimal between 0.0 and 1.0).
- **Interpretation**:
  - **85% - 100% (Strong Match)**: High semantic overlap; the candidate's skills, coursework, and projects closely reflect the job description.
  - **70% - 84% (Good Match)**: Moderate semantic overlap; core competencies align, though some specialized frameworks or nice-to-have tools may be absent.
  - **50% - 69% (Potential Match)**: Basic foundational overlap; transferable skills present, but candidate may need upskilling in several job criteria.
  - **Below 50% (Low Relevance)**: Minimal alignment with stated requirements.
- **IMPORTANT CLARIFICATION**:
  - The similarity score is an algorithmic measure of **semantic relevance to the job posting**.
  - It **is NOT** a probability, prediction, or guarantee of employer selection or job offer.
  - An applicant with a 95% match score may still be evaluated based on factors outside the resume text (e.g., interview performance, competition volume, cultural fit).

## Skill-Based Matching & Gap Analysis
Along with the match score, each internship card provides an interactive **Skill Alignment Breakdown**:
- **Matched Skills**: Direct or semantic matches between candidate profile and job requirements (e.g., Candidate has "FastAPI" -> Job asks for "Python Backend Frameworks").
- **Missing / Recommended Skills**: Required technologies present in the job posting that are missing from the candidate's resume (e.g., "Docker", "Kubernetes"). This allows candidates to identify learning goals before applying.

## Step-by-Step Instructions: How to Find and Select Matching Internships
1. **Navigate to Matching Tab**: Click on **Internship Matches** in the top navigation bar.
2. **Review Auto-Ranked Recommendations**: The page immediately displays recommendations sorted by highest semantic match score.
3. **Apply Custom Filters**:
   - *Domain*: Software Development, Machine Learning, Data Analytics, DevOps, Cyber Security, etc.
   - *Work Arrangement*: Remote, Hybrid, or On-site.
   - *Location*: Filter by city, country, or time zone.
   - *Stipend & Duration*: Set minimum monthly stipend and desired internship duration (e.g., 2 months, 6 months).
4. **Explore Role Details**: Click on any internship card to inspect the comprehensive job description, company overview, role requirements, and skill alignment breakdown.
5. **Select Role for Application**: Click **Select Role** or **Add to Pipeline**. This action links the opportunity to your workspace for instant cover letter generation and application tracking.
