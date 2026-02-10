#!/usr/bin/env python3
"""Generate a tailored CV by combining a generic LaTeX resume with a job posting."""

import glob
import os
import re
import subprocess
import sys

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
RESUME_TEX = os.path.join(REPO_ROOT, "resume.tex")

SYSTEM_PROMPT = """\
You are an expert CV tailoring assistant. Your task is to adapt a LaTeX resume
to better match a specific job posting.

RULES — follow these strictly:

1. OUTPUT FORMAT: Return ONLY valid LaTeX code. No markdown fences, no
   commentary, no explanations — just the complete LaTeX document.

2. PRESERVE STRUCTURE: Keep the exact same LaTeX preamble, \\documentclass,
   \\usepackage declarations, custom commands (\\workentry, \\educationentry,
   \\sectionbox), layout settings, and overall document skeleton. Keep the
   \\input{private} directive exactly as-is.

3. MODIFY ONLY CONTENT — you may change text inside these sections:
   - About Me — rewrite to emphasize skills/experience matching the job posting.
   - Key Competences — reorder, adjust emphasis, promote relevant items, demote
     or remove less relevant ones. You may add technologies mentioned in the
     posting IF the candidate demonstrably has them based on work experience.
   - Work Experience — keep ALL entries but adjust project descriptions and tech
     stacks to highlight the most relevant aspects for this job.
   - Trainings — adjust if relevant to the posting.
   - Projects — reorder or adjust emphasis.

4. NEVER FABRICATE — do not invent experience, skills, projects, or job titles
   that do not exist in the original CV. You may reword and reframe existing
   content to sound more relevant, but never add fictional items.

5. KEEP THE SAME LENGTH — the tailored CV should have very similar length as
   the original resume. Do not add or remove sections. 
   Use the original resume as the reference for size.

6. LANGUAGE — write the CV content in English.
"""


def find_job_posting(company_dir):
    """Find the single .txt file inside the company directory."""
    txt_files = glob.glob(os.path.join(company_dir, "*.txt"))
    if not txt_files:
        print(f"Error: No .txt file found in {company_dir}", file=sys.stderr)
        print("Place the job posting as a .txt file in the offer folder.", file=sys.stderr)
        sys.exit(1)
    if len(txt_files) > 1:
        print(f"Warning: Multiple .txt files found, using {txt_files[0]}", file=sys.stderr)
    return txt_files[0]


def strip_markdown_fences(text):
    """Remove markdown code fences if the LLM wrapped the output."""
    text = text.strip()
    text = re.sub(r"^```(?:latex|tex)?\s*\n", "", text)
    text = re.sub(r"\n```\s*$", "", text)
    return text


def validate_latex(text):
    """Check that the output looks like a valid LaTeX document."""
    has_begin = "\\begin{document}" in text
    has_end = "\\end{document}" in text
    if not has_begin or not has_end:
        print(
            "Warning: Generated LaTeX may be invalid "
            "(missing \\begin{document} or \\end{document}). "
            "Saving anyway for manual inspection.",
            file=sys.stderr,
        )
        return False
    return True


def compile_pdf(tex_path, company_dir):
    """Compile the .tex file to PDF using pdflatex from the repo root."""
    tex_filename = os.path.basename(tex_path)
    output_dir = os.path.relpath(company_dir, REPO_ROOT)

    for pass_num in (1, 2):
        result = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                f"-output-directory={output_dir}",
                os.path.join(output_dir, tex_filename),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            log_path = os.path.join(
                company_dir,
                tex_filename.replace(".tex", ".log"),
            )
            print(f"Error: pdflatex pass {pass_num} failed.", file=sys.stderr)
            print(f"Check the log: {log_path}", file=sys.stderr)
            print(result.stdout[-2000:] if result.stdout else "", file=sys.stderr)
            return False
    return True


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <offer-folder-name>", file=sys.stderr)
        print("Example: python tailor.py google", file=sys.stderr)
        sys.exit(1)

    offer_name = sys.argv[1]
    company_dir = os.path.join(REPO_ROOT, "offers", offer_name)

    if not os.path.isdir(company_dir):
        print(f"Error: Directory not found: {company_dir}", file=sys.stderr)
        sys.exit(1)

    if not os.environ.get("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    # Read inputs
    with open(RESUME_TEX, "r", encoding="utf-8") as f:
        resume_content = f.read()

    job_posting_path = find_job_posting(company_dir)
    with open(job_posting_path, "r", encoding="utf-8") as f:
        job_posting = f.read()

    output_tex = os.path.join(company_dir, f"resume-{offer_name}.tex")

    # Call Gemini via LangChain
    print(f"Calling Gemini 3 Pro to tailor CV for '{offer_name}'...")

    llm = ChatGoogleGenerativeAI(
        model="gemini-3-pro-preview",
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    user_prompt = (
        "Below is my current LaTeX resume and a job posting. "
        "Please produce a tailored version of the resume that highlights "
        "the most relevant experience and skills for this position.\n\n"
        "=== LATEX RESUME ===\n"
        f"{resume_content}\n\n"
        "=== JOB POSTING ===\n"
        f"{job_posting}\n"
    )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ]

    response = llm.invoke(messages)
    tailored_tex = strip_markdown_fences(response.content)

    # Validate and write
    validate_latex(tailored_tex)

    with open(output_tex, "w", encoding="utf-8") as f:
        f.write(tailored_tex)

    print(f"Tailored .tex saved: {output_tex}")

    # Compile to PDF
    print("Compiling PDF...")
    if compile_pdf(output_tex, company_dir):
        pdf_path = output_tex.replace(".tex", ".pdf")
        print(f"PDF ready: {pdf_path}")
    else:
        print("PDF compilation failed. The .tex file is saved for manual inspection.")
        sys.exit(1)


if __name__ == "__main__":
    main()
