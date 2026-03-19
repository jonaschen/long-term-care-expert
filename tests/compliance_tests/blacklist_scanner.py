#!/usr/bin/env python3
"""
tests/compliance_tests/blacklist_scanner.py

Automated blacklist scanner for generated test outputs.

Scans LINE Flex Message JSON outputs (or raw text) for:
  1. Prohibited terms / patterns  (compliance/blacklist_terms.json)
  2. Whitelist coverage           (compliance/whitelist_terms.json)
  3. Disclaimer injection         (compliance/disclaimer_template.md)

Usage
-----
CLI (single file):
    python blacklist_scanner.py --scan-file report.json

CLI (directory of JSON outputs):
    python blacklist_scanner.py --scan-dir outputs/

CLI (raw text):
    python blacklist_scanner.py --scan-text "The sensor noticed slower gait"

Options:
    --json-output   Machine-readable JSON output (default: human-readable)
    --strict        Exit 1 even for whitelist warnings (default: exit 1 only
                    for blacklist violations)

Exit codes:
    0  All scans passed
    1  At least one blacklist violation (or whitelist failure in --strict mode)

Module API
----------
    from blacklist_scanner import ComplianceScanner

    scanner = ComplianceScanner()
    result  = scanner.scan_text("some output text")
    result  = scanner.scan_flex_message(flex_msg_dict)
    results = scanner.scan_directory("outputs/")
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths (relative to project root)
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_BLACKLIST_PATH = _PROJECT_ROOT / "compliance" / "blacklist_terms.json"
_WHITELIST_PATH = _PROJECT_ROOT / "compliance" / "whitelist_terms.json"
_DISCLAIMER_PATH = _PROJECT_ROOT / "compliance" / "disclaimer_template.md"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Violation:
    """A single prohibited-term or pattern match."""

    field_name: str  # e.g. "behavior_summary", "hpa_suggestion", "raw_text"
    violation_type: str  # "prohibited_term" or "prohibited_pattern"
    matched: str  # the actual term or pattern that matched
    context: str  # surrounding text (up to 80 chars) for human review

    def to_dict(self) -> dict[str, str]:
        return {
            "field": self.field_name,
            "type": self.violation_type,
            "matched": self.matched,
            "context": self.context,
        }


@dataclass
class ScanResult:
    """Result of scanning a single piece of text or Flex Message."""

    source: str  # file path or "<text>"
    violations: list[Violation] = field(default_factory=list)
    whitelist_matches: list[str] = field(default_factory=list)
    whitelist_total: int = 0
    disclaimer_present: bool = False
    is_flex_message: bool = False

    @property
    def passed(self) -> bool:
        """True when there are zero blacklist violations."""
        return len(self.violations) == 0

    @property
    def whitelist_covered(self) -> bool:
        """True when at least one observational pattern is present."""
        return len(self.whitelist_matches) > 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "passed": self.passed,
            "violation_count": len(self.violations),
            "violations": [v.to_dict() for v in self.violations],
            "whitelist_coverage": {
                "covered": self.whitelist_covered,
                "matched_patterns": self.whitelist_matches,
                "total_patterns": self.whitelist_total,
            },
            "disclaimer_present": self.disclaimer_present,
            "is_flex_message": self.is_flex_message,
        }


@dataclass
class BatchResult:
    """Aggregated result of scanning multiple files / texts."""

    results: list[ScanResult] = field(default_factory=list)

    @property
    def total_scanned(self) -> int:
        return len(self.results)

    @property
    def total_passed(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def total_failed(self) -> int:
        return self.total_scanned - self.total_passed

    @property
    def total_violations(self) -> int:
        return sum(len(r.violations) for r in self.results)

    @property
    def whitelist_warnings(self) -> int:
        return sum(1 for r in self.results if not r.whitelist_covered)

    @property
    def disclaimer_missing(self) -> int:
        return sum(
            1 for r in self.results if r.is_flex_message and not r.disclaimer_present
        )

    @property
    def all_passed(self) -> bool:
        return self.total_failed == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": {
                "total_scanned": self.total_scanned,
                "passed": self.total_passed,
                "failed": self.total_failed,
                "total_violations": self.total_violations,
                "whitelist_warnings": self.whitelist_warnings,
                "disclaimer_missing": self.disclaimer_missing,
                "overall_result": "PASS" if self.all_passed else "FAIL",
            },
            "results": [r.to_dict() for r in self.results],
        }


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------


class ComplianceScanner:
    """Loads compliance rules once and provides scan methods."""

    def __init__(
        self,
        blacklist_path: Path | str | None = None,
        whitelist_path: Path | str | None = None,
        disclaimer_path: Path | str | None = None,
    ) -> None:
        bl_path = Path(blacklist_path) if blacklist_path else _BLACKLIST_PATH
        wl_path = Path(whitelist_path) if whitelist_path else _WHITELIST_PATH
        dl_path = Path(disclaimer_path) if disclaimer_path else _DISCLAIMER_PATH

        self._prohibited_terms, self._prohibited_patterns = self._load_blacklist(
            bl_path
        )
        self._whitelist_patterns = self._load_whitelist(wl_path)
        self._disclaimer_snippet = self._load_disclaimer_snippet(dl_path)

    # --- loaders ----------------------------------------------------------

    @staticmethod
    def _load_blacklist(path: Path) -> tuple[list[str], list[re.Pattern[str]]]:
        if not path.exists():
            return [], []
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        terms = [t.lower() for t in data.get("prohibited_terms", [])]
        patterns: list[re.Pattern[str]] = []
        for pat_str in data.get("prohibited_patterns", []):
            try:
                patterns.append(re.compile(pat_str, re.IGNORECASE))
            except re.error:
                pass
        return terms, patterns

    @staticmethod
    def _load_whitelist(path: Path) -> list[str]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return [p.lower() for p in data.get("required_patterns", [])]

    @staticmethod
    def _load_disclaimer_snippet(path: Path) -> str:
        """Extract a representative snippet from the disclaimer template
        that must appear in valid Flex Messages.  We use the Chinese opening
        marker ``【系統聲明】`` as it is injected by ``generate_line_report``.
        """
        if not path.exists():
            return "【系統聲明】"
        raw = path.read_text(encoding="utf-8")
        # The Chinese disclaimer always starts with this marker
        if "【系統聲明】" in raw:
            return "【系統聲明】"
        # Fallback to English marker
        return "Non-SaMD"

    # --- core scan logic --------------------------------------------------

    def _find_violations(
        self, text: str, field_name: str
    ) -> list[Violation]:
        """Scan *text* for prohibited terms and patterns."""
        violations: list[Violation] = []
        lower = text.lower()

        for term in self._prohibited_terms:
            idx = lower.find(term)
            if idx != -1:
                ctx_start = max(0, idx - 30)
                ctx_end = min(len(text), idx + len(term) + 30)
                context = text[ctx_start:ctx_end]
                violations.append(
                    Violation(
                        field_name=field_name,
                        violation_type="prohibited_term",
                        matched=term,
                        context=context,
                    )
                )

        for pat in self._prohibited_patterns:
            match = pat.search(text)
            if match:
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end]
                violations.append(
                    Violation(
                        field_name=field_name,
                        violation_type="prohibited_pattern",
                        matched=pat.pattern,
                        context=context,
                    )
                )

        return violations

    def _check_whitelist(self, text: str) -> list[str]:
        """Return which whitelist patterns appear in *text*."""
        lower = text.lower()
        return [p for p in self._whitelist_patterns if p in lower]

    def _check_disclaimer(self, text: str) -> bool:
        """Check whether the disclaimer snippet is present."""
        return self._disclaimer_snippet in text

    # --- public API -------------------------------------------------------

    def scan_text(self, text: str, source: str = "<text>") -> ScanResult:
        """Scan a raw text string for compliance violations.

        Parameters
        ----------
        text : str
            The text to scan.
        source : str
            Label for reporting (file path or description).

        Returns
        -------
        ScanResult
        """
        result = ScanResult(
            source=source,
            whitelist_total=len(self._whitelist_patterns),
            is_flex_message=False,
        )
        result.violations = self._find_violations(text, "raw_text")
        result.whitelist_matches = self._check_whitelist(text)
        result.disclaimer_present = self._check_disclaimer(text)
        return result

    def scan_flex_message(
        self, msg: dict[str, Any], source: str = "<flex>"
    ) -> ScanResult:
        """Scan a LINE Flex Message dict for compliance violations.

        Extracts text from known Flex Message fields (header, body, footer)
        and scans each independently.  Also checks the metadata block for
        compliance flags set by ``generate_line_report``.

        Parameters
        ----------
        msg : dict
            A LINE Flex Message as produced by ``generate_line_report_impl``.
        source : str
            Label for reporting.

        Returns
        -------
        ScanResult
        """
        result = ScanResult(
            source=source,
            whitelist_total=len(self._whitelist_patterns),
            is_flex_message=True,
        )

        # Collect all text from the Flex Message structure
        all_text_parts: list[tuple[str, str]] = []  # (field_name, text)
        contents = msg.get("contents", {})

        # Header texts
        header = contents.get("header", {})
        for item in header.get("contents", []):
            if item.get("type") == "text":
                all_text_parts.append(("header", item.get("text", "")))

        # Body texts
        body = contents.get("body", {})
        for item in body.get("contents", []):
            if item.get("type") == "text":
                text_val = item.get("text", "")
                # Determine field name by position heuristic
                if text_val.startswith("💡"):
                    all_text_parts.append(("hpa_suggestion", text_val))
                else:
                    all_text_parts.append(("behavior_summary", text_val))

        # Footer texts (disclaimer)
        footer = contents.get("footer", {})
        footer_texts: list[str] = []
        for item in footer.get("contents", []):
            if item.get("type") == "text":
                footer_texts.append(item.get("text", ""))
                all_text_parts.append(("footer_disclaimer", item.get("text", "")))

        # altText
        alt_text = msg.get("altText", "")
        if alt_text:
            all_text_parts.append(("altText", alt_text))

        # Scan each text part for blacklist violations
        for field_name, text in all_text_parts:
            result.violations.extend(self._find_violations(text, field_name))

        # Whitelist: check across all body text (header + body, not footer)
        combined_body = " ".join(
            text
            for fname, text in all_text_parts
            if fname not in ("footer_disclaimer",)
        )
        result.whitelist_matches = self._check_whitelist(combined_body)

        # Disclaimer: check footer
        combined_footer = " ".join(footer_texts)
        result.disclaimer_present = self._check_disclaimer(combined_footer)

        # Also check metadata compliance flags if present
        metadata = msg.get("metadata", {})
        compliance = metadata.get("compliance", {})
        if compliance.get("disclaimer_injected") is True:
            # Cross-validate: metadata says injected but text missing?
            if not result.disclaimer_present and footer_texts:
                # If there's footer text but no disclaimer snippet, flag it
                pass  # already False

        return result

    def scan_file(self, filepath: Path | str) -> ScanResult:
        """Scan a single JSON file containing a Flex Message or raw text.

        If the file contains valid JSON with a ``"type": "flex"`` key,
        it is treated as a Flex Message.  Otherwise it is scanned as raw text.

        Parameters
        ----------
        filepath : Path or str
            Path to the file to scan.

        Returns
        -------
        ScanResult
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        raw = path.read_text(encoding="utf-8")
        source = str(path)

        # Try JSON parse
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and data.get("type") == "flex":
                return self.scan_flex_message(data, source=source)
            # Might be a list of messages
            if isinstance(data, list):
                batch = BatchResult()
                for i, item in enumerate(data):
                    if isinstance(item, dict) and item.get("type") == "flex":
                        batch.results.append(
                            self.scan_flex_message(
                                item, source=f"{source}[{i}]"
                            )
                        )
                    else:
                        batch.results.append(
                            self.scan_text(
                                json.dumps(item, ensure_ascii=False),
                                source=f"{source}[{i}]",
                            )
                        )
                # Flatten into single result if only one
                if len(batch.results) == 1:
                    return batch.results[0]
                # For multiple messages, merge into one ScanResult
                merged = ScanResult(
                    source=source,
                    whitelist_total=len(self._whitelist_patterns),
                    is_flex_message=True,
                )
                for r in batch.results:
                    merged.violations.extend(r.violations)
                    merged.whitelist_matches.extend(r.whitelist_matches)
                    if r.disclaimer_present:
                        merged.disclaimer_present = True
                # De-duplicate whitelist matches
                merged.whitelist_matches = list(set(merged.whitelist_matches))
                return merged
        except (json.JSONDecodeError, ValueError):
            pass

        # Fall back to raw text scan
        return self.scan_text(raw, source=source)

    def scan_directory(self, dirpath: Path | str, pattern: str = "*.json") -> BatchResult:
        """Scan all matching files in a directory.

        Parameters
        ----------
        dirpath : Path or str
            Directory containing output files.
        pattern : str
            Glob pattern for files to scan (default: ``"*.json"``).

        Returns
        -------
        BatchResult
        """
        path = Path(dirpath)
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")

        batch = BatchResult()
        for filepath in sorted(path.glob(pattern)):
            if filepath.is_file():
                batch.results.append(self.scan_file(filepath))
        return batch


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _format_human(batch: BatchResult) -> str:
    """Format batch results for human-readable terminal output."""
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("  Compliance Blacklist Scanner — Results")
    lines.append("=" * 60)
    lines.append("")

    for result in batch.results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        lines.append(f"  {status}  {result.source}")

        if not result.passed:
            for v in result.violations:
                lines.append(f"    ├─ [{v.violation_type}] '{v.matched}' in {v.field_name}")
                lines.append(f"    │  context: \"{v.context}\"")

        if not result.whitelist_covered:
            lines.append(
                f"    ⚠️  No observational language found "
                f"(0/{result.whitelist_total} whitelist patterns)"
            )
        else:
            lines.append(
                f"    ✓  Whitelist: {len(result.whitelist_matches)}/{result.whitelist_total} patterns"
            )

        if result.is_flex_message and not result.disclaimer_present:
            lines.append("    ⚠️  Mandatory disclaimer NOT found in footer")

        lines.append("")

    # Summary
    lines.append("-" * 60)
    lines.append(f"  Total scanned : {batch.total_scanned}")
    lines.append(f"  Passed        : {batch.total_passed}")
    lines.append(f"  Failed        : {batch.total_failed}")
    lines.append(f"  Violations    : {batch.total_violations}")
    lines.append(f"  Whitelist warn: {batch.whitelist_warnings}")
    if any(r.is_flex_message for r in batch.results):
        lines.append(f"  Disclaimer ∅  : {batch.disclaimer_missing}")
    lines.append("-" * 60)

    overall = "✅ ALL PASSED" if batch.all_passed else "❌ VIOLATIONS FOUND"
    lines.append(f"  Overall: {overall}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Automated compliance blacklist scanner for generated outputs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--scan-file",
        type=str,
        help="Path to a single JSON output file to scan",
    )
    group.add_argument(
        "--scan-dir",
        type=str,
        help="Path to a directory of JSON output files to scan",
    )
    group.add_argument(
        "--scan-text",
        type=str,
        help="Raw text string to scan inline",
    )

    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Output results as machine-readable JSON",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 for whitelist warnings (not just blacklist violations)",
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.json",
        help="Glob pattern for --scan-dir (default: *.json)",
    )

    args = parser.parse_args()
    scanner = ComplianceScanner()
    batch = BatchResult()

    if args.scan_file:
        batch.results.append(scanner.scan_file(args.scan_file))
    elif args.scan_dir:
        batch = scanner.scan_directory(args.scan_dir, pattern=args.pattern)
    elif args.scan_text:
        batch.results.append(scanner.scan_text(args.scan_text))

    if args.json_output:
        print(json.dumps(batch.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(_format_human(batch))

    # Exit code
    if not batch.all_passed:
        return 1
    if args.strict and batch.whitelist_warnings > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
