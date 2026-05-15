import pytest
from services.parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    clean_extracted_text,
    compress_image_to_base64,
    detect_file_format,
)


class TestDetectFileFormat:
    def test_detects_pdf_by_extension(self):
        assert detect_file_format("/path/to/resume.pdf") == "pdf"

    def test_detects_docx_by_extension(self):
        assert detect_file_format("/path/to/resume.docx") == "docx"

    def test_detects_pdf_by_magic_bytes(self, tmp_path):
        p = tmp_path / "test.bin"
        p.write_bytes(b"%PDF-1.4 skldjflskjdf")
        assert detect_file_format(str(p)) == "pdf"

    def test_detects_docx_by_magic_bytes(self, tmp_path):
        p = tmp_path / "test.bin"
        p.write_bytes(b"PK\x03\x04" + b"\x00" * 100)
        assert detect_file_format(str(p)) == "docx"

    def test_rejects_unknown_format(self, tmp_path):
        p = tmp_path / "test.xyz"
        p.write_bytes(b"random content here")
        with pytest.raises(ValueError, match="Unsupported file format"):
            detect_file_format(str(p))


class TestCleanText:
    def test_removes_excessive_newlines(self):
        text = "张三\n\n\n\n本科\n\n\n\n清华大学"
        cleaned = clean_extracted_text(text)
        assert "\n\n\n\n" not in cleaned

    def test_preserves_single_newlines(self):
        text = "项目经历\n水下目标检测\n负责算法开发"
        cleaned = clean_extracted_text(text)
        assert "\n" in cleaned

    def test_removes_form_feed(self):
        text = "第一页内容\f第二页内容"
        cleaned = clean_extracted_text(text)
        assert "\f" not in cleaned


class TestCompressImage:
    def test_compresses_and_returns_base64(self, tmp_path):
        from PIL import Image
        img_path = tmp_path / "test.jpg"
        img = Image.new("RGB", (1920, 1080), color="red")
        img.save(str(img_path))

        b64, content_type = compress_image_to_base64(str(img_path), max_width=800)
        assert len(b64) > 0
        assert "image" in content_type
