import pytest
from services.generator import build_resume_html


SAMPLE_PROFILE = {
    "name": "张三",
    "email": "zhangsan@example.com",
    "phone": "13800000000",
    "education": [{"school": "清华大学", "degree": "硕士", "major": "计算机科学", "year": "2023-2026"}],
    "skills": ["Python", "PyTorch", "OpenCV", "Docker"],
    "experience": [
        {
            "company": "某科技公司",
            "role": "算法实习生",
            "duration": "2025.06-2025.12",
            "highlights": ["优化模型推理速度30%", "参与目标检测项目"],
        }
    ],
    "projects": [
        {
            "name": "SEAD-YOLO",
            "desc": "水下目标检测算法研究",
            "tech_stack": ["Python", "PyTorch", "YOLO"],
            "achievements": ["mAP提升5个百分点"],
        }
    ],
    "papers": [],
}

SAMPLE_JD = {
    "title": "算法工程师",
    "skills": ["Python", "PyTorch", "目标检测", "模型部署"],
    "biz_focus": "自动驾驶感知",
    "must_have": ["Python", "深度学习"],
    "nice_to_have": ["TensorRT", "模型量化"],
}


def test_build_resume_html_contains_name():
    html = build_resume_html(SAMPLE_PROFILE, SAMPLE_JD)
    assert "张三" in html


def test_build_resume_html_is_valid_html():
    html = build_resume_html(SAMPLE_PROFILE, SAMPLE_JD)
    assert "<!DOCTYPE html>" in html
    assert "</html>" in html


def test_build_resume_html_includes_skills():
    html = build_resume_html(SAMPLE_PROFILE, SAMPLE_JD)
    assert "Python" in html
    assert "PyTorch" in html
    assert "SEAD-YOLO" in html
