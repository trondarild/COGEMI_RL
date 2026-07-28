# tests/test_device_detection.py
"""Run the survey's detectDevice() against real user-agent strings.

The other survey tests read the source and check it says the right things.
This one executes it. Device class decides whether a participant's responses
came from a layout where the 5-point scale wrapped to two rows, so a silent
misclassification would quietly mix the two populations together.

Needs node, which the deploy script already requires. Skipped without it.
"""
import json
import pathlib
import re
import shutil
import subprocess

import pytest

ROUTER = pathlib.Path("cogemi/survey/appropriateness_survey_aspects_park_prolific_v2_roles.html")

# name, user agent, navigator.maxTouchPoints, expected class
CASES = [
    ("iPhone Safari",
     "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
     "Version/17.0 Mobile/15E148 Safari/604.1", 0, "mobile"),
    ("Android phone",
     "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 Chrome/120 "
     "Mobile Safari/537.36", 5, "mobile"),
    ("Android tablet",
     "Mozilla/5.0 (Linux; Android 13; SM-X700) AppleWebKit/537.36 Chrome/120 "
     "Safari/537.36", 5, "tablet"),
    ("iPad legacy UA",
     "Mozilla/5.0 (iPad; CPU OS 15_0 like Mac OS X) AppleWebKit/605.1.15 "
     "Version/15.0 Mobile/15E148 Safari/604.1", 5, "tablet"),
    # iPadOS 13+ presents itself as a Mac; only maxTouchPoints gives it away
    ("iPadOS 13+ desktop UA",
     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
     "Version/17.0 Safari/605.1.15", 5, "tablet"),
    ("macOS Safari",
     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
     "Version/17.0 Safari/605.1.15", 0, "desktop"),
    ("Windows Chrome",
     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 "
     "Safari/537.36", 0, "desktop"),
]

HARNESS = """
function classify(ua, touchPoints) {
  // Shadow navigator and window inside the function body: node 21+ defines a
  // read-only global navigator, so assigning to it would silently do nothing
  // and every case would come back "desktop".
  var body = "var navigator = {userAgent: UA, maxTouchPoints: TP};" +
             "var window = {innerWidth: 1024};" +
             "if (TP > 0) window.ontouchstart = null;" +
             SRC + "detectDevice(); return [DEVICE, VIEWPORT_W];";
  return new Function("UA", "TP", body)(ua, touchPoints);
}
console.log(JSON.stringify(CASES.map(function(c) { return classify(c[0], c[1]); })));
"""


@pytest.fixture(scope="module")
def classified():
    if shutil.which("node") is None:
        pytest.skip("node not installed")
    src = ROUTER.read_text(encoding="utf-8")
    fn = src[src.index("var DEVICE     = null;"):
             src.index("// ---", src.index("function detectDevice()"))]
    script = (f"var SRC = {json.dumps(fn)};\n"
              f"var CASES = {json.dumps([[ua, tp] for _, ua, tp, _ in CASES])};\n"
              + HARNESS)
    out = subprocess.run(["node", "-e", script], capture_output=True,
                         text=True, timeout=30)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout)


@pytest.mark.parametrize("i,case", enumerate(CASES), ids=[c[0] for c in CASES])
def test_device_class(i, case, classified):
    assert classified[i][0] == case[3], \
        f"{case[0]} classified as {classified[i][0]}, expected {case[3]}"


def test_viewport_width_is_captured(classified):
    for got in classified:
        assert got[1] == 1024, f"viewport width not read: {got[1]}"


def test_every_class_is_exercised():
    assert {c[3] for c in CASES} == {"mobile", "tablet", "desktop"}


def test_detection_has_no_browser_only_dependencies():
    """It must run before anything else on the page, so it cannot lean on the
    DOM — only navigator and window."""
    src = ROUTER.read_text(encoding="utf-8")
    body = src[src.index("function detectDevice()"):
               src.index("\n}", src.index("function detectDevice()"))]
    for forbidden in ("document.", "getElementById", "fetch("):
        assert forbidden not in body, f"detectDevice uses {forbidden}"
