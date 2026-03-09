# 📄 Resume Readiness Checker

An AI-powered tool that evaluates your resume against industry standards and tells you exactly where you stand.

---

## 🚀 What It Does

Upload your resume, enter the role and years of experience required — and get:

- Role readiness score & missing skills
- Detailed email alert with strengths, weaknesses & recommendations
- Suggested improvements for your resume

---

## 🛠️ Tech Stack

`Python` `Streamlit` `Gemini API` `Groq API` `n8n` `Git`

---

## 📦 Setup

**1. Clone the repo**
```bash
git clone https://github.com/siddharthpurswani/resume-readiness-checker.git
cd resume-readiness-checker
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add your API keys**

Create `.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your_gemini_api_key"
GROQ_API_KEY = "your_groq_api_key"
N8N_WEBHOOK_URL = "your_n8n_webhook_url"
```

**4. Run the app**
```bash
streamlit run app.py
```

---

## 🧭 How to Use

1. Upload your resume (PDF)
2. Enter the target role & years of experience required
3. Click **Evaluate** — view your readiness score & missing skills
4. Click **Send Email Alert** for a full analysis with recommendations

---

## 📁 Project Structure

```
resume-readiness-checker/
├── app.py
├── requirements.txt
├── .streamlit/
│   └── secrets.toml
└── README.md
```

---

## 📬 Contact

[LinkedIn](https://linkedin.com/in/siddharthpurswani) · [GitHub Issues](https://github.com/siddharthpurswani/resume-readiness-checker/issues)
