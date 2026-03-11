import json
from datetime import date

from app.utils import parse_date_string, parse_period_bounds


class RuleEngine:
    def __init__(self, rules_path):
        with open(rules_path, "r", encoding="utf-8") as file:
            self.rules = json.load(file)

    def validate(self, parsed_data):
        errors = []
        warnings = []

        for field in self.rules.get("required_fields", []):
            if not parsed_data.get(field):
                errors.append(f"필수 항목 누락: {field}")

        issue_date_raw = parsed_data.get("issue_date", "")
        issue_date = parse_date_string(issue_date_raw)
        if not issue_date:
            errors.append("문서 발급일을 인식하지 못했습니다.")
        else:
            issue_age = (date.today() - issue_date).days
            if issue_age < 0:
                errors.append("발급일이 현재 날짜보다 미래입니다.")
            if issue_age > self.rules.get("max_issue_age_days", 90):
                errors.append("발급일이 허용 기간을 초과했습니다.")

        valid_start, valid_end = parse_period_bounds(parsed_data.get("valid_period", ""))
        if valid_start and valid_end:
            if valid_end < valid_start:
                errors.append("유효 기간의 시작일과 종료일 순서가 올바르지 않습니다.")
            absence_days = (valid_end - valid_start).days + 1
            if absence_days > self.rules.get("max_absence_days", 14):
                errors.append("결석 인정 가능 기간을 초과했습니다.")
        elif not parsed_data.get("valid_period"):
            warnings.append("유효 기간이 명확하게 추출되지 않았습니다.")

        if parsed_data.get("document_type") == "unknown":
            warnings.append("문서 유형이 자동 분류되지 않았습니다.")

        confidence = self._calculate_confidence(parsed_data, errors, warnings)
        min_confidence = self.rules.get("minimum_confidence_for_auto_approval", 0.7)
        status = "APPROVED" if not errors and confidence >= min_confidence else "REVIEW_REQUIRED"

        if errors:
            reason = " / ".join(errors)
        elif warnings and status == "REVIEW_REQUIRED":
            reason = " / ".join(warnings)
        else:
            reason = "자동 승인 기준을 충족했습니다."

        return {
            "status": status,
            "confidence": confidence,
            "reason": reason,
            "errors": errors,
            "warnings": warnings,
        }

    def _calculate_confidence(self, parsed_data, errors, warnings):
        filled_fields = 0
        for field in ["name", "organization", "issue_date", "valid_period"]:
            filled_fields += 1 if parsed_data.get(field) else 0
        if parsed_data.get("document_type") and parsed_data["document_type"] != "unknown":
            filled_fields += 1
        completeness = filled_fields / 5
        parser_confidence = float(parsed_data.get("parser_confidence", 0.3))
        score = (0.45 * completeness) + (0.55 * parser_confidence)
        score -= len(errors) * 0.18
        score -= len(warnings) * 0.07
        score = max(0.05, min(0.99, score))
        return round(score, 2)

