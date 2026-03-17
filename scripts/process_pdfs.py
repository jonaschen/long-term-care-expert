#!/usr/bin/env python3
"""
process_pdfs.py

Uses gemini-cli to read each HPA source PDF and produce compliant, structured
knowledge chunks for the RAG knowledge base.

For each PDF:
  1. Sends the PDF to gemini-cli with a domain-specific extraction prompt
  2. Parses the JSON response
  3. Writes the output to knowledge_base/processed_chunks/<name>.md
     with full metadata (Category, Medical Content, Source, Audience,
     Update Date, Chunk ID)

Usage:
    python scripts/process_pdfs.py [--dry-run] [--file <filename>]

Options:
    --dry-run   Print prompts and output paths without calling gemini or writing files
    --file      Process only the specified filename (e.g. 失智症十大警訊.pdf)

Requirements:
    - gemini-cli must be installed and authenticated (gemini --version)
    - Run from the project root directory
"""

import argparse
import datetime
import json
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
# Blacklisted terms — any chunk containing these must not be indexed
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
# Shared extraction instructions injected into every prompt
# ---------------------------------------------------------------------------
COMPLIANCE_INSTRUCTIONS = """
CRITICAL COMPLIANCE RULES — follow these without exception:

1. NEVER use these terms (SaMD prohibited list):
   diagnose / diagnosis / treatment / disorder / disease / prescription /
   medication / sleeping pills / melatonin / Alzheimer's / Parkinson's /
   cognitive impairment / cognitive decline / BPSD / sarcopenia / osteoporosis /
   rehabilitation / clinical / symptoms (as medical term)

2. ALWAYS use observational language:
   "the elder seems to..." / "compared to the usual pattern..." /
   "behavioral pattern has changed..." / "you might consider..." /
   "if this continues, accompanying the elder to a professional would be helpful"

3. Every suggestion must be LIFESTYLE or ENVIRONMENTAL — never medical.

4. Output must be in ENGLISH.
"""

# ---------------------------------------------------------------------------
# Document manifest
# Each entry defines:
#   filename      — PDF filename in raw_documents/
#   chunk_id      — unique ID for the output chunk
#   output_file   — output filename in processed_chunks/
#   category      — one of the 5 RAG categories
#   audience      — family_caregiver | internal_reasoning_only
#   source_label  — human-readable source attribution
#   prompt        — domain-specific extraction instruction
# ---------------------------------------------------------------------------
DOCUMENTS = [
    {
        "filename": "長者防跌妙招手冊.pdf",
        "chunk_id": "fall_prevention_002",
        "output_file": "fall_prevention_tips_hpa.md",
        "category": "fall_prevention",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 長者防跌妙招手冊",
        "prompt": f"""
You are reading the Taiwan Health Promotion Administration (HPA) elder fall prevention handbook.

Extract practical, family-friendly content about:
- Home environment modifications to prevent falls (lighting, rugs, grab bars, bathroom safety)
- Exercise and daily habits that reduce fall risk
- Footwear and clothing guidance
- What to do when helping an elder who has difficulty rising or moving

{COMPLIANCE_INSTRUCTIONS}

Format your output as structured Markdown with clear section headers (##).
Each section should contain 3-6 concrete, immediately actionable bullet points.
Aim for 300-500 words of useful content. Do not summarize — extract the actual guidance.
""",
    },
    {
        "filename": "老人防跌工作手冊.pdf",
        "chunk_id": "fall_prevention_003",
        "output_file": "fall_prevention_professional_hpa.md",
        "category": "fall_prevention",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 老人防跌工作手冊",
        "timeout": 360,
        "prompt": f"""
You are reading the Taiwan HPA professional elder fall prevention handbook (老人防跌工作手冊),
which is aimed at care workers and family caregivers.

Extract content about:
- Environmental assessment checklist for fall risk in the home
- Mobility assessment indicators caregivers can observe (gait speed, rising difficulty)
- Home modification priority items
- Caregiver guidance for supporting elders with fall risk

{COMPLIANCE_INSTRUCTIONS}

Format as structured Markdown with ## section headers and bullet points.
Aim for 400-600 words. Extract actual guidance — do not summarize.
""",
    },
    {
        "filename": "失智症衛教及資源手冊.pdf",
        "chunk_id": "dementia_care_005",
        "output_file": "dementia_education_hpa.md",
        "category": "dementia_care",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 失智症衛教及資源手冊",
        "prompt": f"""
You are reading the Taiwan HPA dementia health education and resource handbook.

Extract content about:
- Creating a dementia-friendly home environment (familiar objects, clear labels, lighting)
- Daily routine strategies that help maintain orientation and reduce anxiety
- Communication techniques for family caregivers (tone, pace, simplicity)
- Activity suggestions that support engagement and wellbeing
- Community and family support resources in Taiwan

{COMPLIANCE_INSTRUCTIONS}

Format as structured Markdown with ## section headers and bullet points.
Aim for 400-600 words of practical, family-usable guidance.
""",
    },
    {
        "filename": "失智症十大警訊.pdf",
        "chunk_id": "dementia_care_006",
        "output_file": "dementia_ten_signs_full_hpa.md",
        "category": "dementia_care",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 失智症十大警訊",
        "prompt": f"""
You are reading the Taiwan HPA "10 Warning Signs" dementia education trifold.

Extract all 10 behavioral change signs described in this document.
For each sign:
- Reframe it as a family observation (what a family member might notice at home)
- Give one concrete daily-life example
- Keep language warm and non-alarming

{COMPLIANCE_INSTRUCTIONS}

Format as a numbered list with a brief heading and 2-3 sentence description for each sign.
End with a short "What Families Can Do" section (3-4 bullet points of supportive action).
""",
    },
    {
        "filename": "失智症照顧者使用手冊.pdf",
        "chunk_id": "dementia_care_007",
        "output_file": "dementia_caregiver_handbook_hpa.md",
        "category": "dementia_care",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 失智症照顧者使用手冊",
        "timeout": 300,
        "prompt": f"""
You are reading the Taiwan HPA dementia caregiver handbook.

Extract content about:
- Day-to-day caregiving strategies (routines, communication, activity support)
- How to respond to common behavioral changes (wandering, repetition, nighttime restlessness)
- Caregiver wellbeing and preventing burnout
- Practical home environment tips from a caregiver perspective

{COMPLIANCE_INSTRUCTIONS}

Format as structured Markdown with ## section headers and bullet points.
Aim for 500-700 words. Focus on what a family caregiver can actually do at home.
""",
    },
    {
        "filename": "健康老化手冊_睡眠篇.pdf",
        "chunk_id": "sleep_hygiene_002",
        "output_file": "sleep_hygiene_full_hpa.md",
        "category": "sleep_hygiene",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 健康老化手冊 睡眠篇",
        "prompt": f"""
You are reading the Taiwan HPA Healthy Aging handbook, sleep chapter.

Extract content about:
- Sleep hygiene habits for older adults (consistent schedule, bedroom environment)
- How aging affects sleep patterns (what is normal vs. worth noticing)
- Environmental adjustments that improve sleep quality and nighttime safety
- Daytime habits that support better nighttime sleep (activity, sunlight, diet)
- Safe nighttime movement (lighting, pathways, preventing falls when rising at night)

{COMPLIANCE_INSTRUCTIONS}

Format as structured Markdown with ## section headers and bullet points.
Aim for 400-600 words of practical, actionable guidance for family caregivers.
""",
    },
    {
        "filename": "動動生活手冊_Active_Living.pdf",
        "chunk_id": "chronic_disease_lifestyle_003",
        "output_file": "active_living_full_hpa.md",
        "category": "chronic_disease_lifestyle",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 動動生活手冊",
        "prompt": f"""
You are reading the Taiwan HPA Active Living handbook (動動生活手冊).

Extract the specific exercises and daily movement activities described, including:
- Named exercises with brief descriptions (what body part, how to do it, how long/often)
- Household activities that count as physical activity and their intensity level
- Safety tips for exercising (what to watch for, when to stop)
- Recommended weekly activity targets for older adults

{COMPLIANCE_INSTRUCTIONS}

Format as structured Markdown with ## section headers.
For each exercise or activity, include: name, description, duration/frequency, benefit.
Aim for 400-600 words.
""",
    },
    {
        "filename": "全民身體活動指引-0110.pdf",
        "chunk_id": "chronic_disease_lifestyle_004",
        "output_file": "physical_activity_guidelines_hpa.md",
        "category": "chronic_disease_lifestyle",
        "audience": "family_caregiver",
        "source_label": "Taiwan HPA — 全民身體活動指引",
        "timeout": 300,
        "prompt": f"""
You are reading Taiwan's National Physical Activity Guidelines (全民身體活動指引).

Extract the sections relevant to older adults (65+), including:
- Recommended types, frequency, and duration of physical activity for older adults
- Light, moderate, and vigorous activity examples appropriate for the elderly
- Guidelines for older adults with limited mobility
- Benefits of regular physical activity described in the document
- Safety precautions mentioned

{COMPLIANCE_INSTRUCTIONS}

Format as structured Markdown with ## section headers and bullet points.
Aim for 400-600 words focused on the elderly-specific sections.
""",
    },
    {
        "filename": "AD-8極早期失智症篩檢量表.pdf",
        "chunk_id": "dementia_care_008",
        "output_file": "ad8_behavioral_domains_full.md",
        "category": "dementia_care",
        "audience": "internal_reasoning_only",
        "source_label": "AD-8 Early Detection Interview — Taiwan Version (Knight ADRC / Washington University)",
        "prompt": f"""
You are reading the AD-8 dementia screening instrument, Taiwan version.

This content is for INTERNAL REASONING ONLY — it will never be shown to family caregivers.

Extract the 8 behavioral domains assessed by this instrument.
For each domain:
- Describe what behavioral change it is asking about
- Give 2-3 examples of what this change might look like in daily home life
- Frame it as an observation a family member might make at home (not a clinical question)

Do NOT include:
- Scoring instructions or cutoff scores
- Any reference to this being a screening or diagnostic tool
- Any clinical or diagnostic framing

{COMPLIANCE_INSTRUCTIONS}

Format as a numbered list with ## heading for each domain.
This chunk is used only to help the dementia-behavior-expert skill understand
which behavioral patterns are worth gentle observation — not to diagnose.
""",
    },
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def run_gemini(pdf_path: Path, prompt: str, timeout: int = 120) -> str:
    """
    Call gemini-cli with a PDF file reference and prompt.
    Returns the response text, or raises RuntimeError on failure.
    """
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

    # Parse JSON output
    raw = result.stdout.strip()
    # Strip leading log lines (e.g. "Loaded cached credentials.")
    lines = raw.splitlines()
    json_start = next((i for i, l in enumerate(lines) if l.strip().startswith("{")), None)
    if json_start is None:
        raise RuntimeError(f"No JSON found in gemini output: {raw[:300]}")
    json_text = "\n".join(lines[json_start:])

    data = json.loads(json_text)
    return data["response"]


def check_blacklist(text: str) -> list[str]:
    """Return any blacklisted terms found in the text (case-insensitive)."""
    text_lower = text.lower()
    return [term for term in BLACKLIST if term.lower() in text_lower]


def build_chunk(doc: dict, content: str) -> str:
    """Wrap extracted content with the required metadata header."""
    internal_warning = ""
    if doc["audience"] == "internal_reasoning_only":
        internal_warning = (
            "\n⚠ INTERNAL USE ONLY — DO NOT SURFACE IN FAMILY-FACING OUTPUT ⚠\n"
            "This chunk is an internal reasoning reference only. It must never appear\n"
            "in any report sent to families and must never be used as a scoring instrument.\n"
        )

    header = f"""# {Path(doc["output_file"]).stem.replace("_", " ").title()}
Category: {doc["category"]}
Medical Content: false
Source: {doc["source_label"]}
Audience: {doc["audience"]}
Update Date: {TODAY}
Chunk ID: {doc["chunk_id"]}
{internal_warning}
"""
    return header + content.strip() + "\n"


def process_document(doc: dict, dry_run: bool = False) -> bool:
    """
    Process a single document. Returns True on success.
    """
    pdf_path = RAW_DIR / doc["filename"]
    output_path = CHUNKS_DIR / doc["output_file"]

    print(f"\n{'─' * 60}")
    print(f"  {doc['filename']}")
    print(f"  → {doc['output_file']}  [{doc['chunk_id']}]")

    if not pdf_path.exists():
        print(f"  ✗  PDF not found: {pdf_path}")
        return False

    if dry_run:
        print(f"  [dry-run] Would call gemini with {len(doc['prompt'])} char prompt")
        print(f"  [dry-run] Would write to {output_path}")
        return True

    timeout = doc.get("timeout", 120)
    print(f"  Calling gemini-cli (timeout={timeout}s)...")
    try:
        response = run_gemini(pdf_path, doc["prompt"], timeout=timeout)
    except Exception as exc:
        print(f"  ✗  gemini-cli failed: {exc}")
        return False

    # Compliance scan
    violations = check_blacklist(response)
    if violations:
        print(f"  ⚠  Blacklisted terms found: {violations}")
        print(f"     Saving to {output_path}.REVIEW — manual review required before indexing")
        output_path = Path(str(output_path) + ".REVIEW")
    else:
        print(f"  ✓  Compliance scan passed")

    chunk = build_chunk(doc, response)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(chunk, encoding="utf-8")

    word_count = len(response.split())
    print(f"  ✓  Written ({word_count} words) → {output_path.name}")
    return not bool(violations)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Process HPA PDFs with gemini-cli into knowledge chunks.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would happen without calling gemini")
    parser.add_argument("--file", metavar="FILENAME", help="Process only this PDF filename")
    args = parser.parse_args()

    docs = DOCUMENTS
    if args.file:
        docs = [d for d in DOCUMENTS if d["filename"] == args.file]
        if not docs:
            print(f"Error: no document configured for '{args.file}'")
            print(f"Available: {[d['filename'] for d in DOCUMENTS]}")
            return 1

    print("=" * 60)
    print("  HPA Knowledge Base — PDF Processing via gemini-cli")
    print("=" * 60)
    print(f"  Documents to process: {len(docs)}")
    if args.dry_run:
        print("  Mode: DRY RUN")

    results = {"success": [], "failed": [], "review": []}

    for doc in docs:
        ok = process_document(doc, dry_run=args.dry_run)
        output_path = CHUNKS_DIR / doc["output_file"]
        review_path = Path(str(output_path) + ".REVIEW")
        if args.dry_run or ok:
            results["success"].append(doc["filename"])
        elif review_path.exists():
            results["review"].append(doc["filename"])
        else:
            results["failed"].append(doc["filename"])

    print(f"\n{'═' * 60}")
    print("  SUMMARY")
    print(f"{'═' * 60}")
    for f in results["success"]:
        print(f"  ✓  {f}")
    for f in results["review"]:
        print(f"  ⚠  {f}  (saved as .REVIEW — compliance check required)")
    for f in results["failed"]:
        print(f"  ✗  {f}")

    if results["review"]:
        print(
            "\n  Files marked .REVIEW contain blacklisted terms."
            "\n  Edit them to remove prohibited language before renaming to .md and indexing."
        )

    if results["failed"]:
        return 1

    if not args.dry_run and results["success"]:
        print(
            "\n  Next steps:"
            "\n    1. Review generated chunks in knowledge_base/processed_chunks/"
            "\n    2. Run compliance scan:"
            '\n       grep -rni "sarcopenia|medication|sleeping pill|diagnos|disorder" knowledge_base/processed_chunks/'
            "\n    3. Build vector index once chunks are verified"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
