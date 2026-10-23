"""Plain-language questions ("Ask" tab): question → plan → results with evidence → written answer.

No paid API. Two ways to get the plan and the written answer:
  * Claude Code on this Mac (headless `claude -p`, Laura's Claude account, like Leggio's ✦ Refine): the Ask tab's
    "Ask Claude" button. Two short calls: one writes the plan, one writes the answer from Conti's results.
  * A Cowork chat: "Save for a chat" stores the question as waiting; in the chat Claude runs
        cd conti && python3 -m conti.ask pending                     # questions waiting
        python3 -m conti.ask packet <id>                             # writes .work/ask/<id>/ (profile, plan language)
        python3 -m conti.ask run <id> --plan plan.json [--answer answer.json]
Conti itself always computes the numbers (analyze.py); Claude only chooses the steps and words the answer.
Re-running a question ("↻ Re-run") repeats its plan on today's data without Claude, so answers grow with the edition.

Stored in conti_data/_questions/<id>.json:
  {id, question, t, status: waiting|planning|running|writing|done|error, source, title, understood, limits,
   plan, result, answer{headline, answer, claims, caveats, followups}, log[], error, updated, reruns}
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from . import analyze, data, extract, ledger, query, source, tags as tagmod

DIR = data.DATA / "_questions"
WORK = source.ROOT / ".work" / "ask"
PROMPTS = Path(__file__).parent / "prompts"
_jobs: dict[str, threading.Thread] = {}

EXAMPLES = [
    "Which occupation consistently borrowed the largest sums, with data to back up this assertion?",
    "Create a network analysis of the top 50 borrowers and lenders, and who they were borrowing from or lending to.",
    "Who paid back the most, and through whom (which agents received the payments)?",
    "Which people appear most often across the tagged pages, and with which occupations?",
    "How many entries refer to the libro giallo, and to which folios?",
]


# ------------------------------------------------------------------ storage
def _path(qid):
    return DIR / f"{qid}.json"


def get(qid: str) -> dict | None:
    return data.read("_questions", f"{qid}.json", None)


def save(rec: dict) -> dict:
    rec["updated"] = data.now()
    data.write("_questions", f"{rec['id']}.json", rec)
    return rec


def all_() -> list[dict]:
    out = []
    for f in sorted(DIR.glob("*.json")) if DIR.exists() else []:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        out.append({k: d.get(k) for k in ("id", "question", "title", "status", "t", "updated", "source", "error")}
                   | {"headline": (d.get("answer") or {}).get("headline", "")})
    return sorted(out, key=lambda d: d.get("t") or "", reverse=True)


def new(question: str, source_: str = "claude-code") -> dict:
    q = (question or "").strip()
    if not q:
        raise ValueError("empty question")
    qid = time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:4]
    return save({"id": qid, "question": q, "t": data.now(), "status": "waiting" if source_ == "chat" else "planning",
                 "source": source_, "log": []})


def delete(qid: str) -> None:
    p = _path(qid)
    if p.exists():
        trash = data.DATA / "_questions_deleted"; trash.mkdir(parents=True, exist_ok=True)
        p.replace(trash / p.name)


def _log(rec, msg):
    rec.setdefault("log", []).append(f"{time.strftime('%H:%M:%S')} {msg}")
    save(rec)


# ------------------------------------------------------------------ what the data holds (for the plan)
def profile() -> dict:
    al = tagmod.aliases()
    out = {"manuscripts": [], "vocabulary": {}}
    voc = {t: {} for t in tagmod.TYPES}
    roles, titles = {}, {}
    for c in source.collections():
        cid = c["id"]; st = data.settings(cid)
        pm = source.pages(cid)
        recs = extract.records(cid, st["statuses"])
        s = extract.summary(recs)
        years = sorted({d["year_modern"] for r in recs for d in r["dates"] if d.get("year_modern")})
        out["manuscripts"].append({"id": cid, "title": c["title"], "pages_total": len(pm), "pages_included": s["pages"],
                                   "pages_tagged": len({r["page"] for r in recs if r["tags"]}), "entries": s["entries"],
                                   "debit_lines": s["debit"], "credit_lines": s["credit"], "sums": s["sums"],
                                   "sums_checked": s["sums_confirmed"], "tags": s["tags"], "tags_approved": s["tags_approved"],
                                   "years_modern": [years[0], years[-1]] if years else [],
                                   "account_holder": st.get("account_holder") or "(not set)"})
        for r in recs:
            for t in r["tags"]:
                voc[t["type"]][t["canon"]] = voc[t["type"]].get(t["canon"], 0) + 1
                a = t.get("attrs") or {}
                if a.get("role"):
                    roles[a["role"]] = roles.get(a["role"], 0) + 1
                if a.get("title"):
                    titles[a["title"]] = titles.get(a["title"], 0) + 1
    for t, d in voc.items():
        out["vocabulary"][t] = dict(sorted(d.items(), key=lambda kv: -kv[1])[: (60 if t == "person" else 80)])
    out["roles"] = roles; out["titles"] = titles
    tx = ledger.transactions()
    out["debts"] = {"debts": sum(1 for t in tx if t["kind"] == "debt"), "payments": sum(1 for t in tx if t["kind"] == "payment"),
                    "with_debtor": sum(1 for t in tx if t["debtors"]), "with_occupation": sum(1 for t in tx if any(d["occupations"] for d in t["debtors"])),
                    "dated": sum(1 for t in tx if t["year"]), "creditor_tagged": sum(1 for t in tx if t["creditor"]["basis"] == "tagged")}
    return out


def plan_language() -> str:
    return ("# Plan language\n\n## Steps (analyze.py)\n```\n" + analyze.__doc__ + "\n```\n\n## How debts are read (ledger.py)\n```\n"
            + ledger.__doc__ + "\n```\n\n## Conti queries (for op \"query\")\n```\n" + query.__doc__ + "\n```\n"
            + "\nGroup-by values for queries: " + ", ".join(query.GROUPS) + "\n")


def packet(rec: dict) -> Path:
    out = WORK / rec["id"]; out.mkdir(parents=True, exist_ok=True)
    (out / "question.txt").write_text(rec["question"] + "\n", encoding="utf-8")
    (out / "profile.json").write_text(json.dumps(profile(), ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "PLAN_LANGUAGE.md").write_text(plan_language(), encoding="utf-8")
    (out / "INSTRUCTIONS.md").write_text((PROMPTS / "ask_plan.md").read_text(encoding="utf-8"), encoding="utf-8")
    (out / "ANSWER_INSTRUCTIONS.md").write_text((PROMPTS / "ask_answer.md").read_text(encoding="utf-8"), encoding="utf-8")
    return out


# ------------------------------------------------------------------ Claude Code (headless, signed-in plan)
def _claude():
    from leggio import refine as _lr          # read-only use of Leggio's helpers (finding claude, clean env)
    return _lr


def claude_status() -> dict:
    try:
        return _claude().status()
    except Exception as e:  # noqa: BLE001
        return {"found": False, "message": str(e)}


def _extract_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.M).strip()
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b < a:
        raise ValueError("Claude's answer contained no JSON object")
    return json.loads(text[a:b + 1])


def _call(out: Path, prompt: str, name: str) -> dict:
    lr = _claude()
    from leggio import store as _ls
    s = _ls.get_settings()
    p = lr.claude_path(s)
    if not p:
        raise RuntimeError("Claude Code was not found on this Mac (Leggio → Settings → Claude explains the setup). "
                           "You can still use “Save for a chat”.")
    cmd = [p, "-p", prompt, "--output-format", "json"] + list(s.get("claude_args") or [])
    if s.get("claude_model"):
        cmd += ["--model", s["claude_model"]]
    r = subprocess.run(cmd, cwd=str(out), capture_output=True, text=True, stdin=subprocess.DEVNULL, env=lr._env(),
                       timeout=int(float(s.get("claude_timeout_min") or 15) * 60))
    (out / f"{name}_stdout.txt").write_text(r.stdout or "", encoding="utf-8")
    (out / f"{name}_stderr.txt").write_text(r.stderr or "", encoding="utf-8")
    try:
        res = json.loads(r.stdout)
    except ValueError:
        raise RuntimeError(f"Claude Code did not answer as expected (exit {r.returncode}): {(r.stderr or r.stdout or '')[-300:]}")
    if res.get("is_error"):
        raise RuntimeError(f"Claude Code reported an error: {str(res.get('result'))[:300]}")
    ans = _extract_json(res.get("result") or "")
    (out / f"{name}.json").write_text(json.dumps(ans, ensure_ascii=False, indent=1), encoding="utf-8")
    return ans


# ------------------------------------------------------------------ steps
def execute(rec: dict, plan: dict) -> dict:
    """Run a plan through Conti and store the result (and a fallback answer until a written one exists)."""
    rec["plan"] = plan
    rec["status"] = "running"; save(rec)
    rec["result"] = analyze.run(plan)
    rec["error"] = None
    return save(rec)


def write_results(rec: dict) -> Path:
    out = WORK / rec["id"]; out.mkdir(parents=True, exist_ok=True)
    (out / "question.txt").write_text(rec["question"] + "\n", encoding="utf-8")
    (out / "plan.json").write_text(json.dumps(rec["plan"], ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "results.json").write_text(json.dumps(analyze.digest(rec["result"]), ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (out / "ANSWER_INSTRUCTIONS.md").write_text((PROMPTS / "ask_answer.md").read_text(encoding="utf-8"), encoding="utf-8")
    return out


def set_answer(rec: dict, ans: dict) -> dict:
    keep = {k: ans.get(k) for k in ("headline", "answer", "claims", "caveats", "followups")}
    keep["claims"] = [c for c in keep.get("claims") or [] if isinstance(c, dict) and c.get("text")]
    keep["caveats"] = [str(c) for c in keep.get("caveats") or []]
    keep["followups"] = [str(c) for c in keep.get("followups") or []]
    keep["written_on_data_of"] = (rec.get("result") or {}).get("t")
    rec["answer"] = keep; rec["status"] = "done"
    return save(rec)


def _work(qid: str):
    rec = get(qid)
    try:
        out = packet(rec)
        _log(rec, "Claude: writing a plan…")
        p = _call(out, "Read INSTRUCTIONS.md in this folder and follow it exactly. Your final message must be only the JSON object it asks for.", "plan")
        for k in ("title", "understood", "limits"):
            rec[k] = p.get(k) or rec.get(k) or ""
        plan = p.get("plan") or {}
        plan.setdefault("title", rec.get("title")); plan.setdefault("question", rec["question"])
        _log(rec, f"Plan: {len(plan.get('steps') or [])} steps. Conti is running it…")
        try:
            execute(rec, plan)
        except analyze.PlanError as e:
            _log(rec, f"The plan did not run ({e}); asking Claude to fix it…")
            (out / "plan_error.txt").write_text(str(e), encoding="utf-8")
            p = _call(out, "Read INSTRUCTIONS.md and PLAN_LANGUAGE.md. Your previous plan (plan.json) failed with the error in "
                           "plan_error.txt. Return the corrected JSON object only.", "plan2")
            plan = p.get("plan") or {}; plan.setdefault("question", rec["question"])
            execute(rec, plan)
        rec = get(qid)
        rec["status"] = "writing"; _log(rec, "Claude: writing the answer from Conti's results…")
        out = write_results(rec)
        ans = _call(out, "Read ANSWER_INSTRUCTIONS.md in this folder and follow it exactly. Your final message must be only the JSON object it asks for.", "answer")
        set_answer(rec, ans)
        _log(rec, "Done.")
    except Exception as e:  # noqa: BLE001
        rec = get(qid) or rec
        rec["status"] = "error"; rec["error"] = str(e)[:600]
        _log(rec, f"Stopped: {e}")
    finally:
        _jobs.pop(qid, None)


def start(qid: str) -> dict:
    rec = get(qid)
    if not rec:
        raise ValueError("no such question")
    if qid in _jobs and _jobs[qid].is_alive():
        return rec
    rec["status"] = "planning"; rec["source"] = "claude-code"; rec["error"] = None; save(rec)
    t = threading.Thread(target=_work, args=(qid,), daemon=True)
    _jobs[qid] = t; t.start()
    return rec


def rerun(qid: str) -> dict:
    """Same plan on today's data (no Claude). The written answer is kept but marked as written on older data."""
    rec = get(qid)
    if not rec or not rec.get("plan"):
        raise ValueError("this question has no plan yet")
    execute(rec, rec["plan"])
    rec = get(qid); rec["status"] = "done" if rec.get("answer") else "answered-without-text"
    rec["reruns"] = (rec.get("reruns") or 0) + 1
    return save(rec)


# ------------------------------------------------------------------ CLI (for answering in a Cowork chat)
def main(argv=None):
    ap = argparse.ArgumentParser(prog="python3 -m conti.ask", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("pending", help="questions saved for a chat (status waiting) or stopped with an error")
    sub.add_parser("profile", help="print what the data holds")
    s = sub.add_parser("new", help="store a new question"); s.add_argument("question")
    s = sub.add_parser("packet", help="write .work/ask/<id>/ (profile, plan language, instructions)"); s.add_argument("id")
    s = sub.add_parser("run", help="run a plan for a question (and store a written answer)")
    s.add_argument("id"); s.add_argument("--plan", required=True); s.add_argument("--answer")
    s.add_argument("--title"); s.add_argument("--understood"); s.add_argument("--limits")
    s = sub.add_parser("digest", help="print the results digest Claude writes the answer from"); s.add_argument("id")
    s = sub.add_parser("answer", help="store a written answer (JSON file)"); s.add_argument("id"); s.add_argument("answer")
    a = ap.parse_args(argv)
    if a.cmd == "pending":
        for q in all_():
            if q["status"] != "done":
                print(f"{q['id']}\t{q['status']}\t{q['question']}")
    elif a.cmd == "profile":
        print(json.dumps(profile(), ensure_ascii=False, indent=1))
    elif a.cmd == "new":
        print(new(a.question, "chat")["id"])
    elif a.cmd == "packet":
        print(packet(get(a.id)))
    elif a.cmd == "run":
        rec = get(a.id)
        p = json.loads(Path(a.plan).read_text(encoding="utf-8"))
        plan = p.get("plan", p)
        for k in ("title", "understood", "limits"):
            v = getattr(a, k) or p.get(k)
            if v:
                rec[k] = v
        rec["source"] = "chat"
        plan.setdefault("question", rec["question"])
        execute(rec, plan)
        rec = get(a.id)
        out = write_results(rec)
        if a.answer:
            set_answer(rec, json.loads(Path(a.answer).read_text(encoding="utf-8")))
        else:
            rec["status"] = "answered-without-text"; save(rec)
        print(f"ran {len(plan['steps'])} steps → results digest in {out / 'results.json'}")
    elif a.cmd == "digest":
        print(json.dumps(analyze.digest(get(a.id)["result"]), ensure_ascii=False, indent=1, default=str))
    elif a.cmd == "answer":
        set_answer(get(a.id), json.loads(Path(a.answer).read_text(encoding="utf-8")))
        print("stored")


if __name__ == "__main__":
    main(sys.argv[1:])
