import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from config import config

router = APIRouter()


@router.post("/api/upload")
async def upload_files(
    resume: UploadFile = File(...),
    jd_image: UploadFile | None = File(None),
    company_name: str = Form(""),
    photo: UploadFile | None = File(None),
):
    # Validate resume
    allowed_resume = {".pdf", ".docx"}
    resume_ext = Path(resume.filename).suffix.lower()
    if resume_ext not in allowed_resume:
        raise HTTPException(400, f"不支持的简历格式: {resume_ext}，仅支持 PDF/DOCX")

    allowed_image = {".png", ".jpg", ".jpeg", ".webp"}

    if jd_image:
        jd_ext = Path(jd_image.filename).suffix.lower()
        if jd_ext not in allowed_image:
            raise HTTPException(400, f"不支持的图片格式: {jd_ext}，仅支持 PNG/JPG/WEBP")

    if photo:
        photo_ext = Path(photo.filename).suffix.lower()
        if photo_ext not in {".png", ".jpg", ".jpeg"}:
            raise HTTPException(400, f"不支持的证件照格式: {photo_ext}，仅支持 PNG/JPG")

    # Check file size
    resume_content = await resume.read()
    max_bytes = config.MAX_FILE_SIZE_MB * 1024 * 1024

    if len(resume_content) > max_bytes:
        raise HTTPException(400, f"简历文件超过 {config.MAX_FILE_SIZE_MB}MB 限制")

    jd_content = None
    if jd_image:
        jd_content = await jd_image.read()
        if len(jd_content) > max_bytes:
            raise HTTPException(400, f"JD截图超过 {config.MAX_FILE_SIZE_MB}MB 限制")

    # Save to uploads
    os.makedirs(config.UPLOAD_DIR, exist_ok=True)
    upload_id = str(uuid.uuid4())[:8]
    resume_path = os.path.join(config.UPLOAD_DIR, f"{upload_id}_resume{resume_ext}")
    jd_path = None

    with open(resume_path, "wb") as f:
        f.write(resume_content)

    if jd_image and jd_content:
        jd_ext = Path(jd_image.filename).suffix.lower()
        jd_path = os.path.join(config.UPLOAD_DIR, f"{upload_id}_jd{jd_ext}")
        with open(jd_path, "wb") as f:
            f.write(jd_content)

    photo_path = None
    if photo:
        photo_content = await photo.read()
        if len(photo_content) > 5 * 1024 * 1024:
            raise HTTPException(400, "证件照超过 5MB 限制")
        photo_path = os.path.join(config.UPLOAD_DIR, f"{upload_id}_photo{photo_ext}")
        with open(photo_path, "wb") as f:
            f.write(photo_content)

    return {
        "upload_id": upload_id,
        "resume_path": resume_path,
        "jd_path": jd_path,
        "photo_path": photo_path,
        "company_name": company_name,
    }
