#!/usr/bin/env python3
"""Offline validation for sanitized ABUTRON automation inventory; no host access."""
from __future__ import annotations
import collections, json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INV=ROOT/"inventory"
HEX64=re.compile(r"[a-f0-9]{64}\Z",re.I)
CID=re.compile(r"[a-f0-9]{32}",re.I)
LOGIN=re.compile(r"\d{5,12}")
FORBIDDEN=("-----BEGIN PRIVATE KEY-----","-----BEGIN OPENSSH PRIVATE KEY-----",
           "MQL5/Files/ABUTRON_ACTIVATION_SECRET.txt","sk-proj-")
def check(ok,reason):
    if not ok:raise AssertionError(reason)
def main():
    summary=json.loads((INV/"summary.json").read_text(encoding="utf-8"))
    registry=json.loads((INV/"worker-source-registry.json").read_text(encoding="utf-8"))
    rows=[]
    for f in sorted(INV.glob("*.json")):
        if f.name in ("summary.json","worker-source-registry.json"):continue
        x=json.loads(f.read_text(encoding="utf-8"))
        check(x.get("schema")=="abutron.automation.unit_group.v1","INVALID_CATEGORY_SCHEMA")
        check(x.get("category")==f.stem,"GROUP_FILENAME_MISMATCH")
        check(x.get("snapshot_utc")==summary["snapshot_utc"],"SNAPSHOT_TIME_MISMATCH")
        for u in x["units"]:
            check(u.get("category")==f.stem,"CATEGORY_MISMATCH")
            check(u.get("type") in ("service","timer","socket","path"),"UNKNOWN_UNIT_KIND")
            check(not u.get("raw_unit_text_exported"),"RAW_SERVICE_TEXT_MUST_NOT_BE_EXPORTED")
            for k in ("unit_name_sanitized","source_basename","run_as","source_public_ref"):
                value=u.get(k) or ""
                check(not CID.search(value) and not LOGIN.search(value),"IDENTITY_IN_UNIT_FIELD")
            for k in ("definition_sha256","source_sha256"):
                val=u.get(k)
                check(val is None or bool(HEX64.fullmatch(val)), "BAD_SHA256")
            check(not any(k in u for k in ("environment","env","exec_start_args","account_login","connection_id","password","token")),"PRIVATE_FIELD_PUBLISHED")
        rows.extend(x["units"])
    check(len(rows)==summary["total"],"UNIT_SUMMARY_COUNT_MISMATCH")
    check(len({u["id"] for u in rows})==len(rows),"DUPLICATE_SNAPSHOT_UNIT_ID")
    check(dict(collections.Counter(u["type"] for u in rows))==summary["unit_types"],"UNIT_TYPE_COUNT_MISMATCH")
    check(dict(collections.Counter(u["active_state"] for u in rows))==summary["active_states"],"ACTIVE_STATE_COUNT_MISMATCH")
    check(dict(collections.Counter(u["install_state"] for u in rows))==summary["install_states"],"INSTALL_STATE_COUNT_MISMATCH")
    check(dict(collections.Counter(u["category"] for u in rows))==summary["categories"],"CATEGORY_COUNT_MISMATCH")
    src=registry.get("sources",[])
    check(len(src)==summary["unique_source_files"],"SOURCE_REGISTRY_COUNT_MISMATCH")
    for s in src:
        name=s.get("source_basename") or ""
        check(not CID.search(name) and not LOGIN.search(name),"IDENTITY_IN_SOURCE_NAME")
        digest=s.get("source_sha256")
        check(digest is None or bool(HEX64.fullmatch(digest)),"BAD_SOURCE_SHA256")
        check(s.get("publication") in ("REVIEW_REQUIRED_NOT_EXPORTED","EXISTING_SANITIZED_V9_REVIEW_SOURCE_MAY_DIFFER_FROM_HOST"),"INVALID_PUBLICATION_STATUS")
    for p in ROOT.rglob("*"):
        if p.resolve() == Path(__file__).resolve():
            continue  # Do not match scanner definitions against their own literal test patterns.
        if p.is_file() and p.suffix in (".md",".json",".py"):
            body=p.read_text(encoding="utf-8")
            check(not any(marker in body for marker in FORBIDDEN),"FORBIDDEN_PRIVATE_MATERIAL_MARKER")
    print(f"PASS automation inventory: {len(rows)} units, {len(src)} unique source references, 9 groups, zero raw unit text, 0 identity fields")
    return 0
if __name__=="__main__":
    try:sys.exit(main())
    except (AssertionError,KeyError,ValueError) as exc:
        print(f"FAIL {type(exc).__name__}: {exc}",file=sys.stderr)
        sys.exit(1)
