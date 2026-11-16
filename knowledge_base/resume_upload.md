# Resume Upload and Parsing: User Guide & Specifications

## Overview
The Resume Upload module is the foundational data intake component of the Internship Application Agent. It ingests candidate resumes, extracts raw text content, and transforms unstructured text into structured, normalized profile entities used across matching, cover letter generation, and interview preparation.

## Supported File Formats & File Limits
- **PDF (.pdf)**: Standard text-based PDF documents (recommended). Scanned image-only PDFs should have selectable text or standard OCR.
- **DOCX (.docx)**: Microsoft Word documents with standard headings and bulleted structures.
- **Plain Text (.txt)**: Plain text or Markdown-formatted resume files.
- **Maximum File Size**: 10 Megabytes (MB) per uploaded file.
- **File Integrity**: Files must be unencrypted and not password-protected.

## Step-by-Step Instructions: How to Upload Your Resume
1. **Navigate to the Profile Section**: In the platform navigation sidebar, click on **My Profile** or **Resume Upload**.
2. **Select or Drag File**: Click the **Browse File** button or drag-and-drop your resume file into the upload dropzone.
3. **Initiate Processing**: Click **Upload & Parse Resume**. The system displays a progress bar indicating extraction progress.
4. **Inspect Extracted Information**: Upon completion, the parsed profile is presented in the profile dashboard.
5. **Verify and Edit**: Check your contact details, education history, skills list, and past projects. If any detail is misparsed or omitted, edit the field directly.
6. **Save Profile**: Click **Confirm Profile** to index your verified profile into the matching engine.

## Extracted Profile Fields
The parsing pipeline extracts and classifies the following key data points:
- **Contact Details**: Full name, email address, telephone number, city/state, LinkedIn URL, GitHub profile, and portfolio website.
- **Education Summary**: University or college name, degree (B.Tech, B.S., M.S., etc.), major/field of study, start and expected graduation dates, GPA or marks percentage.
- **Technical Skills**: Programming languages (Python, Java, JavaScript, C++, etc.), frameworks/libraries (React, FastAPI, Django, PyTorch, LangChain), databases (PostgreSQL, MongoDB, ChromaDB), and developer tools (Git, Docker, Linux, AWS).
- **Soft Skills & Competencies**: Problem solving, teamwork, leadership, written communication, agile methodologies.
- **Work & Internship Experience**: Prior employers, roles held, start and end dates, key responsibilities, and quantifiable impact metrics.
- **Academic & Personal Projects**: Project titles, tech stack utilized, functional description, and GitHub/deployment links.
- **Certifications & Honors**: Professional certifications (AWS Certified, Coursera/Infosys Springboard certifications), hackathon awards, and scholarships.

## How to View and Manage Extracted Information
- Users can view their extracted information on the **Candidate Profile** page.
- Fields are organized into editable cards: *Personal Info*, *Education*, *Skills*, *Experience*, and *Projects*.
- Candidates can re-upload an updated resume at any time. When a new resume is uploaded, the user can choose whether to replace the existing profile or merge new skills and projects.

## Error Handling & Troubleshooting
- **Unreadable or Image-Only PDF**: If the PDF contains raster images without OCR text layer, the system displays an error: `"Document contains no extractable text. Please upload a standard text PDF or DOCX file."`
- **File Exceeds Size Limit**: Files larger than 10MB will be rejected with an immediate client-side error notification.
- **Unsupported File Extension**: Uploading files such as .png, .jpg, .zip, or .exe will trigger an invalid format alert.
