#!/usr/bin/env bash
# Dev client smoke test + armour showcase. Usage: bash tools/run_client_qa.sh [save folder to copy into run/saves/QA]
# Default source save: Tad's Dragonsteel Schools Test world. Screenshots land in run/screenshots.
set -u
cd "$(dirname "$0")/.."
SRC="${1:-C:/Users/owner/curseforge/minecraft/Instances/Dragonsteel Schools Test/saves/New World}"
rm -rf run/saves/QA run/screenshots run/crash-reports
mkdir -p run/saves && cp -r "$SRC" run/saves/QA && rm -f run/saves/QA/session.lock
export JAVA_HOME="C:/Users/owner/AppData/Local/hermes/cache/toolchains/jdk-17.0.20.1+1"
timeout 600 bash ./gradlew --no-daemon runClient -Pdsqa -PdsqaWorld=QA > build/qa-client.log 2>&1
code=$?
grep -E "qa\] DONE|Crash report|error:" build/qa-client.log
ls run/crash-reports 2>/dev/null && exit 1
grep -q "qa\] DONE" build/qa-client.log || { echo "QA did not finish (exit $code)"; exit 1; }
echo "QA OK: $(ls run/screenshots | wc -l) screenshots"
