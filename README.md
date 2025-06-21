# 🔍 Legal Insights Automation Pipeline

Smart AI-powered research, analysis, and email delivery for lawyers.

---

## 🚀 What It Does

This pipeline automatically:

1. Extracts a lawyer’s **specializations** and **client focus** from bios or web searches.
2. Searches sources like:
   - [FCA News](https://www.fca.org.uk/news)
   - [Bank of England](https://www.bankofengland.co.uk/news/)
   - [UK Supreme Court](https://www.supremecourt.uk/news/index.html)
3. Summarizes **recent legal updates** aligned to the lawyer’s profile.
4. Styles the report in **professional HTML**.
5. **Emails** the report via SendGrid.

---

## 🧠 Architecture Overview

- `UserAnalyser`: Extracts lawyer's areas of interest using public search tools.
- `NewsQueryAgent`: Finds and summarizes recent legal developments.
- `ReportGeneratorAgent`: Creates a personalized legal report.
- `HtmlStyler`: Converts the report to styled HTML.
- `EmailSenderAgent`: Sends the final report to the lawyer.

Agents are orchestrated using Google ADK’s `SequentialAgent` and `ParallelAgent` utilities, powered by Gemini 2.5 Flash.

---


## 📌 Notes
Public data only — respects client confidentiality.

Easily extendable to other professions or jurisdictions
