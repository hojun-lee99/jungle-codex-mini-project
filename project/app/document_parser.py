import json
import re

import requests

from app.utils import (
    clean_multiline_text,
    extract_date_candidates,
    normalize_whitespace,
    strip_code_fence,
)


class DocumentParser:
    DOCUMENT_TYPE_KEYWORDS = {
        "medical_certificate": ["진단서", "진료확인서", "의사소견서", "medical", "clinic", "hospital"],
        "funeral_certificate": ["장례", "부고", "사망", "funeral"],
        "competition_participation": ["대회", "참가확인", "competition", "contest", "참가증"],
        "counseling_confirmation": ["상담", "심리", "counseling", "상담확인서"],
    }

    def __init__(self, api_key="", model="gpt-4.1-mini", api_url=""):
        self.api_key = api_key
        self.model = model
        self.api_url = api_url

    def parse(self, text):
        cleaned_text = clean_multiline_text(text)
        if not cleaned_text:
            return self._finalize(
                {
                    "name": "",
                    "document_type": "unknown",
                    "organization": "",
                    "issue_date": "",
                    "valid_period": "",
                },
                source="empty",
            )

        if self.api_key:
            parsed = self._parse_with_llm(cleaned_text)
            if parsed:
                return self._finalize(parsed, source="llm")

        return self._finalize(self._parse_with_heuristics(cleaned_text), source="heuristic")

    def _parse_with_llm(self, text):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "당신은 학사 결석 증빙 문서를 구조화하는 파서입니다. "
                        "반드시 JSON 객체만 반환하세요. 키는 name, document_type, "
                        "organization, issue_date, valid_period 입니다."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "다음 OCR 텍스트를 읽고 구조화된 JSON을 반환하세요.\n\n"
                        f"{text[:5000]}"
                    ),
                },
            ],
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=45,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(strip_code_fence(content))
            return {
                "name": parsed.get("name", ""),
                "document_type": parsed.get("document_type", "unknown"),
                "organization": parsed.get("organization", ""),
                "issue_date": parsed.get("issue_date", ""),
                "valid_period": parsed.get("valid_period", ""),
            }
        except Exception:
            return None

    def _parse_with_heuristics(self, text):
        normalized = normalize_whitespace(text)
        return {
            "name": self._extract_name(text),
            "document_type": self._infer_document_type(normalized),
            "organization": self._extract_organization(text),
            "issue_date": self._extract_issue_date(text),
            "valid_period": self._extract_valid_period(text),
        }

    def _extract_name(self, text):
        patterns = [
            r"(?:성명|이름|환자명|학생명)\s*[:：]?\s*([A-Za-z가-힣 ]{2,30})",
            r"(?:본인|대상자)\s*[:：]?\s*([A-Za-z가-힣 ]{2,30})",
            r"(?:name)\s*[:：]?\s*([A-Za-z가-힣 ]{2,30})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_organization(self, text):
        patterns = [
            r"(?:발급기관|병원명|기관명|주최기관|상담기관|organization)\s*[:：]?\s*([^\n]{2,60})",
            r"([^\n]{2,60}(?:병원|의원|클리닉|센터|대학교|학교|협회|학회|재단))",
            r"([^\n]{2,60}(?:hospital|clinic|center|university|association|foundation))",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        for line in text.splitlines():
            compact = normalize_whitespace(line)
            if any(keyword in compact for keyword in ["병원", "의원", "센터", "대학교", "협회", "학회"]):
                return compact[:60]
        return ""

    def _extract_issue_date(self, text):
        labeled_patterns = [
            r"(?:발급일|발행일|작성일|issue date)\s*[:：]?\s*([^\n]+)",
        ]
        for pattern in labeled_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        candidates = extract_date_candidates(text)
        return candidates[0] if candidates else ""

    def _extract_valid_period(self, text):
        patterns = [
            r"(?:유효기간|진료기간|참가일시|참가기간|기간|valid period)\s*[:：]?\s*([^\n]+)",
            r"((?:\d{4}[./-]\d{1,2}[./-]\d{1,2}|\d{4}\s*년\s*\d{1,2}\s*월\s*\d{1,2}\s*일).{0,10}[~-].{0,10}(?:\d{4}[./-]\d{1,2}[./-]\d{1,2}|\d{4}\s*년\s*\d{1,2}\s*월\s*\d{1,2}\s*일))",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _infer_document_type(self, text):
        lowered = text.lower()
        for document_type, keywords in self.DOCUMENT_TYPE_KEYWORDS.items():
            if any(keyword.lower() in lowered for keyword in keywords):
                return document_type
        return "unknown"

    def _finalize(self, parsed, source):
        normalized = {
            "name": str(parsed.get("name", "")).strip(),
            "document_type": str(parsed.get("document_type", "unknown")).strip() or "unknown",
            "organization": str(parsed.get("organization", "")).strip(),
            "issue_date": str(parsed.get("issue_date", "")).strip(),
            "valid_period": str(parsed.get("valid_period", "")).strip(),
            "parser_source": source,
        }
        filled_fields = 0
        for field in ["name", "organization", "issue_date", "valid_period"]:
            filled_fields += 1 if normalized.get(field) else 0
        if normalized.get("document_type") and normalized["document_type"] != "unknown":
            filled_fields += 1
        base_score = 0.75 if source == "llm" else 0.45
        if source == "empty":
            base_score = 0.1
        normalized["parser_confidence"] = round(min(0.99, base_score + (filled_fields * 0.05)), 2)
        return normalized
