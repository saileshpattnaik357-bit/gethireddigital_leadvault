"""
LeadVault classifier evaluation harness.

Measures the shipping accept/reject decision (final_verifier + buying_intent_agent,
combined exactly as leadvault_mining_runner._classify_candidates combines them)
against a labelled corpus, and reports precision / recall / F1.

Two corpora are supported:

  gold   - hand-labelled rows in evaluation/gold_corpus.jsonl. Small, trusted.
  silver - the 1,446 evaluated posts from the legacy prototype debug reports
           (Test Python/MISC EXCEL/GETHIRED_Evaluated_Debug_Report_*.xlsx),
           labelled by a heuristic labeller. Large, directional only.

Silver labels are NOT ground truth. They exist so that a change to the
classifier can be compared before/after on a large sample. Treat the gold
number as the real one and the silver number as a trend indicator.

Usage:
    python -m evaluation.harness                # both corpora, print report
    python -m evaluation.harness --json out.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.buying_intent_agent import analyze_buying_intent  # noqa: E402
from services.final_verifier import verify_post  # noqa: E402

GOLD_PATH = HERE / "gold_corpus.jsonl"
REPORTS_DIR = HERE / "reports"
SILVER_SOURCE_DIR = Path(r"E:\Sailesh\Gethired Global\Leadvault\TECH\Test Python\MISC EXCEL")
SILVER_FILES = [
    "GETHIRED_Evaluated_Debug_Report_20260605_005936.xlsx",
    "GETHIRED_Evaluated_Debug_Report_20260608_232142.xlsx",
    "GETHIRED_Evaluated_Debug_Report_20260608_235549.xlsx",
    "GETHIRED_Evaluated_Debug_Report_20260609_153754.xlsx",
    "GETHIRED_Evaluated_Debug_Report_20260609_153833.xlsx",
    "GETHIRED_Evaluated_Debug_Report_20260616_005538.xlsx",
]

# Labels. "buyer" and "aggregator_rfp" are the positive class (should be accepted).
POSITIVE_LABELS = {"buyer", "aggregator_rfp"}
ALL_LABELS = ["buyer", "aggregator_rfp", "vendor", "content", "job", "noise"]


@dataclass
class EvalRow:
    text: str
    label: str
    source: str = ""
    objective: str = "agency_procurement"
    row_id: str = ""


@dataclass
class EvalReport:
    corpus: str
    rows: int
    positives: int
    predicted_positive: int
    true_positive: int
    false_positive: int
    false_negative: int
    precision: float
    recall: float
    f1: float
    accept_rate: float
    false_positives_by_label: dict[str, int]
    false_negatives_by_label: dict[str, int]
    generated_at_utc: str


# ----------------------------------------------------------------------------
# The decision under test. Mirrors leadvault_mining_runner._classify_candidates.
# ----------------------------------------------------------------------------

ACCEPT_THRESHOLD = 60


def classify_current(text: str, objective: str = "agency_procurement") -> bool:
    verification = verify_post(text, lead_objective=objective)
    intent = analyze_buying_intent(text, verification_category=verification.category)
    return bool(verification.should_export and intent.intent_score >= ACCEPT_THRESHOLD)


def make_llm_classifier(provider: Any, model: str, timeout: int = 60, only_borderline: bool = True) -> Callable[[str, str], bool]:
    """
    Same decision as the runner with LLM validation on. `accept` here counts a
    row as positive if it would be exported OR parked for review, because both
    mean "the system thinks this is a buyer".
    """
    from harness import llm as llm_layer
    from harness.context import build_packet
    from services.leadvault_mining_runner import _apply_llm_verdict

    def classify(text: str, objective: str = "agency_procurement") -> bool:
        verification = verify_post(text, lead_objective=objective)
        intent = analyze_buying_intent(text, verification_category=verification.category)
        verdict = None
        if (not only_borderline) or llm_layer.is_borderline(should_export=verification.should_export, score=intent.intent_score):
            packet = build_packet(objective=objective, post_text=text, deterministic_verdict={
                "category": verification.category, "score": intent.intent_score,
                "evidence": intent.evidence, "negative_signals": intent.negative_signals})
            verdict = llm_layer.validate(packet, provider=provider, model=model, tenant="eval", timeout=timeout).as_dict()
        accept, _, _, _ = _apply_llm_verdict(verification.should_export, intent.intent_score, verdict, verification.category)
        return bool(accept)

    return classify


# ----------------------------------------------------------------------------
# Silver labeller (heuristic). Kept here so the labelling rule is inspectable.
# ----------------------------------------------------------------------------

_VENDOR = re.compile(
    r"(i'?m (currently )?offering|i help|i've (worked|helped)|i helped|let'?s connect|happy to be a resource|"
    r"dm me|book a call|i'?m building a|my (agency|clients)|we (offer|provide|specialize)|just shipped|"
    r"thanks to .{0,30}testimonial|available for (work|hire|projects)|now accepting)", re.I)
_JOB = re.compile(
    r"(#hiring|apply here|this position is based|we are looking for a .{0,25}(consultant|developer|engineer|manager)!|"
    r"full[- ]time|join our team|apply now|send (your )?resume)", re.I)
_CONTENT = re.compile(
    r"(why (does|do) your|here are (a few|the)|top \d+|best \d+|ultimate guide|guide to|how to|are you |"
    r"don'?t you think|isn'?t just about|the challenge is|those are useful signals|things to check|"
    r"lessons learned|best practices|what i learned)", re.I)
_AGGREGATOR = re.compile(
    r"\b(a |an )?(u\.s\.|us|uk|san francisco|european|australian|canadian|irish|national)?\s*"
    r"(university|organization|organisation|company|firm|brand|startup|business|agency|retailer|nonprofit)\b"
    r".{0,60}\b(is|are) (looking for|seeking|searching for)", re.I)
_BUYER = re.compile(
    r"\b(we|our (company|team|startup|business|org))\b.{0,80}\b(need|looking for|seeking|in the market for|"
    r"can anyone recommend|anyone recommend|recommendations for)\b", re.I)


def silver_label(text: str) -> str:
    t = text or ""
    if _VENDOR.search(t):
        return "vendor"
    if _JOB.search(t):
        return "job"
    if _CONTENT.search(t):
        return "content"
    if _AGGREGATOR.search(t):
        return "aggregator_rfp"
    if _BUYER.search(t):
        return "buyer"
    return "noise"


# ----------------------------------------------------------------------------
# Corpus loaders
# ----------------------------------------------------------------------------

def load_gold() -> list[EvalRow]:
    rows: list[EvalRow] = []
    if not GOLD_PATH.exists():
        return rows
    for i, line in enumerate(GOLD_PATH.read_text(encoding="utf-8").splitlines()):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        data = json.loads(line)
        rows.append(EvalRow(
            text=str(data["text"]),
            label=str(data["label"]),
            source=str(data.get("source", "gold")),
            objective=str(data.get("objective", "agency_procurement")),
            row_id=str(data.get("id", f"gold_{i}")),
        ))
    return rows


def load_silver() -> list[EvalRow]:
    try:
        from openpyxl import load_workbook
    except Exception:  # pragma: no cover
        return []
    rows: list[EvalRow] = []
    seen: set[str] = set()
    for name in SILVER_FILES:
        path = SILVER_SOURCE_DIR / name
        if not path.exists():
            continue
        wb = load_workbook(path, read_only=True, data_only=True)
        if "All Evaluated" not in wb.sheetnames:
            continue
        ws = wb["All Evaluated"]
        header: list[str] = []
        for r_index, values in enumerate(ws.iter_rows(values_only=True)):
            if r_index == 0:
                header = [str(v or "").strip() for v in values]
                continue
            row = dict(zip(header, values))
            text = str(row.get("Snippet") or "").strip()
            url = str(row.get("URL") or "").strip()
            key = url or text[:200]
            if not text or key in seen:
                continue
            seen.add(key)
            rows.append(EvalRow(
                text=text,
                label=silver_label(text),
                source=str(row.get("Source Type") or "legacy"),
                row_id=key[:120],
            ))
    return rows


# ----------------------------------------------------------------------------
# Scoring
# ----------------------------------------------------------------------------

def evaluate(rows: Iterable[EvalRow], classify: Callable[[str, str], bool], corpus: str) -> tuple[EvalReport, list[dict[str, Any]]]:
    rows = list(rows)
    tp = fp = fn = 0
    predicted_positive = 0
    fp_by: Counter[str] = Counter()
    fn_by: Counter[str] = Counter()
    details: list[dict[str, Any]] = []
    for row in rows:
        gold_pos = row.label in POSITIVE_LABELS
        pred = classify(row.text, row.objective)
        predicted_positive += int(pred)
        if pred and gold_pos:
            tp += 1
        elif pred and not gold_pos:
            fp += 1
            fp_by[row.label] += 1
        elif not pred and gold_pos:
            fn += 1
            fn_by[row.label] += 1
        details.append({"id": row.row_id, "label": row.label, "predicted_accept": pred, "text": row.text[:240]})
    positives = sum(1 for r in rows if r.label in POSITIVE_LABELS)
    precision = tp / predicted_positive if predicted_positive else 0.0
    recall = tp / positives if positives else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    report = EvalReport(
        corpus=corpus,
        rows=len(rows),
        positives=positives,
        predicted_positive=predicted_positive,
        true_positive=tp,
        false_positive=fp,
        false_negative=fn,
        precision=round(precision, 4),
        recall=round(recall, 4),
        f1=round(f1, 4),
        accept_rate=round(predicted_positive / len(rows), 4) if rows else 0.0,
        false_positives_by_label=dict(fp_by),
        false_negatives_by_label=dict(fn_by),
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    return report, details


def run_all(classify: Callable[[str, str], bool] = classify_current, write_report: bool = True) -> dict[str, Any]:
    out: dict[str, Any] = {"reports": {}, "label_distribution": {}}
    for corpus, loader in (("gold", load_gold), ("silver", load_silver)):
        rows = loader()
        if not rows:
            out["reports"][corpus] = None
            continue
        report, details = evaluate(rows, classify, corpus)
        out["reports"][corpus] = asdict(report)
        out["label_distribution"][corpus] = dict(Counter(r.label for r in rows))
        out.setdefault("details", {})[corpus] = details
    if write_report:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        (REPORTS_DIR / f"eval_{stamp}.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    return out


def _print(out: dict[str, Any]) -> None:
    for corpus, report in out["reports"].items():
        print("=" * 70)
        if not report:
            print(f"{corpus.upper()}: corpus not available")
            continue
        print(f"{corpus.upper()} CORPUS  rows={report['rows']}  positives={report['positives']}")
        print(f"  label distribution : {out['label_distribution'].get(corpus)}")
        print(f"  accept rate        : {report['accept_rate']:.1%}  ({report['predicted_positive']} accepted)")
        print(f"  precision          : {report['precision']:.1%}")
        print(f"  recall             : {report['recall']:.1%}")
        print(f"  f1                 : {report['f1']:.3f}")
        print(f"  false positives by : {report['false_positives_by_label']}")
        print(f"  false negatives by : {report['false_negatives_by_label']}")
    print("=" * 70)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="also write full output to this path")
    ap.add_argument("--llm", choices=["ollama", "openai", "anthropic"], help="also score with the LLM validator via this provider")
    ap.add_argument("--model", default=None, help="model id for --llm (default: settings.LEADVAULT_LLM_MODEL)")
    ap.add_argument("--gold-only", action="store_true", help="skip the silver corpus (LLM runs are slow)")
    ap.add_argument("--all-rows", action="store_true", help="send every row to the LLM, not just borderline ones")
    args = ap.parse_args()
    if args.gold_only:
        global load_silver
        load_silver = lambda: []  # noqa: E731
    if args.llm:
        from config import settings
        from harness import llm as llm_layer
        import copy
        s2 = copy.copy(settings)
        s2.LEADVAULT_LLM_VALIDATION = "1"; s2.LEADVAULT_LLM_PROVIDER = args.llm
        provider = llm_layer.build_provider(s2)
        if provider.name == "null":
            print(f"provider {args.llm} not available (missing key?)"); return 2
        model = args.model or settings.LEADVAULT_LLM_MODEL
        print(f"LLM-assisted run: provider={provider.name} model={model} borderline_only={not args.all_rows}")
        out = run_all(classify=make_llm_classifier(provider, model, only_borderline=not args.all_rows))
    else:
        out = run_all()
    _print(out)
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
