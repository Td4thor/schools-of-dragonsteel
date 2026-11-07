"""Rejects partial or misleading GameTest results.

Counts every @GameTest in src/gametest, then requires the server log to report that exactly that many
required tests passed, with no failure or crash markers. A green Gradle exit alone is not evidence.
It also requires every runtime mod the tests depend on to have loaded.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
log = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "build/gametest-run/logs/latest.log"
if not log.is_file():
    raise SystemExit(f"GameTest verification FAILED: no log at {log}")
text = log.read_text(encoding="utf-8", errors="replace")
expected = sum(len(re.findall(r"@GameTest\s*\(", p.read_text(encoding="utf-8")))
               for p in (ROOT / "src/gametest/java").rglob("*.java"))
passed = re.findall(r"All (\d+) required tests passed", text)
failures = [line for line in text.splitlines() if any(term in line for term in (
    "failed!", "required tests failed", "Game test server crashed", "Failed to load registries",
    "Exception in server tick loop", "Couldn't parse data file dragonsteel_schools",
    "Couldn't load tag dragonsteel_schools", "Parsing error loading recipe dragonsteel_schools"))]
missing = [mod for mod in ("iceandfire", "ice_and_fire_spellbooks", "grandsigil", "irons_spellbooks")
           if not re.search(rf"\[DragonsteelSchools/runtime\] loaded {mod}\b", text)]
if not expected or not passed or int(passed[-1]) != expected or failures or missing:
    raise SystemExit(f"GameTest verification FAILED: expected {expected}; markers={passed}; "
                     f"missing runtime mods={missing}.\n" + "\n".join(failures))
print(f"GameTest verification PASSED: all {expected} discovered required GameTests passed.")
