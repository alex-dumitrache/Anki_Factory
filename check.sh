#!/usr/bin/env bash
# Integrity pass for the pipeline repo.  bash check.sh
# Orientation hygiene: catches the friction paid at the start of every session.

cd "$(dirname "$0")" || exit 1
echo "== Anki_Factory :: integrity =="; echo

echo "-- governance ambiguity: multiple versions of a protocol doc --"
ls AI_PIPELINE_RULES_OF_ENGAGEMENT_v*.md 2>/dev/null | sed 's/^/  /'
n=$(ls AI_PIPELINE_RULES_OF_ENGAGEMENT_v*.md 2>/dev/null | wc -l)
if [ "$n" -gt 1 ]; then
  echo "  ⚠️  $n versions present. CLAUDE.md cites v2.1."
  echo "      A superseded protocol doc sitting beside the live one is a"
  echo "      live ambiguity in the governance layer — archive or delete."
fi
echo

echo "-- .bak files (CLAUDE.md §IV calls these LEGACY) --"
c=$(find . -name '*.bak*' -not -path './.git/*' 2>/dev/null | wc -l)
echo "  $c found"
[ "$c" -gt 0 ] && find . -name '*.bak*' -not -path './.git/*' 2>/dev/null | head -15 | sed 's/^/    /'
[ "$c" -gt 0 ] && echo "    → git restore is the rollback path now; clean in one grouped commit"
echo

echo "-- root clutter --"
r=$(find . -maxdepth 1 -type f | wc -l)
echo "  $r files at repo root"
[ "$r" -gt 40 ] && echo "    ⚠️  every session's orientation pays for this"
echo "  run artefacts at root:"
ls CLAUDE_MANUAL_PHASE_*.txt forensic_raw_*.txt 2>/dev/null | wc -l | sed 's/^/    /'
echo "    → these belong in Archive/ or a runs/ folder"
echo

echo "-- CHANGELOG.md size --"
if [ -f CHANGELOG.md ]; then
  echo "  $(wc -l < CHANGELOG.md) lines / $(wc -c < CHANGELOG.md) bytes"
  b=$(wc -c < CHANGELOG.md)
  [ "$b" -gt 150000 ] && echo "    ⚠️  head -50 is a workaround for a file that outgrew its container."
  [ "$b" -gt 150000 ] && echo "       Consider CHANGELOG.md (current year) + CHANGELOG-ARCHIVE.md."
fi
echo

echo "-- always-loaded context size (global rule 12: adding requires removing) --"
for f in ".claude/preflight_check.txt" "CLAUDE.md" "$HOME/.claude/CLAUDE.md"; do
  [ -f "$f" ] && printf "  %-38s %4s lines\n" "$f" "$(wc -l < "$f")"
done
p=$(wc -l < .claude/preflight_check.txt 2>/dev/null || echo 0)
[ "$p" -gt 20 ] && echo "    ⚠️  preflight past its 20-line cap — a checklist long enough to skim has stopped firing"
echo

echo "-- workflow skill files tracked in git (CLAUDE.md §IV depends on this) --"
for f in scout design redteam surgeon commit compass telemetry medic shorts; do
  p=".claude/commands/$f.md"
  if [ ! -f "$p" ]; then echo "  MISSING FILE: $p"
  elif ! git ls-files --error-unmatch "$p" >/dev/null 2>&1; then echo "  UNTRACKED: $p"
  fi
done
for p in .claude/commands/*.md; do
  b=$(basename "$p" .md)
  case " scout design redteam surgeon commit compass telemetry medic shorts " in
    *" $b "*) ;;
    *) echo "  NOT IN THIS CHECK'S LIST: $p  (add it — a check cannot see what was never added to it)";;
  esac
done
[ -f .claude/preflight_check.txt ] && \
  { git ls-files --error-unmatch .claude/preflight_check.txt >/dev/null 2>&1 \
    || echo "  UNTRACKED: .claude/preflight_check.txt  (its loss would be invisible)"; }
echo "  ok"; echo

echo "-- files CLAUDE.md points at that don't exist --"
grep -ohE '`[A-Za-z0-9_./-]+\.(md|py|txt|json)`' CLAUDE.md 2>/dev/null \
  | tr -d '`' | sort -u | while read -r ref; do
      [ -e "$ref" ] && continue
      # illustrative examples and files that live outside the repo
      case "$ref" in foo.py|*feedback_workflow.md|memory/*) continue ;; esac
      find . -name "$(basename "$ref")" -not -path './.git/*' 2>/dev/null | grep -q . && continue
      echo "  MISSING: $ref"
    done
echo "  ok"; echo

echo "-- repo state (the §Session-Start Orientation check) --"
git status --short 2>/dev/null | head -15 | sed 's/^/  /'
echo "  --"
git log --oneline -3 2>/dev/null | sed 's/^/  /'
echo
echo "done."
