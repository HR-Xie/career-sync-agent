import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from config import config

router = APIRouter()


@router.post("/api/upload")
async def upload_files(
    resume: UploadFile = File(...),
    jd_image: UploadFile = File(...),
    company_name: str = Form(""),
):
    # Validate file types
    allowed_resume = {".pdf", ".docx"}
    allowed_image = {".png", ".jpg", ".jpeg", ".webp"}

    resume_ext = Path(resume.filename).suffix.lower()
    jd_ext = Path(jd_image.filename).suffix.lower()

    if resume_ext not in allowed_resume:
        raise HTTPException(400, f"不支持的简历格式: {resume_ext}，仅支持 PDF/DOCX")
    if jd_ext not in allowed_image:
        raise HTTPException(400, f"不支持的图片格式: {jd_ext}，仅支持 PNG/JPG/WEBP")

    # Check file size
    resume_content = await resume.read()
    jd_content = await jd_image.read()
    max_bytes = config.MAX_FILE_SIZE_MB * 1024 * 1024

    if len(resume_content) > max_bytes:
        raise HTTPException(400, f"简历文件超过 {config.MAX_FILE_SIZE_MB}MB 限制")
    if len(jd_content) > max_bytes:
        raise HTTPException(400, f"JD截图超过 {config.MAX_FILE_SIZE_MB}MB 限制")

    # Save to uploads
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    upload_id = str(uuid.uuid4())[:8]
    resume_path = os.path.join(config.UPLOAD_DIR, f"{upload_id}_resume{resume_ext}")
    jd_path = os.path.join(config.UPLOAD_DIR, f"{upload_id}_jd{jd_ext}")

    with open(resume_path, "wb") as f:
        f.write(resume_content)
    with open(jd_path, "wb") as f:
        f.write(jd_content)

    return {"upload_id": upload_id, "resume_path": resume_path, "jd_path": jd_path, "company_name": company_name}
