#!/usr/bin/env python3
"""
tests/compliance_tests/test_blacklist_scanner.py

Unit tests for the automated blacklist scanner.
"""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import pytest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from blacklist_scanner import (
    BatchResult,
    ComplianceScanner,
    ScanResult,
    Violation,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def scanner() -> ComplianceScanner:
    """Scanner loaded with the real project compliance files."""
    return ComplianceScanner()


@pytest.fixture
def tmp_dir():
    """Create and clean up a temporary directory for file-based tests."""
    d = Path(tempfile.mkdtemp(prefix="scanner_test_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _make_flex_message(
    title: str = "🌙 Sleep Observation",
    summary: str = "The sensor noticed more nighttime movement than usual.",
    suggestion: str = "You might consider checking the room temperature.",
    urgency: str = "routine",
    report_type: str = "daily_insight",
    disclaimer: str = "【系統聲明】本系統並非醫療器材（Non-SaMD）。",
) -> dict:
    """Build a minimal LINE Flex Message matching generate_line_report output."""
    return {
        "type": "flex",
        "altText": title,
        "contents": {
            "type": "bubble",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": title, "weight": "bold"},
                ],
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": summary, "wrap": True},
                    {"type": "separator"},
                    {"type": "text", "text": f"💡 {suggestion}", "wrap": True},
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {"type": "text", "text": disclaimer, "wrap": True, "size": "xxs"},
                ],
            },
        },
        "metadata": {
            "urgency_level": urgency,
            "report_type": report_type,
            "compliance": {
                "blacklist_scan": "pass",
                "disclaimer_injected": True,
            },
        },
    }


# ---------------------------------------------------------------------------
# Violation dataclass
# ---------------------------------------------------------------------------


class TestViolation:
    def test_to_dict(self):
        v = Violation(
            field_name="summary",
            violation_type="prohibited_term",
            matched="diagnosis",
            context="...a diagnosis was...",
        )
        d = v.to_dict()
        assert d["field"] == "summary"
        assert d["type"] == "prohibited_term"
        assert d["matched"] == "diagnosis"


# ---------------------------------------------------------------------------
# ScanResult
# ---------------------------------------------------------------------------


class TestScanResult:
    def test_passed_when_no_violations(self):
        r = ScanResult(source="test")
        assert r.passed is True

    def test_failed_when_violations(self):
        r = ScanResult(source="test")
        r.violations.append(
            Violation("f", "prohibited_term", "treatment", "context")
        )
        assert r.passed is False

    def test_whitelist_covered(self):
        r = ScanResult(source="test")
        r.whitelist_matches = ["we observed that"]
        assert r.whitelist_covered is True

    def test_whitelist_not_covered(self):
        r = ScanResult(source="test")
        assert r.whitelist_covered is False


# ---------------------------------------------------------------------------
# BatchResult
# ---------------------------------------------------------------------------


class TestBatchResult:
    def test_empty_batch(self):
        b = BatchResult()
        assert b.total_scanned == 0
        assert b.all_passed is True

    def test_aggregation(self):
        b = BatchResult()
        r1 = ScanResult(source="a")
        r2 = ScanResult(source="b")
        r2.violations.append(
            Violation("f", "prohibited_term", "medication", "ctx")
        )
        b.results = [r1, r2]
        assert b.total_scanned == 2
        assert b.total_passed == 1
        assert b.total_failed == 1
        assert b.total_violations == 1
        assert b.all_passed is False


# ---------------------------------------------------------------------------
# Text scanning
# ---------------------------------------------------------------------------


class TestScanText:
    def test_clean_text_passes(self, scanner: ComplianceScanner):
        result = scanner.scan_text(
            "The sensor noticed that nighttime activity increased compared to the usual pattern."
        )
        assert result.passed is True
        assert len(result.violations) == 0

    def test_prohibited_term_detected(self, scanner: ComplianceScanner):
        result = scanner.scan_text("The patient was diagnosed with insomnia disorder.")
        assert result.passed is False
        terms_found = {v.matched for v in result.violations}
        assert "diagnosis" not in terms_found or "diagnosed with" in terms_found
        # At minimum, "insomnia disorder" should be caught
        assert any(
            "insomnia disorder" in v.matched or "disorder" in v.matched
            for v in result.violations
        )

    def test_multiple_violations(self, scanner: ComplianceScanner):
        result = scanner.scan_text(
            "The diagnosis suggests Alzheimer's disease. Treatment with medication is required."
        )
        assert result.passed is False
        assert len(result.violations) >= 3  # diagnosis, Alzheimer's, treatment, medication, disease

    def test_case_insensitive(self, scanner: ComplianceScanner):
        result = scanner.scan_text("DIAGNOSIS confirmed.")
        assert result.passed is False

    def test_whitelist_detection(self, scanner: ComplianceScanner):
        result = scanner.scan_text(
            "We observed that the elder's nighttime activity was higher."
        )
        assert result.whitelist_covered is True
        assert "we observed that" in result.whitelist_matches

    def test_whitelist_multiple_patterns(self, scanner: ComplianceScanner):
        result = scanner.scan_text(
            "The sensor noticed that movement increased. "
            "Compared to the usual pattern, this is new."
        )
        assert len(result.whitelist_matches) >= 2

    def test_no_whitelist_match(self, scanner: ComplianceScanner):
        result = scanner.scan_text("Sleep was poor last night.")
        assert result.whitelist_covered is False

    def test_disclaimer_in_raw_text(self, scanner: ComplianceScanner):
        result = scanner.scan_text(
            "Report content. 【系統聲明】本系統並非醫療器材。"
        )
        assert result.disclaimer_present is True

    def test_context_captured(self, scanner: ComplianceScanner):
        result = scanner.scan_text(
            "After observing the elder, the diagnosis was clear."
        )
        assert result.passed is False
        assert any("diagnosis" in v.context for v in result.violations)

    def test_prohibited_pattern_has_condition(self, scanner: ComplianceScanner):
        result = scanner.scan_text("The elder has dementia and needs care.")
        assert result.passed is False
        # Should match "has dementia" term and "has \w+" pattern
        pattern_violations = [
            v for v in result.violations if v.violation_type == "prohibited_pattern"
        ]
        assert len(pattern_violations) >= 1


# ---------------------------------------------------------------------------
# Flex Message scanning
# ---------------------------------------------------------------------------


class TestScanFlexMessage:
    def test_clean_message_passes(self, scanner: ComplianceScanner):
        msg = _make_flex_message()
        result = scanner.scan_flex_message(msg)
        assert result.passed is True
        assert result.is_flex_message is True
        assert result.disclaimer_present is True

    def test_violation_in_summary(self, scanner: ComplianceScanner):
        msg = _make_flex_message(
            summary="The elder shows symptoms of cognitive decline."
        )
        result = scanner.scan_flex_message(msg)
        assert result.passed is False
        fields_with_violations = {v.field_name for v in result.violations}
        assert "behavior_summary" in fields_with_violations

    def test_violation_in_suggestion(self, scanner: ComplianceScanner):
        msg = _make_flex_message(
            suggestion="Consider medication for sleep improvement."
        )
        result = scanner.scan_flex_message(msg)
        assert result.passed is False

    def test_violation_in_title(self, scanner: ComplianceScanner):
        msg = _make_flex_message(title="Diagnosis Alert")
        result = scanner.scan_flex_message(msg)
        assert result.passed is False

    def test_missing_disclaimer(self, scanner: ComplianceScanner):
        msg = _make_flex_message(disclaimer="Some other footer text")
        result = scanner.scan_flex_message(msg)
        assert result.disclaimer_present is False

    def test_whitelist_in_body(self, scanner: ComplianceScanner):
        msg = _make_flex_message(
            summary="The sensor noticed that nighttime movement increased."
        )
        result = scanner.scan_flex_message(msg)
        assert result.whitelist_covered is True


# ---------------------------------------------------------------------------
# File scanning
# ---------------------------------------------------------------------------


class TestScanFile:
    def test_scan_flex_json(self, scanner: ComplianceScanner, tmp_dir: Path):
        msg = _make_flex_message()
        filepath = tmp_dir / "report.json"
        filepath.write_text(json.dumps(msg, ensure_ascii=False), encoding="utf-8")

        result = scanner.scan_file(filepath)
        assert result.passed is True
        assert result.is_flex_message is True

    def test_scan_plain_text_file(self, scanner: ComplianceScanner, tmp_dir: Path):
        filepath = tmp_dir / "output.txt"
        filepath.write_text(
            "We observed that the elder had more nighttime movement.",
            encoding="utf-8",
        )
        result = scanner.scan_file(filepath)
        assert result.passed is True
        assert result.is_flex_message is False

    def test_scan_file_with_violations(self, scanner: ComplianceScanner, tmp_dir: Path):
        msg = _make_flex_message(
            summary="Treatment for the diagnosed condition is needed."
        )
        filepath = tmp_dir / "bad_report.json"
        filepath.write_text(json.dumps(msg, ensure_ascii=False), encoding="utf-8")

        result = scanner.scan_file(filepath)
        assert result.passed is False

    def test_file_not_found(self, scanner: ComplianceScanner):
        with pytest.raises(FileNotFoundError):
            scanner.scan_file("/nonexistent/path.json")

    def test_scan_json_array(self, scanner: ComplianceScanner, tmp_dir: Path):
        msgs = [_make_flex_message(), _make_flex_message()]
        filepath = tmp_dir / "batch.json"
        filepath.write_text(json.dumps(msgs, ensure_ascii=False), encoding="utf-8")

        result = scanner.scan_file(filepath)
        # Should handle array of messages
        assert result.passed is True


# ---------------------------------------------------------------------------
# Directory scanning
# ---------------------------------------------------------------------------


class TestScanDirectory:
    def test_scan_empty_dir(self, scanner: ComplianceScanner, tmp_dir: Path):
        batch = scanner.scan_directory(tmp_dir)
        assert batch.total_scanned == 0
        assert batch.all_passed is True

    def test_scan_dir_with_mixed_results(
        self, scanner: ComplianceScanner, tmp_dir: Path
    ):
        # Good report
        good = _make_flex_message()
        (tmp_dir / "good.json").write_text(
            json.dumps(good, ensure_ascii=False), encoding="utf-8"
        )

        # Bad report
        bad = _make_flex_message(
            summary="The diagnosis confirms Alzheimer's disease."
        )
        (tmp_dir / "bad.json").write_text(
            json.dumps(bad, ensure_ascii=False), encoding="utf-8"
        )

        batch = scanner.scan_directory(tmp_dir)
        assert batch.total_scanned == 2
        assert batch.total_passed == 1
        assert batch.total_failed == 1
        assert not batch.all_passed

    def test_not_a_directory(self, scanner: ComplianceScanner, tmp_dir: Path):
        filepath = tmp_dir / "file.json"
        filepath.write_text("{}", encoding="utf-8")
        with pytest.raises(NotADirectoryError):
            scanner.scan_directory(filepath)

    def test_custom_glob_pattern(self, scanner: ComplianceScanner, tmp_dir: Path):
        # Create .txt and .json files
        (tmp_dir / "report.json").write_text(
            json.dumps(_make_flex_message(), ensure_ascii=False), encoding="utf-8"
        )
        (tmp_dir / "notes.txt").write_text("Clean text", encoding="utf-8")

        batch_json = scanner.scan_directory(tmp_dir, pattern="*.json")
        assert batch_json.total_scanned == 1

        batch_all = scanner.scan_directory(tmp_dir, pattern="*.*")
        assert batch_all.total_scanned == 2


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


class TestOutputFormatting:
    def test_batch_to_dict(self):
        b = BatchResult()
        r = ScanResult(source="test.json", whitelist_total=14, is_flex_message=True)
        r.disclaimer_present = True
        r.whitelist_matches = ["we observed that"]
        b.results.append(r)

        d = b.to_dict()
        assert d["summary"]["overall_result"] == "PASS"
        assert d["summary"]["total_scanned"] == 1
        assert len(d["results"]) == 1
        assert d["results"][0]["whitelist_coverage"]["covered"] is True

    def test_failed_batch_to_dict(self):
        b = BatchResult()
        r = ScanResult(source="bad.json")
        r.violations.append(
            Violation("summary", "prohibited_term", "diagnosis", "...diagnosis...")
        )
        b.results.append(r)

        d = b.to_dict()
        assert d["summary"]["overall_result"] == "FAIL"
        assert d["summary"]["total_violations"] == 1


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_string(self, scanner: ComplianceScanner):
        result = scanner.scan_text("")
        assert result.passed is True
        assert result.whitelist_covered is False

    def test_unicode_chinese_text(self, scanner: ComplianceScanner):
        result = scanner.scan_text(
            "感測器觀察到長輩近幾天的夜間活動比平時頻繁。"
        )
        assert result.passed is True

    def test_mixed_language(self, scanner: ComplianceScanner):
        result = scanner.scan_text(
            "We observed that 長輩最近的活動量有些變化。"
        )
        assert result.passed is True
        assert result.whitelist_covered is True

    def test_partial_term_no_false_positive(self, scanner: ComplianceScanner):
        # "treat" is prohibited, so "treated" should match too
        result = scanner.scan_text("The elder was treated warmly.")
        # "treated" contains "treat" so this WILL be caught
        assert result.passed is False

    def test_malformed_flex_message(self, scanner: ComplianceScanner):
        # Missing expected structure but has type: flex
        msg = {"type": "flex", "altText": "Test"}
        result = scanner.scan_flex_message(msg)
        # Should not crash
        assert isinstance(result, ScanResult)

    def test_whitelist_total_correct(self, scanner: ComplianceScanner):
        result = scanner.scan_text("anything")
        assert result.whitelist_total == 14  # 14 patterns in whitelist file
