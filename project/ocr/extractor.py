from pathlib import Path

import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageOps
from pypdf import PdfReader

from app.utils import clean_multiline_text


class OCRService:
    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}

    def __init__(self, language="kor+eng", max_pages=3):
        self.language = language
        self.max_pages = max_pages

    def extract_text(self, file_path):
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return self._extract_from_pdf(path)
        if suffix in self.IMAGE_EXTENSIONS:
            return self._extract_from_image(path)
        raise ValueError("OCR이 지원하지 않는 파일 형식입니다.")

    def _extract_from_image(self, file_path):
        image = Image.open(file_path)
        processed_image = ImageOps.grayscale(image)
        text = pytesseract.image_to_string(processed_image, lang=self.language)
        return clean_multiline_text(text)

    def _extract_from_pdf(self, file_path):
        ocr_texts = []

        try:
            images = convert_from_path(
                file_path,
                first_page=1,
                last_page=self.max_pages,
            )
            for image in images:
                processed_image = ImageOps.grayscale(image)
                ocr_texts.append(
                    pytesseract.image_to_string(processed_image, lang=self.language)
                )
        except Exception:
            ocr_texts = []

        combined_ocr = clean_multiline_text("\n".join(ocr_texts))
        if combined_ocr:
            return combined_ocr

        try:
            reader = PdfReader(str(file_path))
            extracted = []
            for page in reader.pages[: self.max_pages]:
                extracted.append(page.extract_text() or "")
            return clean_multiline_text("\n".join(extracted))
        except Exception as exc:
            raise RuntimeError(
                "PDF OCR 처리에 실패했습니다. Tesseract와 Poppler 설치를 확인해 주세요."
            ) from exc

