#!/usr/bin/env python3
"""
scripts/expand_chunks.py

Second-pass PDF extraction for Phase 1 chunk expansion.

process_pdfs.py extracts one summary chunk per document (18 total).
This script extracts 10-20 section-level chunks per document, targeting
the ≥ 500 chunk count required for Phase 1 acceptance.

For each PDF, one gemini-cli call returns a JSON array of sections.
Each section is written as its own .md file in processed_chunks/.
Compliance blacklist runs on each individual section.

Usage:
    python scripts/expand_chunks.py [--dry-run] [--file <filename>]

Options:
    --dry-run   Print prompts and output paths without calling gemini
    --file      Process only the specified PDF filename
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "knowledge_base" / "raw_documents"
CHUNKS_DIR = REPO_ROOT / "knowledge_base" / "processed_chunks"
TODAY = datetime.date.today().isoformat()

# ---------------------------------------------------------------------------
# Blacklist — same as process_pdfs.py
# ---------------------------------------------------------------------------
BLACKLIST = [
    "diagnos", "diagnosis", "diagnosed",
    "treatment", "treated", "treatment plan",
    "disorder", "syndrome", "disease",
    "medical condition", "chronic condition",
    "prescription", "prescribe", "medication",
    "sleeping pills", "melatonin",
    "alzheimer", "parkinson",
    "cognitive impairment", "cognitive decline",
    "rehabilitation", "clinical",
    "sarcopenia", "osteoporosis",
    "BPSD",
]

# ---------------------------------------------------------------------------
# Shared compliance rules injected into every prompt
# ---------------------------------------------------------------------------
COMPLIANCE = """
CRITICAL COMPLIANCE RULES — apply to EVERY section without exception:
1. NEVER use: diagnose / diagnosis / treatment / disorder / disease /
   prescription / medication / sleeping pills / melatonin / Alzheimer's /
   Parkinson's / cognitive impairment / cognitive decline / BPSD /
   sarcopenia / osteoporosis / rehabilitation / clinical
2. ALWAYS use observational language:
   "the elder seems to..." / "compared to the usual pattern..." /
   "you might consider..." / "if this continues, consult a professional"
3. Every suggestion must be LIFESTYLE or ENVIRONMENTAL — never medical.
4. Output must be in ENGLISH.
"""


def output_format(base_id: str) -> str:
    return (
        "\nOUTPUT FORMAT — return a valid JSON array ONLY. "
        "No markdown fences, no preamble, no trailing text.\n"
        "IMPORTANT: within the content string value, never use double-quote (\") characters. "
        "Use single-quote (') for any emphasis or quotation inside content.\n"
        "Each element:\n"
        "{\n"
        f'  "chunk_id": "{base_id}_s<two-digit-number>",\n'
        '  "section_title": "Short descriptive title",\n'
        '  "content": "## Section Title\\n\\n[Markdown content, 150-350 words, use single-quotes for emphasis]"\n'
        "}\n"
    )


# ---------------------------------------------------------------------------
# Document manifest
# ---------------------------------------------------------------------------
DOCUMENTS = [
    {
        "filename": "長者防跌妙招手冊.pdf",
        "base_id": "fall_tips",
        "category": "fall_prevention",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 長者防跌妙招手冊",
        "target_sections": "10-14",
        "timeout": 200,
        "topics": (
            "Bathroom Safety, Bedroom Safety, Living Room Safety, Kitchen Safety, "
            "Outdoor Walking Safety, Lighting Improvements, Footwear and Clothing, "
            "Grab Bars and Handrails, Exercise for Fall Prevention, "
            "Rising Safely from Chairs and Beds, Nighttime Safety, When to Ask for Help"
        ),
    },
    {
        "filename": "老人防跌工作手冊.pdf",
        "base_id": "fall_pro",
        "category": "fall_prevention",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 老人防跌工作手冊",
        "target_sections": "15-20",
        "timeout": 420,
        "topics": (
            "Home Environmental Assessment, Bathroom Hazard Checklist, Bedroom Hazard Checklist, "
            "Kitchen and Stairs Safety, Outdoor Hazard Checklist, Observing Gait and Balance, "
            "Observing Rising Difficulty, Assistive Device Guidance, Priority Home Modifications, "
            "Exercise Programs for Fall Prevention, Supporting the Elder During Movement, "
            "Footwear Assessment, Caregiver Communication Techniques, Increasing Supervision Safely, "
            "Vision and Lighting Considerations, When to Seek Professional Advice"
        ),
    },
    {
        "filename": "失智症衛教及資源手冊.pdf",
        "base_id": "dementia_edu",
        "category": "dementia_care",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 失智症衛教及資源手冊",
        "target_sections": "12-16",
        "timeout": 220,
        "topics": (
            "Creating a Dementia-Friendly Home Environment, Familiar Objects and Clear Labels, "
            "Lighting and Spatial Orientation, Establishing Daily Routines, "
            "Communication Techniques for Families, Responding to Repetitive Questions, "
            "Managing Nighttime Restlessness, Safe Wandering Prevention, "
            "Activity Suggestions for Engagement and Wellbeing, Mealtime Support, "
            "Personal Care Assistance, Caregiver Wellbeing and Preventing Burnout, "
            "Community Support Resources in Taiwan, Long-Distance Family Caregiving Tips"
        ),
    },
    {
        "filename": "失智症十大警訊.pdf",
        "base_id": "dementia_signs",
        "category": "dementia_care",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 失智症十大警訊",
        "target_sections": "10-12",
        "timeout": 120,
        "topics": (
            "One section per behavioral change sign (10 signs total), reframed as a family "
            "observation with a concrete daily-life example and one gentle supportive action. "
            "Plus: What Families Can Do, How to Support Without Creating Anxiety"
        ),
    },
    {
        "filename": "失智症照顧者使用手冊.pdf",
        "base_id": "dementia_care",
        "category": "dementia_care",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 失智症照顧者使用手冊",
        "target_sections": "15-20",
        "timeout": 340,
        "topics": (
            "Building a Safe Home Environment, Managing Daily Routines, Morning and Evening Routines, "
            "Mealtime Strategies, Personal Hygiene Assistance, Responding to Wandering, "
            "Responding to Repetitive Behaviors, Managing Nighttime Restlessness, "
            "Outdoor Safety and Supervision, Communication Approaches, "
            "Handling Agitation and Emotional Distress, Activity Engagement (music, reminiscence), "
            "Caregiver Respite and Self-Care, Talking with Other Family Members, "
            "Community Day Center Resources, When to Seek Additional Support"
        ),
    },
    {
        "filename": "健康老化手冊_睡眠篇.pdf",
        "base_id": "sleep",
        "category": "sleep_hygiene",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 健康老化手冊 睡眠篇",
        "target_sections": "10-14",
        "timeout": 280,
        "topics": (
            "How Aging Affects Sleep (what is normal vs. worth noticing), "
            "Consistent Sleep Schedule, Bedroom Environment (temperature, light, noise), "
            "Reducing Fluid Intake Before Bed, Daytime Habits That Improve Sleep (sunlight, activity), "
            "Avoiding Stimulants in the Evening, Relaxation Routines Before Bedtime, "
            "Safe Nighttime Movement (lighting, pathways), Nocturia Management, "
            "What Families Can Observe About Sleep Patterns, "
            "When to Accompany Elder for a Professional Conversation"
        ),
    },
    {
        "filename": "動動生活手冊_Active_Living.pdf",
        "base_id": "active_living",
        "category": "chronic_disease_lifestyle",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 動動生活手冊",
        "target_sections": "12-16",
        "timeout": 180,
        "topics": (
            "Warm-Up Exercises, Neck and Shoulder Stretches, Upper Body Strengthening, "
            "Core and Balance Exercises, Leg Strengthening, Seated Exercises for Limited Mobility, "
            "Walking for Health (pace, duration, footwear), Household Activities That Count as Exercise, "
            "Chair-Based Exercises, Cool-Down Stretches, Weekly Activity Goals for Older Adults, "
            "Exercising Safely (when to stop, warning signs), Group Exercise Benefits, "
            "Outdoor Activity Safety"
        ),
    },
    {
        "filename": "全民身體活動指引-0110.pdf",
        "base_id": "activity_guidelines",
        "category": "chronic_disease_lifestyle",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 全民身體活動指引",
        "target_sections": "10-14",
        "timeout": 340,
        "topics": (
            "Why Physical Activity Matters for Older Adults, Weekly Activity Targets for 65+, "
            "Light Activity Examples (walking, household tasks), Moderate Activity Examples, "
            "Activity for Elders with Limited Mobility (seated, supported), "
            "Balance and Fall Prevention Activities, Muscle Strengthening Recommendations, "
            "Reducing Sedentary Time, Getting Started Safely, "
            "Activity Monitoring (how to gauge effort level), "
            "Benefits of Regular Activity for Healthy Aging, Encouraging an Elder to Stay Active"
        ),
    },
    # --- general_aging pass: re-extract cross-cutting content from existing PDFs ---
    # These entries target the general_aging category specifically.
    # The same PDFs already have domain-specific chunks; these pulls focus on
    # healthy aging themes (independence, social wellbeing, caregiver support,
    # normal aging changes, knowing when to seek professional advice).
    {
        "filename": "動動生活手冊_Active_Living.pdf",
        "base_id": "general_aging_active",
        "category": "general_aging",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 動動生活手冊",
        "target_sections": "8-10",
        "timeout": 180,
        "topics": (
            "Benefits of Staying Active for Overall Wellbeing in Later Life, "
            "How Activity Supports Independence and Daily Function, "
            "Encouraging an Elder to Stay Engaged and Motivated, "
            "Social Benefits of Group Activities and Community Participation, "
            "Adapting Activities as the Elder's Abilities Change, "
            "Supporting Emotional Wellbeing Through Movement and Routine, "
            "When Families Should Accompany an Elder for a Professional Conversation, "
            "How Families Can Gently Monitor Changes in Energy and Engagement"
        ),
    },
    {
        "filename": "全民身體活動指引-0110.pdf",
        "base_id": "general_aging_guidelines",
        "category": "general_aging",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 全民身體活動指引",
        "target_sections": "8-10",
        "timeout": 340,
        "topics": (
            "Normal Physical Changes in Later Life That Families Should Understand, "
            "How to Help an Elder Maintain Independence in Daily Activities, "
            "Nutrition and Meal Habits That Support Healthy Aging (lifestyle focus only), "
            "Reducing Sedentary Time Throughout the Day, "
            "Emotional and Social Aspects of Healthy Aging, "
            "How Families Can Support Without Over-Assisting, "
            "Signs That an Elder's Needs Are Changing — When to Gently Seek Advice, "
            "Supporting an Elder's Sense of Purpose and Daily Meaning"
        ),
    },
    {
        "filename": "失智症照顧者使用手冊.pdf",
        "base_id": "general_aging_caregiver",
        "category": "general_aging",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 失智症照顧者使用手冊",
        "target_sections": "8-10",
        "timeout": 340,
        "topics": (
            "Caregiver Wellbeing and Recognizing Burnout, "
            "Taking Breaks Without Guilt — Respite Planning for Families, "
            "Talking With Other Family Members About Caregiving Responsibilities, "
            "Maintaining Your Own Health While Caring for an Elder, "
            "Finding Community Support and Peer Networks for Caregivers, "
            "Managing the Emotional Weight of Watching an Elder Change, "
            "Setting Realistic Expectations and Celebrating Small Wins, "
            "How to Ask for Help — Practical First Steps for Overwhelmed Families"
        ),
    },
    {
        "filename": "AD-8極早期失智症篩檢量表.pdf",
        "base_id": "ad8",
        "category": "dementia_care",
        "audience": "internal_reasoning_only",
        "source_label": "AD-8 Early Detection Interview — Taiwan Version (Knight ADRC / Washington University)",
        "target_sections": "8-10",
        "timeout": 140,
        "topics": (
            "One section per AD-8 behavioral domain (8 domains). For each: describe what change "
            "the domain observes in plain family language, give 3-4 concrete daily-life examples, "
            "suggest one gentle way a family member might notice this without creating anxiety. "
            "Do NOT include scoring instructions, cutoff scores, or any clinical framing. "
            "Plus: How Families Can Gently Observe, Framing Observations Warmly. "
            "This content is INTERNAL REASONING ONLY — never shown to families."
        ),
    },
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def build_prompt(doc: dict) -> str:
    role = (
        "This content is for INTERNAL REASONING ONLY — it will never be shown to families."
        if doc["audience"] == "internal_reasoning_only"
        else "You are extracting practical, family-friendly guidance."
    )
    return (
        f"You are reading a Taiwan Health Promotion Administration document: {doc['source_label']}.\n"
        f"{role}\n\n"
        f"Extract {doc['target_sections']} distinct, self-contained sections. "
        f"Each section must be independently searchable and useful on its own.\n\n"
        f"Section topics to cover:\n{doc['topics']}\n"
        f"{COMPLIANCE}"
        f"{output_format(doc['base_id'])}"
    )


def run_gemini(pdf_path: Path, prompt: str, timeout: int) -> str:
    full_prompt = f"@{pdf_path} {prompt}"
    result = subprocess.run(
        ["gemini", "-p", full_prompt, "-o", "json"],
        input="",
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gemini-cli exited {result.returncode}: {result.stderr[:500]}")
    raw = result.stdout.strip()
    lines = raw.splitlines()
    json_start = next((i for i, l in enumerate(lines) if l.strip().startswith("{")), None)
    if json_start is None:
        raise RuntimeError(f"No JSON found in gemini output: {raw[:300]}")
    data = json.loads("\n".join(lines[json_start:]))
    return data["response"]


def _repair_json_quotes(text: str) -> str:
    """
    Fix unescaped double-quotes inside JSON string values.
    Gemini sometimes emits content like: "content": "...the "relay" approach..."
    which is invalid JSON. This replaces embedded double-quotes with single-quotes
    inside string values only.
    """
    # Match JSON string values and replace inner unescaped " with '
    # Strategy: find all JSON string spans and sanitize content within them.
    result = []
    i = 0
    in_string = False
    escape_next = False
    key_done = False  # track whether we're in a key vs value

    while i < len(text):
        ch = text[i]
        if escape_next:
            result.append(ch)
            escape_next = False
            i += 1
            continue
        if ch == "\\":
            result.append(ch)
            escape_next = True
            i += 1
            continue
        if ch == '"':
            if not in_string:
                in_string = True
                result.append(ch)
            else:
                # Peek: is the next non-whitespace char a structural JSON char?
                j = i + 1
                while j < len(text) and text[j] in " \t\r\n":
                    j += 1
                next_ch = text[j] if j < len(text) else ""
                if next_ch in (",", "}", "]", ":"):
                    # This is the closing quote of the string
                    in_string = False
                    result.append(ch)
                else:
                    # Embedded quote inside a string value — replace with '
                    result.append("'")
            i += 1
            continue
        result.append(ch)
        i += 1

    return "".join(result)


def parse_sections(response: str) -> list[dict]:
    """Extract JSON array from gemini response, handling markdown fences."""
    text = re.sub(r"^```(?:json)?\s*", "", response.strip())
    text = re.sub(r"\s*```$", "", text).strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON array in response: {text[:300]}")
    raw = text[start:end + 1]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Attempt repair for embedded unescaped double-quotes
        repaired = _repair_json_quotes(raw)
        return json.loads(repaired)


def check_blacklist(text: str) -> list[str]:
    text_lower = text.lower()
    return [term for term in BLACKLIST if term.lower() in text_lower]


def build_chunk_file(doc: dict, section: dict) -> str:
    internal_warning = ""
    if doc["audience"] == "internal_reasoning_only":
        internal_warning = (
            "\n⚠ INTERNAL USE ONLY — DO NOT SURFACE IN FAMILY-FACING OUTPUT ⚠\n"
            "This chunk is an internal reasoning reference only.\n"
        )
    header = (
        f"# {section['section_title']}\n"
        f"Category: {doc['category']}\n"
        f"Medical Content: false\n"
        f"Source: {doc['source_label']}\n"
        f"Audience: {doc['audience']}\n"
        f"Update Date: {TODAY}\n"
        f"Chunk ID: {section['chunk_id']}\n"
        f"{internal_warning}\n"
    )
    return header + section["content"].strip() + "\n"


def process_document(doc: dict, dry_run: bool = False) -> tuple[int, int]:
    """Returns (success_count, review_count)."""
    pdf_path = RAW_DIR / doc["filename"]

    print(f"\n{'─' * 60}")
    print(f"  {doc['filename']}")
    print(f"  base_id: {doc['base_id']}  |  target: {doc['target_sections']} sections")
    if doc["audience"] == "internal_reasoning_only":
        print("  audience: INTERNAL ONLY")

    if not pdf_path.exists():
        print(f"  ✗  PDF not found: {pdf_path}")
        return 0, 0

    if dry_run:
        print(f"  [dry-run] prompt: {len(build_prompt(doc))} chars  |  timeout: {doc['timeout']}s")
        return 0, 0

    print(f"  Calling gemini-cli (timeout={doc['timeout']}s)...")
    try:
        response = run_gemini(pdf_path, build_prompt(doc), timeout=doc["timeout"])
    except Exception as exc:
        print(f"  ✗  gemini-cli failed: {exc}")
        return 0, 0

    try:
        sections = parse_sections(response)
    except Exception as exc:
        print(f"  ✗  JSON parse failed: {exc}")
        raw_path = CHUNKS_DIR / f"{doc['base_id']}_raw_response.txt"
        raw_path.write_text(response, encoding="utf-8")
        print(f"     Raw response saved → {raw_path.name} (inspect and retry)")
        return 0, 0

    print(f"  Parsed {len(sections)} sections")

    success = review = 0
    for idx, section in enumerate(sections, start=1):
        chunk_id = section.get("chunk_id") or f"{doc['base_id']}_s{idx:02d}"
        section["chunk_id"] = chunk_id
        content = section.get("content", "")

        violations = check_blacklist(content)
        output_path = CHUNKS_DIR / f"{chunk_id}.md"

        if violations:
            output_path = CHUNKS_DIR / f"{chunk_id}.md.REVIEW"
            print(f"    ⚠  [{chunk_id}] blacklist hit: {violations}")
            review += 1
        else:
            success += 1

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(build_chunk_file(doc, section), encoding="utf-8")

    internal_tag = " [INTERNAL]" if doc["audience"] == "internal_reasoning_only" else ""
    print(f"  ✓  {success} chunks written, {review} flagged .REVIEW{internal_tag}")
    return success, review


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Expand HPA PDFs into section-level chunks for Phase 1 ≥500 target."
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate setup without calling gemini")
    parser.add_argument("--file", metavar="FILENAME",
                        help="Process only this PDF filename")
    args = parser.parse_args()

    docs = DOCUMENTS
    if args.file:
        docs = [d for d in DOCUMENTS if d["filename"] == args.file]
        if not docs:
            print(f"Error: no document configured for '{args.file}'")
            print(f"Available: {[d['filename'] for d in DOCUMENTS]}")
            return 1

    print("=" * 60)
    print("  HPA Knowledge Base — Section-Level Chunk Expansion")
    print("=" * 60)
    print(f"  Documents: {len(docs)}  |  Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"  Output:    {CHUNKS_DIR}")

    total_success = total_review = 0
    failed = []

    for doc in docs:
        s, r = process_document(doc, dry_run=args.dry_run)
        total_success += s
        total_review += r
        if not args.dry_run and s == 0 and r == 0:
            failed.append(doc["filename"])

    if not args.dry_run:
        existing_md = len(list(CHUNKS_DIR.glob("*.md")))
        existing_review = len(list(CHUNKS_DIR.glob("*.REVIEW")))
        print(f"\n{'═' * 60}")
        print("  SUMMARY")
        print(f"{'═' * 60}")
        print(f"  New chunks written:    {total_success}")
        print(f"  Flagged .REVIEW:       {total_review}")
        if failed:
            print(f"  Failed:                {failed}")
        print(f"  Total .md in chunks/:  {existing_md}")
        if existing_review:
            print(f"  Total .REVIEW:         {existing_review}  (manual review required)")
        print()
        print("  Re-index Qdrant with expanded chunks:")
        print("    python tools/embedding_pipeline.py --reset")
        if existing_review:
            print()
            print("  Review flagged chunks before re-indexing:")
            print("    ls knowledge_base/processed_chunks/*.REVIEW")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
