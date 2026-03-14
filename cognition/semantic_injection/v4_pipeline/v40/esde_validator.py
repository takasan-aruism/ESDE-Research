#!/usr/bin/env python3
"""
ESDE v4.0 — Output Validator
==============================
Phase : v4.0 Language Interface (Post-Generation Gate)
Role  : Claude (Implementation), spec by GPT (Audit)

Validates and sanitizes LLM output per Mode A System Directive.
Implements three audit rules from GPT Collapse Docking Audit:

  Rule 1: No reasoning leakage (<think> blocks, planning phrases)
  Rule 2: No prompt awareness (references to directive/instruction)
  Rule 3: Controlled interpretation (flag absolute claims)

USAGE
-----
  # Validate a response string
  python esde_validator.py response.txt

  # Validate + auto-strip reasoning leakage
  python esde_validator.py response.txt --strip

  # Pipe from curl
  curl -s ... | python3 -c "import json,sys; ..." | python esde_validator.py --stdin
"""

import re, sys, argparse, json


# ================================================================
# RULE 1: Reasoning Leakage
# ================================================================
# QwQ-32B emits <think>...</think> blocks with internal reasoning.
# These must be stripped entirely before validation.

THINK_PATTERN = re.compile(r"<think>.*?</think>", re.DOTALL)
# QwQ-32B sometimes omits <think> but includes </think>
THINK_CLOSE_ONLY = re.compile(r"^.*?</think>\s*", re.DOTALL)

REASONING_PHRASES = [
    r"\bI need to\b",
    r"\bI should\b",
    r"\bLet me\b",
    r"\bThe user wants\b",
    r"\bThe user is asking\b",
    r"\bFirst,? I\b",
    r"\bOkay,? I\b",
    r"\bNow I\b",
    r"\bI['']ll structure\b",
    r"\bI['']ll go through\b",
    r"\bstep by step\b",
]

REASONING_RE = [re.compile(p, re.IGNORECASE) for p in REASONING_PHRASES]


def strip_think_blocks(text: str) -> str:
    """Remove <think>...</think> blocks entirely.
    Also handles QwQ-32B pattern: reasoning text + </think> without opening tag."""
    result = THINK_PATTERN.sub("", text).strip()
    if "</think>" in result:
        result = THINK_CLOSE_ONLY.sub("", result).strip()
    return result


def check_reasoning_leakage(text: str) -> list[str]:
    """Return list of reasoning phrase violations found."""
    violations = []
    for pattern in REASONING_RE:
        matches = pattern.findall(text)
        if matches:
            violations.append(f"reasoning_phrase: '{matches[0]}'")
    return violations


# ================================================================
# RULE 2: Prompt Awareness
# ================================================================
PROMPT_PHRASES = [
    r"\bSTATE_PACKET\b",
    r"\bSYSTEM DIRECTIVE\b",
    r"\b[Pp]rompt\b",
    r"\b[Dd]irective\b",
    r"\b[Ii]nstruction\b",
    r"\b[Uu]ser [Ii]nput\b",
    r"\bPROPRIOCEPTION\b",
    r"\bthe response must\b",
    r"\bthe output must\b",
    r"\bmy (task|role) is\b",
]

PROMPT_RE = [re.compile(p) for p in PROMPT_PHRASES]


def check_prompt_awareness(text: str) -> list[str]:
    """Return list of prompt-reference violations found."""
    violations = []
    for pattern in PROMPT_RE:
        matches = pattern.findall(text)
        if matches:
            violations.append(f"prompt_reference: '{matches[0]}'")
    return violations


# ================================================================
# RULE 3: Controlled Interpretation
# ================================================================
# Flag absolute claims that may exceed metric grounding.
# These are warnings, not hard rejections.

ABSOLUTE_PHRASES = [
    r"\bis empty\b",
    r"\bis gone\b",
    r"\bnothing remains\b",
    r"\bcompletely destroyed\b",
    r"\btotally dissolved\b",
    r"\bno longer exist\b",
    r"\bceased to exist\b",
    r"\bcannot recover\b",
    r"\bwill never\b",
    r"\bwill collapse\b",
    r"\bwill dissolve\b",
]

ABSOLUTE_RE = [re.compile(p, re.IGNORECASE) for p in ABSOLUTE_PHRASES]


def check_absolute_claims(text: str) -> list[str]:
    """Return list of absolute-claim warnings (soft, not rejection)."""
    warnings = []
    for pattern in ABSOLUTE_RE:
        matches = pattern.findall(text)
        if matches:
            warnings.append(f"absolute_claim: '{matches[0]}'")
    return warnings


# ================================================================
# TRACEABILITY CHECK
# ================================================================
def check_traceability(text: str) -> list[str]:
    """Verify OUTPUT_ID and STATE_HASH are present."""
    issues = []
    if "[OUTPUT_ID:" not in text:
        issues.append("missing OUTPUT_ID tag")
    if "[STATE_HASH:" not in text:
        issues.append("missing STATE_HASH tag")
    return issues


# ================================================================
# EMOTION CHECK
# ================================================================
EMOTION_WORDS = [
    r"\bjoy\b", r"\bsadness\b", r"\bfear\b", r"\bhope\b",
    r"\bhappy\b", r"\bsad\b", r"\bafraid\b", r"\bangry\b",
    r"\bgrief\b", r"\blove\b", r"\bhate\b", r"\bterrified\b",
    r"\bexcited\b", r"\banxious\b", r"\bdespair\b", r"\brelief\b",
    r"\bjoyful\b", r"\bsorrowful\b", r"\bfrightened\b",
]

EMOTION_RE = [re.compile(p, re.IGNORECASE) for p in EMOTION_WORDS]


def check_emotions(text: str) -> list[str]:
    """Flag emotional language (hard violation in Mode A)."""
    violations = []
    for pattern in EMOTION_RE:
        matches = pattern.findall(text)
        if matches:
            violations.append(f"emotion: '{matches[0]}'")
    return violations


# ================================================================
# FULL VALIDATION
# ================================================================
def validate(raw_response: str, auto_strip: bool = True) -> dict:
    """
    Validate an LLM response against Mode A rules.

    Returns:
      {
        "status": "PASS" | "FAIL" | "WARN",
        "cleaned": <stripped text>,
        "violations": [...],
        "warnings": [...],
      }
    """
    # Step 1: Strip <think> blocks
    if auto_strip:
        cleaned = strip_think_blocks(raw_response)
    else:
        cleaned = raw_response

    violations = []
    warnings = []

    # Rule 1: Reasoning leakage
    if not auto_strip:
        # If not auto-stripping, check for think blocks
        if THINK_PATTERN.search(raw_response):
            violations.append("think_block_present")

    reasoning = check_reasoning_leakage(cleaned)
    violations.extend(reasoning)

    # Rule 2: Prompt awareness
    prompt = check_prompt_awareness(cleaned)
    violations.extend(prompt)

    # Rule 3: Absolute claims (warnings only)
    absolutes = check_absolute_claims(cleaned)
    warnings.extend(absolutes)

    # Traceability
    trace = check_traceability(cleaned)
    violations.extend(trace)

    # Emotion check
    emotions = check_emotions(cleaned)
    violations.extend(emotions)

    # Verdict
    if violations:
        status = "FAIL"
    elif warnings:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "status": status,
        "cleaned": cleaned,
        "violations": violations,
        "warnings": warnings,
    }


# ================================================================
# CLI
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="ESDE v4.0 Output Validator")
    parser.add_argument("file", nargs="?", help="Response text file")
    parser.add_argument("--stdin", action="store_true",
                        help="Read from stdin")
    parser.add_argument("--strip", action="store_true", default=True,
                        help="Auto-strip <think> blocks (default: True)")
    parser.add_argument("--no-strip", action="store_true",
                        help="Do NOT auto-strip <think> blocks")
    parser.add_argument("--json-input", action="store_true",
                        help="Input is API JSON response; extract content")
    args = parser.parse_args()

    if args.no_strip:
        args.strip = False

    # Read input
    if args.stdin or (not args.file):
        raw = sys.stdin.read()
    else:
        with open(args.file) as f:
            raw = f.read()

    # Extract content from API JSON if needed
    if args.json_input:
        try:
            data = json.loads(raw)
            raw = data["choices"][0]["message"]["content"]
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"[SYS_CHECK: FAIL — Cannot parse API response: {e}]")
            sys.exit(1)

    # Validate
    result = validate(raw, auto_strip=args.strip)

    # Output
    print(f"\n{'='*60}")
    print(f"  ESDE v4.0 Output Validator — {result['status']}")
    print(f"{'='*60}")

    if result["violations"]:
        print(f"\n  VIOLATIONS ({len(result['violations'])}):")
        for v in result["violations"]:
            print(f"    - {v}")

    if result["warnings"]:
        print(f"\n  WARNINGS ({len(result['warnings'])}):")
        for w in result["warnings"]:
            print(f"    - {w}")

    print(f"\n  CLEANED OUTPUT:")
    print(f"  {'-'*56}")
    print(f"  {result['cleaned']}")
    print(f"  {'-'*56}")

    if result["status"] == "PASS":
        print(f"\n  [SYS_CHECK: PASS]")
    elif result["status"] == "WARN":
        print(f"\n  [SYS_CHECK: PASS — with warnings]")
    else:
        print(f"\n  [SYS_CHECK: FAIL — {', '.join(result['violations'])}]")

    sys.exit(0 if result["status"] != "FAIL" else 1)


if __name__ == "__main__":
    main()
