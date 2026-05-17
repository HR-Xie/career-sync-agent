import json
import re
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = "templates/resumes"


def _is_fresh_grad(profile: dict) -> bool:
    """Detect if candidate is a fresh graduate based on education end year."""
    current_year = datetime.now().year
    edu_entries = profile.get("education", [])
    if not edu_entries:
        # No education info and no experience → likely fresh grad
        return not profile.get("experience")

    max_year = 0
    for edu in edu_entries:
        year_str = edu.get("year", "")
        years = re.findall(r"(20\d{2})", year_str)
        if years:
            max_year = max(max_year, max(int(y) for y in years))

    if max_year == 0:
        return not profile.get("experience")

    return (current_year - max_year) <= 1


def build_resume_html(profile: dict, jd_keywords: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
        auto_reload=True,
    )
    template = env.get_template("modern.html")
    return template.render(
        profile=profile,
        jd=jd_keywords,
        is_fresh_grad=_is_fresh_grad(profile),
    )


def parse_llm_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:] if len(lines) > 1 else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


def generate_tailored_prompt(profile: dict, jd_keywords: dict | None = None) -> str:
    profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
    if jd_keywords:
        from llm.prompts import RESUME_TAILORING_PROMPT
        return RESUME_TAILORING_PROMPT.format(
            jd_keywords=json.dumps(jd_keywords, ensure_ascii=False, indent=2),
            profile_json=profile_json,
        )
    else:
        from llm.prompts import RESUME_POLISH_PROMPT
        return RESUME_POLISH_PROMPT.format(profile_json=profile_json)


def generate_self_intro_prompt(tailored_resume: dict, company_info: str, jd_keywords: dict | None = None) -> str:
    from llm.prompts import INTERVIEW_SELF_INTRO_PROMPT
    jd_text = json.dumps(jd_keywords, ensure_ascii=False, indent=2) if jd_keywords else "（未提供JD，请基于候选人经历生成通用自我介绍）"
    return INTERVIEW_SELF_INTRO_PROMPT.format(
        tailored_resume=json.dumps(tailored_resume, ensure_ascii=False, indent=2),
        company_info=company_info,
        jd_keywords=jd_text,
    )


def generate_company_research_prompt(search_results: str, company_name: str, job_title: str) -> str:
    from llm.prompts import COMPANY_RESEARCH_PROMPT
    return COMPANY_RESEARCH_PROMPT.format(
        search_results=search_results,
        company_name=company_name,
        job_title=job_title,
    )
