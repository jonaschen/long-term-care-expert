#!/usr/bin/env python3
"""
download_hpa_docs.py

Downloads necessary HPA (Taiwan Health Promotion Administration) source documents
for the long-term-care-expert Phase 1 knowledge base.

Usage:
    pip install -r scripts/requirements.txt
    python scripts/download_hpa_docs.py

What this script does:
  1. For documents with a known direct PDF URL — downloads immediately.
  2. For HPA EBook/Detail/List pages — fetches the HTML, locates the embedded
     PDF download link, then downloads the PDF.
  3. Saves every file to knowledge_base/raw_documents/ with the canonical filename
     listed in README.md.
  4. Replaces the existing 2 KB HTML stub files (長者防跌妙招手冊.pdf,
     失智症照顧者使用手冊.pdf) with the real PDFs.
  5. The AD-8 instrument page requires a manual click-through; the script will
     open the landing page URL and print the expected download path.

After all PDFs are in place, run the OCR → semantic chunking → medical filter
pipeline described in LONGTERM_CARE_EXPERT_DEV_PLAN.md.
"""

import sys
import time
import hashlib
import re
import urllib.parse
from pathlib import Path
from typing import Optional

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print(
        "Missing dependencies. Please run:\n"
        "    pip install -r scripts/requirements.txt\n"
        "or:\n"
        "    pip install requests beautifulsoup4"
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DOCS_DIR = REPO_ROOT / "knowledge_base" / "raw_documents"

# ---------------------------------------------------------------------------
# Document manifest
#
# type values:
#   "direct"       – source_url is the actual PDF download URL
#   "ebook_page"   – HPA EBook viewer page; PDF link is extracted from the HTML
#   "detail_page"  – HPA Detail page;       PDF link is extracted from the HTML
#   "list_page"    – HPA List page;          PDF link is extracted from the HTML
#   "manual"       – requires human interaction; script prints instructions only
# ---------------------------------------------------------------------------
DOCUMENTS = [
    {
        "name": "長者防跌妙招手冊",
        "filename": "長者防跌妙招手冊.pdf",
        "type": "ebook_page",
        "source_url": "https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=1193",
        "description": "Fall Prevention for Elderly — Public Version (HPA)",
        "replaces_stub": True,
        "category": "fall_prevention",
    },
    {
        "name": "老人防跌工作手冊",
        "filename": "老人防跌工作手冊.pdf",
        "type": "ebook_page",
        "source_url": "https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=4347",
        "description": "Fall Prevention for Elderly — Professional Version (HPA)",
        "replaces_stub": False,
        "category": "fall_prevention",
    },
    {
        "name": "失智症衛教及資源手冊",
        "filename": "失智症衛教及資源手冊.pdf",
        "type": "ebook_page",
        "source_url": "https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=4381",
        "description": "Dementia Health Education and Resource Handbook (HPA)",
        "replaces_stub": False,
        "category": "dementia_care",
    },
    {
        "name": "失智症十大警訊",
        "filename": "失智症十大警訊.pdf",
        "type": "detail_page",
        "source_url": "https://www.hpa.gov.tw/Pages/Detail.aspx?nodeid=871&pid=8017",
        "description": "10 Warning Signs of Dementia — Trifold (HPA)",
        "replaces_stub": False,
        "category": "dementia_care",
    },
    {
        "name": "失智症照顧者使用手冊",
        "filename": "失智症照顧者使用手冊.pdf",
        "type": "list_page",
        "source_url": "https://www.hpa.gov.tw/Pages/List.aspx?nodeid=4381",
        "description": "Dementia Caregiver Handbook (HPA)",
        "replaces_stub": True,
        "category": "dementia_care",
    },
    {
        "name": "健康老化手冊_睡眠篇",
        "filename": "健康老化手冊_睡眠篇.pdf",
        "type": "direct",
        "source_url": (
            "https://health.hpa.gov.tw/common/Download.ashx"
            "?f=f70fe5f8-cf1f-4f89-929c-072a219d29ab.pdf"
            "&o=05.%E7%9D%A1%E7%9C%A0%E8%88%87%E7%B2%BE%E7%A5%9E%E5%81%A5%E5%BA%B7.pdf"
        ),
        "description": "Healthy Aging Manual — Sleep Chapter (HPA)",
        "replaces_stub": False,
        "category": "sleep_hygiene",
    },
    {
        "name": "動動生活手冊",
        "filename": "動動生活手冊_Active_Living.pdf",
        "type": "ebook_page",
        "source_url": "https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=1399",
        "description": "Active Living Handbook (HPA)",
        "replaces_stub": False,
        "category": "chronic_disease_lifestyle",
    },
    {
        "name": "全民身體活動指引",
        "filename": "全民身體活動指引.pdf",
        "type": "ebook_page",
        "source_url": "https://www.hpa.gov.tw/Pages/EBook.aspx?nodeid=1411",
        "description": "National Physical Activity Guidelines (HPA)",
        "replaces_stub": False,
        "category": "chronic_disease_lifestyle",
    },
    {
        "name": "AD8極早期失智症篩檢量表_台灣版",
        "filename": "AD8極早期失智症篩檢量表_台灣版.pdf",
        "type": "manual",
        "source_url": "https://knightadrc.wustl.edu/professionals-clinicians/ad8-instrument/",
        "description": (
            "AD-8 Dementia Screening Interview — Taiwan Version "
            "(Knight ADRC / Washington University)"
        ),
        "replaces_stub": False,
        "category": "dementia_care",
        "manual_note": (
            "This document requires manual download from the Knight ADRC website.\n"
            "  1. Visit: https://knightadrc.wustl.edu/professionals-clinicians/ad8-instrument/\n"
            "  2. Locate the Traditional Chinese (台灣版) PDF under 'Translations'.\n"
            "  3. Verify the licence: free for clinical/research use per Knight ADRC.\n"
            "  4. Save the file as: knowledge_base/raw_documents/AD8極早期失智症篩檢量表_台灣版.pdf\n"
            "\n"
            "IMPORTANT — internal use only:\n"
            "  The AD-8 scale is used as an INTERNAL REASONING REFERENCE for the\n"
            "  dementia-behavior-expert skill. It must NEVER appear in family-facing\n"
            "  output and must never be used as a scoring instrument in reports."
        ),
    },
]

# ---------------------------------------------------------------------------
# HTTP session with sensible defaults
# ---------------------------------------------------------------------------
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (compatible; ltc-knowledge-base-downloader/1.0; "
            "+https://github.com/jonaschen/long-term-care-expert)"
        ),
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
    }
)
REQUEST_TIMEOUT = 30  # seconds
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds between retries
MIN_PDF_SIZE_BYTES = 10_000  # anything smaller is considered a stub / error page


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get(url: str) -> requests.Response:
    """GET with retries."""
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = SESSION.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            if attempt == RETRY_ATTEMPTS:
                raise
            print(f"    [retry {attempt}/{RETRY_ATTEMPTS}] {exc}")
            time.sleep(RETRY_DELAY)


def _extract_pdf_url_from_hpa_page(page_url: str) -> Optional[str]:
    """
    Fetch an HPA web page and return the first .pdf download URL found.

    HPA pages typically expose PDFs in one of these ways:
      (a) An <a href="...pdf"> tag whose text contains 下載 / PDF / 全文
      (b) An <iframe src="..."> pointing to a PDF viewer URL that contains the
          actual PDF path as a query-string parameter
      (c) A meta-redirect or JavaScript window.location pointing to a PDF

    This function covers cases (a) and (b), which cover the vast majority of
    HPA EBook and Detail pages.
    """
    resp = _get(page_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    base = "https://www.hpa.gov.tw"

    # --- Strategy 1: direct <a href="*.pdf"> links ----------------------------
    for tag in soup.find_all("a", href=True):
        href: str = tag["href"]
        if href.lower().endswith(".pdf"):
            return href if href.startswith("http") else urllib.parse.urljoin(base, href)

    # --- Strategy 2: <iframe> whose src contains a PDF path ------------------
    for tag in soup.find_all("iframe", src=True):
        src: str = tag["src"]
        # Some viewers embed the PDF URL as a query param, e.g. ?file=...pdf
        parsed = urllib.parse.urlparse(src)
        qs = urllib.parse.parse_qs(parsed.query)
        for val_list in qs.values():
            for val in val_list:
                if val.lower().endswith(".pdf"):
                    return val if val.startswith("http") else urllib.parse.urljoin(base, val)
        # Or the iframe src itself is a PDF
        if src.lower().endswith(".pdf"):
            return src if src.startswith("http") else urllib.parse.urljoin(base, src)

    # --- Strategy 3: look for /File/Attach/ paths in all attributes ----------
    for tag in soup.find_all(True):
        for attr in ("href", "src", "data-src", "data-url"):
            val = tag.get(attr, "")
            if "/File/" in val and ".pdf" in val.lower():
                return val if val.startswith("http") else urllib.parse.urljoin(base, val)

    # --- Strategy 4: search raw HTML for HPA-specific .pdf path patterns ----
    # Restricts matches to HPA server paths (/File/, /Pages/, /common/) to avoid
    # matching unrelated CSS or JavaScript asset references that end in .pdf.
    # The first match is returned immediately — these strategies are ordered from
    # most to least specific, so if we reach strategy 4 the first HPA-path match
    # is the best available candidate.
    matches = re.findall(
        r'["\'](/(?:File|Pages|common)[^"\']*\.pdf)["\']', resp.text, re.IGNORECASE
    )
    for match in matches:
        return urllib.parse.urljoin(base, match)

    return None


def _extract_pdf_url_from_list_page(page_url: str, keyword: str = "") -> Optional[str]:
    """
    For HPA List pages, find the most relevant PDF link.
    Optionally filter by a keyword in the link text.
    """
    resp = _get(page_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    base = "https://www.hpa.gov.tw"

    candidates = []
    for tag in soup.find_all("a", href=True):
        href: str = tag["href"]
        text: str = tag.get_text(strip=True)
        if href.lower().endswith(".pdf"):
            score = 1
            if keyword and keyword in text:
                score = 2
            candidates.append((score, href if href.startswith("http") else urllib.parse.urljoin(base, href)))

    if candidates:
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    # Fallback to generic extractor
    return _extract_pdf_url_from_hpa_page(page_url)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_html_stub(path: Path) -> bool:
    """Return True if the file is an HTML error page masquerading as a PDF."""
    if not path.exists():
        return False
    with open(path, "rb") as f:
        header = f.read(512)
    return b"<!DOCTYPE" in header or b"<html" in header


# ---------------------------------------------------------------------------
# Core download logic
# ---------------------------------------------------------------------------

def download_document(doc: dict) -> dict:
    """
    Download a single document.

    Returns a result dict with keys: name, filename, status, message, size_kb.
    """
    name = doc["name"]
    filename = doc["filename"]
    dest = RAW_DOCS_DIR / filename
    doc_type = doc["type"]

    print(f"\n{'─' * 60}")
    print(f"  {name}")
    print(f"  {doc['description']}")
    print(f"  → {dest.name}")

    # Handle manual-download documents
    if doc_type == "manual":
        print(f"\n  ⚠  MANUAL DOWNLOAD REQUIRED")
        print(f"     {doc.get('manual_note', doc['source_url'])}")
        status = "skipped_manual"
        if dest.exists() and dest.stat().st_size > MIN_PDF_SIZE_BYTES:
            print(f"  ✓  Already present ({dest.stat().st_size // 1024} KB) — skipping.")
            status = "already_exists"
        return {
            "name": name,
            "filename": filename,
            "status": status,
            "message": "Manual download required — see instructions above.",
        }

    # Skip if already downloaded (and not a stub)
    if dest.exists() and dest.stat().st_size > MIN_PDF_SIZE_BYTES and not _is_html_stub(dest):
        print(f"  ✓  Already present ({dest.stat().st_size // 1024} KB) — skipping.")
        return {"name": name, "filename": filename, "status": "already_exists",
                "message": f"File present: {dest.stat().st_size // 1024} KB",
                "size_kb": dest.stat().st_size // 1024}

    if dest.exists() and _is_html_stub(dest):
        print(f"  ↻  Replacing HTML stub with real PDF...")

    # Resolve the actual PDF URL
    pdf_url = doc["source_url"]
    if doc_type in ("ebook_page", "detail_page"):
        print(f"  Fetching page: {pdf_url}")
        try:
            pdf_url = _extract_pdf_url_from_hpa_page(pdf_url)
        except Exception as exc:
            msg = f"Failed to fetch EBook page: {exc}"
            print(f"  ✗  {msg}")
            return {"name": name, "filename": filename, "status": "error", "message": msg}

        if not pdf_url:
            msg = "Could not locate a PDF download link on the EBook page."
            print(f"  ✗  {msg}")
            print(
                f"     Please visit the page manually and save the PDF as:\n"
                f"     {dest}"
            )
            return {"name": name, "filename": filename, "status": "error", "message": msg}
        print(f"  Resolved PDF URL: {pdf_url}")

    elif doc_type == "list_page":
        print(f"  Fetching list page: {pdf_url}")
        try:
            pdf_url = _extract_pdf_url_from_list_page(pdf_url, keyword=name)
        except Exception as exc:
            msg = f"Failed to fetch List page: {exc}"
            print(f"  ✗  {msg}")
            return {"name": name, "filename": filename, "status": "error", "message": msg}

        if not pdf_url:
            msg = "Could not locate a PDF download link on the List page."
            print(f"  ✗  {msg}")
            return {"name": name, "filename": filename, "status": "error", "message": msg}
        print(f"  Resolved PDF URL: {pdf_url}")

    # Download the PDF
    print(f"  Downloading: {pdf_url}")
    try:
        resp = _get(pdf_url)
    except Exception as exc:
        msg = f"Download failed: {exc}"
        print(f"  ✗  {msg}")
        return {"name": name, "filename": filename, "status": "error", "message": msg}

    content_type = resp.headers.get("Content-Type", "")
    if "html" in content_type.lower():
        msg = (
            f"Server returned HTML instead of PDF (Content-Type: {content_type}). "
            "The EBook page may require JavaScript or a login."
        )
        print(f"  ✗  {msg}")
        return {"name": name, "filename": filename, "status": "error", "message": msg}

    if len(resp.content) < MIN_PDF_SIZE_BYTES:
        msg = f"Downloaded file is too small ({len(resp.content)} bytes) — likely an error page."
        print(f"  ✗  {msg}")
        return {"name": name, "filename": filename, "status": "error", "message": msg}

    # Write to disk
    dest.write_bytes(resp.content)

    # Validate the downloaded file is actually a PDF (check %PDF magic bytes)
    with open(dest, "rb") as f:
        magic = f.read(8)
    if not magic.startswith(b"%PDF"):
        dest.unlink()
        msg = (
            f"Downloaded file does not appear to be a valid PDF "
            f"(header: {magic!r}). The server may require a login or JavaScript."
        )
        print(f"  ✗  {msg}")
        return {"name": name, "filename": filename, "status": "error", "message": msg}

    size_kb = len(resp.content) // 1024
    sha = _sha256(dest)
    print(f"  ✓  Saved {size_kb} KB  SHA-256: {sha[:16]}...")
    return {
        "name": name,
        "filename": filename,
        "status": "downloaded",
        "message": f"Downloaded {size_kb} KB",
        "size_kb": size_kb,
        "sha256": sha,
        "pdf_url": pdf_url,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    RAW_DOCS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  HPA Knowledge Base — Phase 1 Document Downloader")
    print("=" * 60)
    print(f"  Destination: {RAW_DOCS_DIR}")
    print(f"  Documents to process: {len(DOCUMENTS)}")

    results = []
    for doc in DOCUMENTS:
        result = download_document(doc)
        results.append(result)
        time.sleep(1)  # be polite to the server

    # Summary
    print(f"\n{'═' * 60}")
    print("  SUMMARY")
    print(f"{'═' * 60}")

    status_counts = {}
    for r in results:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1

    for r in results:
        icon = {
            "downloaded": "✓",
            "already_exists": "✓",
            "skipped_manual": "⚠",
            "error": "✗",
        }.get(r["status"], "?")
        print(f"  {icon}  {r['filename']:<50}  {r['status']}")

    print()
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")

    n_errors = status_counts.get("error", 0)
    n_manual = status_counts.get("skipped_manual", 0)

    if n_errors > 0:
        print(
            f"\n  {n_errors} document(s) failed to download automatically.\n"
            "  For each error:\n"
            "    1. Visit the source_url listed in scripts/download_hpa_docs.py\n"
            "    2. Download the PDF manually\n"
            "    3. Save it to knowledge_base/raw_documents/ with the canonical filename\n"
            "       listed in README.md"
        )
    if n_manual > 0:
        print(
            f"\n  {n_manual} document(s) require manual download — see instructions above."
        )

    if n_errors == 0 and n_manual == 0:
        print("\n  All documents downloaded successfully!")
        print(
            "\n  Next steps (Phase 1):\n"
            "    1. Run OCR and Markdown conversion on all new PDFs\n"
            "    2. Apply semantic chunking pipeline\n"
            "    3. Run medical content filter\n"
            "    4. Build vector index (target: ≥ 500 clean chunks across 5 categories)"
        )

    return 0 if n_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
