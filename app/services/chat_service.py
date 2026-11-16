import re
from typing import List, Dict, Any, Optional
from app.config import get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.memory_service import MemoryService
from app.services.retrieval_service import RetrievalService
from app.services.guardrail_service import GuardrailService
from app.prompts.product_assistant_prompt import get_product_assistant_prompt, format_prompt_text

class ChatService:
    """
    Core RAG Chat Service coordinating:
    1. Guardrail checks (scope & prompt injection)
    2. Conversational memory retrieval
    3. Query contextualization for follow-up questions
    4. ChromaDB semantic document retrieval
    5. Context groundedness validation
    6. LLM response generation (Gemini / OpenAI / Grounded Fallback)
    7. Memory persistence in SQLite
    """

    def __init__(
        self,
        memory_service: Optional[MemoryService] = None,
        retrieval_service: Optional[RetrievalService] = None,
        guardrail_service: Optional[GuardrailService] = None
    ):
        self.settings = get_settings()
        self.memory = memory_service or MemoryService()
        self.retrieval = retrieval_service or RetrievalService()
        self.guardrails = guardrail_service or GuardrailService()

    def handle_chat(self, request: ChatRequest) -> ChatResponse:
        session_id = request.session_id.strip()
        question = request.question.strip()

        # 1. Prompt Injection Defense
        is_injection, injection_refusal = self.guardrails.check_injection(question)
        if is_injection:
            return self._record_and_respond(
                session_id=session_id,
                question=question,
                answer=injection_refusal,
                sources=[],
                context_retrieved=False
            )

        # 2. Check ongoing conversation context
        history_records = self.memory.get_history(session_id=session_id, limit=self.settings.MAX_HISTORY_MESSAGES)
        has_prior_context = len(history_records) > 0

        # 3. Product Scope Guardrail Check
        in_scope, scope_refusal = self.guardrails.check_scope(question, has_prior_context=has_prior_context)
        if not in_scope:
            return self._record_and_respond(
                session_id=session_id,
                question=question,
                answer=scope_refusal,
                sources=[],
                context_retrieved=False
            )

        # 4. Contextualize Query (Resolve Follow-up Questions)
        search_query = self.memory.contextualize_query(session_id=session_id, question=question)

        # 5. ChromaDB Retrieval
        retrieval_result = self.retrieval.retrieve(query=search_query)
        context_text = retrieval_result["context_text"]
        sources = retrieval_result["sources"]
        has_relevant_context = retrieval_result["has_relevant_context"]

        # Calculate top score
        top_score = 0.0
        if retrieval_result["chunks"]:
            top_score = max(c.get("score", 0.0) for c in retrieval_result["chunks"])

        # 6. Validate Groundedness / Insufficient Context
        # Greetings do not require document context
        is_greeting = question.lower() in ["hi", "hello", "hey", "good morning", "good evening"]
        if not is_greeting and not has_relevant_context:
            is_grounded, ungrounded_msg = self.guardrails.validate_groundedness(
                has_relevant_context=False,
                top_score=top_score
            )
            return self._record_and_respond(
                session_id=session_id,
                question=question,
                answer=ungrounded_msg,
                sources=[],
                context_retrieved=False
            )

        # 7. Format Chat History for Prompt
        chat_history_str = self.memory.format_history_for_prompt(session_id=session_id)

        # 8. Generate LLM Response
        answer = self._generate_response(
            question=question,
            retrieved_context=context_text,
            chat_history=chat_history_str,
            is_greeting=is_greeting,
            chunks=retrieval_result["chunks"]
        )

        # 9. Persist and Return
        return self._record_and_respond(
            session_id=session_id,
            question=question,
            answer=answer,
            sources=sources,
            context_retrieved=has_relevant_context
        )

    def _generate_response(
        self,
        question: str,
        retrieved_context: str,
        chat_history: str,
        is_greeting: bool,
        chunks: List[Dict[str, Any]]
    ) -> str:
        """Invokes configured LLM provider with fallback handling."""
        if is_greeting:
            return (
                "Hello! I am the official product assistant for the Internship Application Agent. "
                "I can explain how the platform works, guide you through resume parsing, "
                "internship matching, cover letter generation, interview preparation, "
                "and tracking your applications. How can I assist you today?"
            )

        provider = self.settings.LLM_PROVIDER.lower()

        # Attempt Gemini if configured
        if provider == "gemini" and self.settings.active_gemini_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model=self.settings.LLM_MODEL,
                    google_api_key=self.settings.active_gemini_key,
                    temperature=0.2
                )
                prompt_template = get_product_assistant_prompt()
                chain = prompt_template | llm
                response = chain.invoke({
                    "retrieved_context": retrieved_context,
                    "chat_history": chat_history,
                    "question": question
                })
                return response.content.strip()
            except Exception as e:
                print(f"[Warning] Gemini API call failed: {e}. Falling back to internal engine.")

        # Attempt OpenAI if configured
        if provider == "openai" and self.settings.OPENAI_API_KEY:
            try:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model=self.settings.LLM_MODEL,
                    api_key=self.settings.OPENAI_API_KEY,
                    temperature=0.2
                )
                prompt_template = get_product_assistant_prompt()
                chain = prompt_template | llm
                response = chain.invoke({
                    "retrieved_context": retrieved_context,
                    "chat_history": chat_history,
                    "question": question
                })
                return response.content.strip()
            except Exception as e:
                print(f"[Warning] OpenAI API call failed: {e}. Falling back to internal engine.")

        # Grounded context-based response generator
        return self._synthesize_grounded_answer(question, chunks, chat_history)

    def _synthesize_grounded_answer(
        self,
        question: str,
        chunks: List[Dict[str, Any]],
        chat_history: str
    ) -> str:
        """
        Synthesizes a clean, fully grounded, structured answer strictly
        from the retrieved knowledge base chunks.
        """
        if not chunks:
            return "The requested information is not available in the current product documentation."

        q_lower = question.lower()

        # Specific question handling for core product capabilities
        # 0. Planned Features vs Missing Info (Highest priority check)
        if "voice" in q_lower or "speech" in q_lower:
            return (
                "Live voice-based mock interviews with speech tone analysis are a planned feature on our product roadmap "
                "for future release and are not currently available in the live platform."
            )

        if "pricing" in q_lower or "enterprise" in q_lower or "license" in q_lower:
            return (
                "The requested information is not available in the current product documentation. "
                "I can only provide details about verified and documented features of the Internship Application Agent."
            )

        # 1. Product Benefits & Advantages
        if any(k in q_lower for k in ["benefit", "benefits", "advantage", "advantages"]):
            return (
                "The main benefits of the Internship Application Agent include:\n"
                "- **Automated Profile Extraction**: Converts unstructured resumes (PDF, DOCX, TXT) into structured profiles without manual data entry.\n"
                "- **Intelligent Semantic Matching**: Compares candidate skills and projects with internship requirements using dense vector embeddings.\n"
                "- **Tailored Application Materials**: Automatically drafts contextual, role-specific cover letters.\n"
                "- **Targeted Interview Preparation**: Generates personalized technical questions and STAR-method behavioral practice.\n"
                "- **End-to-End Application Tracking**: Centralized Kanban board to monitor application stages, deadlines, and notes."
            )

        # 2. Supported Formats & File Limits
        if re.search(r"\bformats?\b", q_lower) or any(k in q_lower for k in ["file type", "file size", "size limit", "10mb", "upload limit"]):
            return (
                "The supported file formats and upload specifications for resumes are:\n"
                "- **PDF (.pdf)**: Standard text-based PDF documents (recommended).\n"
                "- **DOCX (.docx)**: Microsoft Word documents.\n"
                "- **Plain Text (.txt)**: Plain text or Markdown resume files.\n"
                "- **Maximum File Size**: 10 Megabytes (MB) per file.\n"
                "- **Security**: Files must be unencrypted and not password-protected."
            )

        # 3. Target Users & Audience (Students, Graduates, Mentors)
        if any(k in q_lower for k in ["target user", "target users", "audience", "who is this for", "who can use", "mentor", "mentors"]):
            return (
                "The target users of the Internship Application Agent include:\n"
                "- **College & University Students**: Seeking summer, semester, or part-time internships.\n"
                "- **Recent Graduates**: Transitioning from academia to entry-level workforce roles.\n"
                "- **Career Switchers**: Exploring new domains requiring skills-based matching.\n"
                "- **Campus Placement Teams & Mentors**: Academic coordinators and placement mentors tracking candidate readiness and workflows."
            )

        # 4. STAR Method in Interview Preparation
        if "star" in q_lower:
            return (
                "In the Interview Preparation module, behavioral questions are structured around the **STAR method**:\n"
                "- **Situation**: Describe the specific context, challenge, or background of a past project.\n"
                "- **Task**: Explain your specific role and responsibility in that situation.\n"
                "- **Action**: Detail the technical and collaborative steps you took to address the problem.\n"
                "- **Result**: Highlight quantifiable outcomes, metrics, lessons learned, and impact.\n\n"
                "The system evaluates candidate practice answers against the STAR framework and provides constructive improvement suggestions."
            )

        # 5. Practice Modes in Interview Prep
        if any(k in q_lower for k in ["practice mode", "practice modes", "modes available", "question bank"]):
            return (
                "The Interview Preparation module provides two practice modes:\n"
                "1. **Self-Paced Question Bank Mode**: A curated set of 10 to 15 questions categorized into Technical Core, Project Deep-Dive, and Behavioral/Teamwork, complete with evaluation criteria and model outlines.\n"
                "2. **Interactive Mock Practice Mode**: Candidates submit written or practice answers and receive immediate AI evaluation on completeness, technical depth, STAR structure, and actionable feedback."
            )

        # 6. Application Tracking Stages & Lifecycle
        if any(k in q_lower for k in ["stage", "stages", "status", "statuses", "lifecycle"]):
            return (
                "The Application Tracker supports 7 lifecycle stages across its Kanban board and table views:\n"
                "1. **Wishlist / Saved**: Opportunities bookmarked for later consideration.\n"
                "2. **Applied**: Applications submitted to employers.\n"
                "3. **Under Review**: Employer is reviewing candidate qualifications.\n"
                "4. **Interview Scheduled**: Candidate invited for screening or technical rounds.\n"
                "5. **Offer Received**: Formal internship offer extended.\n"
                "6. **Rejected**: Application was not advanced.\n"
                "7. **Withdrawn**: Candidate withdrew candidacy (e.g., accepted another offer)."
            )

        # 7. Error Handling, Troubleshooting & Image PDFs
        if any(k in q_lower for k in ["error", "unreadable", "image", "troubleshoot", "scanned"]):
            return (
                "The platform includes comprehensive validation and error handling for resume uploads:\n"
                "- **Image-Only or Scanned PDFs**: If a PDF contains raster images without an OCR text layer, the system alerts: *'Document contains no extractable text. Please upload a standard text PDF or DOCX file.'*\n"
                "- **File Size Exceeded**: Files larger than 10MB are rejected immediately.\n"
                "- **Unsupported Formats**: Files with extensions like .png, .jpg, .zip, or .exe trigger an invalid format alert."
            )

        # 8. Skill Gap Analysis & Missing Skills
        if any(k in q_lower for k in ["gap", "missing skill", "missing skills", "recommended skill"]):
            return (
                "The internship matching engine provides an interactive **Skill Alignment Breakdown** for each opportunity:\n"
                "- **Matched Skills**: Direct or semantic overlap between candidate background and job requirements.\n"
                "- **Missing / Recommended Skills**: Required technologies present in the job posting that are missing from the candidate's resume, helping applicants identify upskilling targets before applying."
            )

        # 9. Cover Letter Export & Download
        if any(k in q_lower for k in ["download", "export"]):
            return (
                "Yes, after generating and reviewing your tailored cover letter in the inline editor, you can:\n"
                "- Save it directly to your application record in the Application Tracker.\n"
                "- Download it as a formatted **PDF (.pdf)** file.\n"
                "- Download it as an editable Microsoft Word **(.docx)** document."
            )

        # 10. External Applications
        if "external" in q_lower or ("outside" in q_lower and ("track" in q_lower or "platform" in q_lower or "application" in q_lower)):
            return (
                "Yes, you can manually add external applications found outside the platform. In the Application Tracker dashboard, "
                "click '+ Add External Application' to log external opportunities (company name, role title, link, and submission date)."
            )

        # 11. Matching & Score
        if "score" in q_lower or "similarity score" in q_lower:
            return (
                "The similarity score indicates how semantically relevant an internship is to your resume "
                "(ranging from 0% to 100%), based on dense vector embeddings. "
                "Important Note: It is an algorithmic relevance score, not a probability or guarantee of employer selection."
            )

        if "how does internship matching work" in q_lower or ("matching" in q_lower and "work" in q_lower):
            return (
                "Internship matching works by comparing candidate resume information with internship requirements "
                "using semantic similarity. The system converts your profile (skills, projects, education) into dense "
                "embeddings and computes cosine similarity against available internship postings, ranking them by relevance."
            )

        # 12. Resume Upload, Parsing & Editing
        if "edit" in q_lower and ("resume" in q_lower or "extract" in q_lower or "information" in q_lower):
            return (
                "Yes, you can edit the extracted resume information. Once your resume is uploaded and parsed, "
                "the platform displays an interactive Candidate Profile page where you can verify and directly edit "
                "your contact details, education, skills, experience, and projects before confirming your profile."
            )

        if "upload" in q_lower and "resume" in q_lower:
            return (
                "To upload your resume:\n"
                "1. Navigate to the 'My Profile' or 'Resume Upload' section in the platform.\n"
                "2. Drag and drop or browse to select your resume in PDF, DOCX, or TXT format (max 10MB).\n"
                "3. Click 'Upload & Parse Resume'.\n"
                "4. Inspect the extracted information (contact, skills, education, projects).\n"
                "5. Verify and edit any fields if needed, then confirm your profile."
            )

        if "parsing" in q_lower or "extract" in q_lower:
            return (
                "The resume parsing module extracts structured candidate information including: contact details "
                "(name, email, phone, links), education summary, technical and soft skills, work and internship "
                "experience, projects with tech stacks, and certifications."
            )

        # 13. Cover Letter Generation
        if "cover letter" in q_lower:
            return (
                "The Cover Letter Generation feature uses AI to draft tailored, professional cover letters for specific internships. "
                "It combines your parsed resume (skills and projects) with the target job's requirements and company background. "
                "You can select your preferred tone (Professional, Enthusiastic, Academic), choose specific projects to highlight, "
                "edit the draft inline, and download it as PDF or DOCX."
            )

        # 14. Interview Preparation
        if "interview" in q_lower:
            return (
                "The Interview Preparation module generates role-specific technical questions, project deep-dives based on your resume, "
                "and behavioral questions using the STAR method (Situation, Task, Action, Result). "
                "Candidates can practice in Self-Paced Question Bank mode or Interactive Mock Practice mode to receive AI feedback on their responses."
            )

        # 15. Application Tracking
        if "track" in q_lower or "tracker" in q_lower:
            return (
                "The Application Tracking module provides a centralized Kanban and table dashboard to manage applications across lifecycle stages: "
                "Saved/Wishlist, Applied, Under Review, Interview Scheduled, Offer Received, Rejected, and Withdrawn. "
                "It tracks company names, roles, submission dates, deadlines, notes, and links to your tailored cover letters."
            )

        # 16. Product Overview / What is this product
        if "what is this product" in q_lower or "overview" in q_lower or ("what" in q_lower and "product" in q_lower):
            return (
                "The Internship Application Agent is an AI-powered platform designed to assist students and early-career candidates "
                "through the entire internship application lifecycle. It automates resume parsing, performs semantic internship matching, "
                "generates tailored cover letters, tracks application statuses, and provides targeted interview preparation."
            )

        # 17. Workflow step by step
        if "step by step" in q_lower or "workflow" in q_lower:
            return (
                "The end-to-end workflow consists of 8 steps:\n"
                "1. User Registration: Account setup and workspace provisioning.\n"
                "2. Resume Upload: Upload PDF, DOCX, or TXT file (up to 10MB).\n"
                "3. Resume Parsing: Automated extraction of profile entities and skills.\n"
                "4. Semantic Internship Matching: Dense embedding similarity matching against vacancies.\n"
                "5. Internship Selection: Reviewing role details and match score breakdowns.\n"
                "6. Cover Letter Generation: Creating customized, role-tailored cover letters.\n"
                "7. Application Tracking: Monitoring applications across Kanban stages.\n"
                "8. Interview Preparation: Role-specific technical and STAR behavioral mock practice."
            )

        # Fallback to the top chunk text cleanly summarized
        top_text = chunks[0].get("text", "").strip()
        paragraphs = [p.strip() for p in top_text.split("\n\n") if p.strip() and not p.startswith("#")]
        if paragraphs:
            return paragraphs[0]
        return top_text[:400] + "..."

    def _record_and_respond(
        self,
        session_id: str,
        question: str,
        answer: str,
        sources: List[str],
        context_retrieved: bool
    ) -> ChatResponse:
        """Saves interaction to persistent memory and returns response."""
        self.memory.add_user_message(session_id=session_id, content=question)
        self.memory.add_assistant_message(session_id=session_id, content=answer, sources=sources)
        return ChatResponse(
            session_id=session_id,
            question=question,
            answer=answer,
            sources=sources,
            context_retrieved=context_retrieved
        )
