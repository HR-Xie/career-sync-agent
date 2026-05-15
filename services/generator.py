import json
from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = "templates/resumes"


def build_resume_html(profile: dict, jd_keywords: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("modern.html")
    return template.render(profile=profile, jd=jd_keywords)


def parse_llm_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:] if len(lines) > 1 else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


def generate_tailored_prompt(profile: dict, jd_keywords: dict) -> str:
    from llm.prompts import RESUME_TAILORING_PROMPT
    return RESUME_TAILORING_PROMPT.format(
        jd_keywords=json.dumps(jd_keywords, ensure_ascii=False, indent=2),
        profile_json=json.dumps(profile, ensure_ascii=False, indent=2),
    )


def generate_self_intro_prompt(tailored_resume: dict, company_info: str, jd_keywords: dict) -> str:
    from llm.prompts import INTERVIEW_SELF_INTRO_PROMPT
    return INTERVIEW_SELF_INTRO_PROMPT.format(
        tailored_resume=json.dumps(tailored_resume, ensure_ascii=False, indent=2),
        company_info=company_info,
        jd_keywords=json.dumps(jd_keywords, ensure_ascii=False, indent=2),
    )


def generate_company_research_prompt(search_results: str, company_name: str, job_title: str) -> str:
    from llm.prompts import COMPANY_RESEARCH_PROMPT
    return COMPANY_RESEARCH_PROMPT.format(
        search_results=search_results,
        company_name=company_name,
        job_title=job_title,
    )
