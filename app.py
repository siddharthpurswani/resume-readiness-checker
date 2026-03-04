import streamlit as st
import pdfplumber
import json
import requests
from google import genai

# ─────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Resume Readiness Checker",
    page_icon="🎯",
    layout="centered"
)

# ─────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────
st.title("🎯 Resume Readiness Checker")
st.markdown("Upload your resume and check how ready you are for your target role.")
st.divider()

# ─────────────────────────────────────────
#  STAGE 1 — RESUME UPLOAD
# ─────────────────────────────────────────
st.subheader("📄 Stage 1: Upload Your Resume")

uploaded_file = st.file_uploader(
    "Upload your resume (PDF or TXT)",
    type=["pdf", "txt"],
    help="We'll extract the text and analyse it against your target role."
)

# ─────────────────────────────────────────
#  TEXT EXTRACTION FUNCTION
# ─────────────────────────────────────────
def extract_text(file) -> str:
    """Extract raw text from uploaded PDF or TXT file."""
    if file.type == "application/pdf":
        with pdfplumber.open(file) as pdf:
            pages = [page.extract_text() for page in pdf.pages if page.extract_text()]
        return "\n".join(pages)
    elif file.type == "text/plain":
        return file.read().decode("utf-8")
    return ""

# ─────────────────────────────────────────
#  STAGE 1 LOGIC
# ─────────────────────────────────────────
if uploaded_file:
    if "resume_text" not in st.session_state or \
       st.session_state.get("uploaded_filename") != uploaded_file.name:

        with st.spinner("📖 Reading your resume..."):
            resume_text = extract_text(uploaded_file)

        if resume_text.strip():
            st.success("✅ Resume uploaded successfully!")
            st.session_state["resume_text"] = resume_text
            st.session_state["uploaded_filename"] = uploaded_file.name
        else:
            st.error("❌ Could not extract any text. Please try a different file.")
            st.session_state.pop("resume_text", None)
            st.session_state.pop("uploaded_filename", None)
    else:
        st.success("✅ Resume uploaded successfully!")
else:
    st.session_state.pop("resume_text", None)
    st.session_state.pop("uploaded_filename", None)
    st.info("👆 Please upload your resume to get started.")

# ─────────────────────────────────────────
#  STAGE 2 — ROLE & EXPERIENCE INPUT
# ─────────────────────────────────────────
st.divider()
st.subheader("📝 Stage 2: Role & Experience Details")

if "resume_text" not in st.session_state:
    st.warning("⏳ Complete Stage 1 first by uploading your resume.")
else:
    col1, col2 = st.columns(2)

    with col1:
        target_role = st.text_input(
            "🎯 Target Job Role",
            placeholder="e.g. ML Engineer, Data Scientist",
            help="The role you are applying for."
        )

    with col2:
        experience_required = st.number_input(
            "📅 Years of Experience Required for Role",
            min_value=0,
            max_value=30,
            value=0,
            step=1,
            help="How many years does the job posting require?"
        )

    analyse_btn = st.button("🔍 Analyse My Resume", use_container_width=True)

    # ─────────────────────────────────────────
    #  GEMINI EXTRACTION FUNCTION (3-LAYER)
    # ─────────────────────────────────────────
    def analyse_resume(resume_text: str, role: str, exp_required: int) -> dict:
        """Send resume + role context to Gemini for smart 3-layer analysis."""

        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

        prompt = f"""
You are a senior technical recruiter and career coach with 15+ years of experience.
You understand that a resume is more than a list of skills — it tells a story of growth,
intuition, and real-world problem solving.

Analyse the resume below for the role of "{role}" which requires {exp_required} years of experience.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EVALUATION FRAMEWORK (3 Layers)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LAYER 1 — SKILLS MATCH (40% weight)
- Identify skills EXPLICITLY listed in the resume.
- Also INFER implied skills from project descriptions and achievements.
  Example: "Built a real-time recommendation engine" implies Python, ML pipelines, low-latency systems.
  Example: "Reduced API response time by 40%" implies performance optimization, profiling, backend depth.
- Compare against the 6-10 must-have skills for "{role}" by current industry standards.

LAYER 2 — EXPERIENCE DEPTH (40% weight)
- Extract years of experience from the resume.
- Do NOT just count years — evaluate QUALITY of experience:
  * Did they ship to production? (depth signal)
  * Did they work across the full stack or pipeline? (breadth signal)
  * Did they solve ambiguous, open-ended problems? (seniority signal)
  * Did they work at scale (large data, large teams, large user base)? (impact signal)
- A candidate with 2 years but strong depth signals can match a 4-year requirement.

LAYER 3 — SENIORITY SIGNALS (20% weight)
- Look for evidence of: leadership, mentoring, project ownership, cross-functional collaboration.
- Look for: promotions, scope expansion, independent decision-making.
- Look for: publications, open source contributions, side projects, certifications.
- These signals indicate the candidate has developed professional intuition beyond just skills.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCORING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- skills_match_score: % of required skills present (explicit + implied)
- experience_depth_score: quality-adjusted experience score out of 100%
- seniority_score: seniority signals score out of 100%
- overall_readiness_score: weighted average (40/40/20)

READINESS CATEGORIES — MANDATORY FIELD:
- "Ideal Candidate"   → overall_readiness_score >= 85%
- "Strong Candidate"  → overall_readiness_score >= 65%
- "Needs Upskilling"  → overall_readiness_score >= 45%
- "Significant Gap"   → overall_readiness_score < 45%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- A candidate strong in Layer 2 + Layer 3 can compensate for gaps in Layer 1.
- Do NOT penalise a candidate just for not listing buzzwords if their projects imply those skills.
- Be fair — evaluate like a thoughtful human recruiter, not a keyword scanner.
- "readiness_category" is MANDATORY — NEVER omit it. It must be exactly one of the four values above.

Return ONLY a valid JSON object with this exact schema — no extra text, no markdown:
{{
  "role": string,
  "experience_required": number,
  "experience_on_resume": number,
  "skills_required": [list of 6-10 must-have skills for this role],
  "skills_present": [explicitly listed skills relevant to role],
  "implied_skills": [skills inferred from projects and achievements],
  "skills_missing": [important skills neither listed nor implied],
  "seniority_signals": [list of seniority/leadership/impact signals found],
  "skills_match_score": string (e.g. "70%"),
  "experience_depth_score": string (e.g. "80%"),
  "seniority_score": string (e.g. "60%"),
  "overall_readiness_score": string (e.g. "72%"),
  "experience_gap": number (0 if no gap or compensated),
  "compensating_factor": boolean,
  "compensating_reason": string (explain if compensating_factor is true, else "None"),
  "readiness_category": "Ideal Candidate" or "Strong Candidate" or "Needs Upskilling" or "Significant Gap"
}}

RESUME:
{resume_text}
"""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        raw = response.text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        return json.loads(raw.strip())

    # ─────────────────────────────────────────
    #  READINESS CATEGORY FALLBACK
    # ─────────────────────────────────────────
    def apply_readiness_fallback(result: dict) -> dict:
        """Fallback if Gemini omits readiness_category."""
        if not result.get("readiness_category"):
            score = int(result.get("overall_readiness_score", "0%").replace("%", ""))
            if score >= 85:
                result["readiness_category"] = "Ideal Candidate"
            elif score >= 65:
                result["readiness_category"] = "Strong Candidate"
            elif score >= 45:
                result["readiness_category"] = "Needs Upskilling"
            else:
                result["readiness_category"] = "Significant Gap"
        return result

    # ─────────────────────────────────────────
    #  RUN ANALYSIS
    # ─────────────────────────────────────────
    if analyse_btn:
        if not target_role.strip():
            st.warning("⚠️ Please enter the target job role.")
        elif experience_required == 0:
            st.warning("⚠️ Please enter the years of experience required for the role.")
        else:
            with st.spinner("🤖 Analysing your resume with Gemini..."):
                try:
                    result = analyse_resume(
                        st.session_state["resume_text"],
                        target_role,
                        experience_required
                    )
                    result = apply_readiness_fallback(result)
                    st.session_state["gemini_result"] = result
                except Exception as e:
                    st.error(f"❌ Gemini API error: {e}")

    # ─────────────────────────────────────────
    #  DISPLAY STRUCTURED JSON OUTPUT
    # ─────────────────────────────────────────
    if "gemini_result" in st.session_state:
        result = st.session_state["gemini_result"]

        st.divider()
        st.subheader("📊 Output 1: Structured Extraction")

        # Row 1 - 4 score metrics
        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("🎯 Skills Match", result.get("skills_match_score", "N/A"))
        col_b.metric("📅 Experience Depth", result.get("experience_depth_score", "N/A"))
        col_c.metric("🏅 Seniority", result.get("seniority_score", "N/A"))
        col_d.metric("⭐ Overall Readiness", result.get("overall_readiness_score", "N/A"))

        # Row 2 - readiness category + experience on resume
        col_e, col_f = st.columns(2)
        col_e.metric("📌 Readiness Category", result.get("readiness_category", "N/A"))
        col_f.metric("📅 Experience on Resume", f'{result.get("experience_on_resume", "N/A")} yrs')

        # Compensating factor callout
        if result.get("compensating_factor"):
            st.info(f"💡 **Compensating Factor:** {result.get('compensating_reason', '')}")

        # 3 column skills breakdown
        col_g, col_h, col_i = st.columns(3)
        with col_g:
            st.markdown("**✅ Skills Present**")
            for skill in result.get("skills_present", []):
                st.markdown(f"- {skill}")

        with col_h:
            st.markdown("**🔍 Implied Skills**")
            for skill in result.get("implied_skills", []):
                st.markdown(f"- {skill}")

        with col_i:
            st.markdown("**❌ Skills Missing**")
            for skill in result.get("skills_missing", []):
                st.markdown(f"- {skill}")

        # Seniority signals
        if result.get("seniority_signals"):
            st.markdown("**🏅 Seniority Signals Detected**")
            for signal in result.get("seniority_signals", []):
                st.markdown(f"- {signal}")

        with st.expander("🔍 View Full JSON"):
            st.json(result)

# ─────────────────────────────────────────
#  STAGE 3 — EMAIL AUTOMATION
# ─────────────────────────────────────────
st.divider()
st.subheader("📧 Stage 3: Email Automation")

if "gemini_result" not in st.session_state:
    st.warning("⏳ Complete Stage 2 first to unlock email automation.")
else:
    recipient_email = st.text_input(
        "📩 Recipient Email ID",
        placeholder="e.g. candidate@gmail.com"
    )

    send_btn = st.button("📤 Send Alert Mail", use_container_width=True)

    if send_btn:
        if not recipient_email.strip():
            st.warning("⚠️ Please enter a recipient email address.")
        else:
            payload = {
                "resume_text": st.session_state["resume_text"],
                "extracted_json": st.session_state["gemini_result"],
                "role": st.session_state["gemini_result"].get("role"),
                "readiness_category": st.session_state["gemini_result"].get("readiness_category"),
                "recipient_email": recipient_email
            }

            with st.spinner("⚙️ Running n8n workflow..."):
                try:
                    response = requests.post(
                        st.secrets["N8N_WEBHOOK_URL"],
                        json=payload,
                        timeout=60
                    )
                    result = response.json()
                    st.session_state["n8n_result"] = result
                except Exception as e:
                    st.error(f"❌ Webhook error: {e}")

# ─────────────────────────────────────────
#  STAGE 4 — DISPLAY ALL 4 OUTPUTS
# ─────────────────────────────────────────
st.divider()
st.subheader("📋 Stage 4: Final Results")

if "n8n_result" not in st.session_state:
    st.warning("⏳ Send an alert mail to see final results.")
else:
    n8n = st.session_state["n8n_result"]

    # Output 2 - Final Analytical Answer
    st.markdown("### 🧠 Output 2: Final Analytical Answer")
    st.write(n8n.get("final_answer", "N/A"))

    # Output 3 - Generated Email Body
    st.markdown("### 📧 Output 3: Generated Email Body")
    st.write(n8n.get("email_body", "N/A"))

    # Output 4 - Email Automation Status
    st.markdown("### 📬 Output 4: Email Automation Status")
    status = n8n.get("status", "N/A")
    if status == "SENT":
        st.success(f"✅ Alert Email Status: {status}")
    else:
        st.warning(f"⚠️ Status: {status}")