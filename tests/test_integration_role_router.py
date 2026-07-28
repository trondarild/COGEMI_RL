# tests/test_integration_role_router.py
"""
Live integration tests for the role router against the pilot's Supabase
project. These exercise the path that actually spends money: if claim_role()
or the insert schema is wrong, participants hit a dead study.

Off by default — they write to the production table. Enable with:

    COGEMI_LIVE_SUPABASE=1 python -m pytest tests/test_integration_role_router.py -v

Every row written uses a prolific_id prefixed `__smoketest__`, and the module
calls purge_smoketest_data() on the way out. Real Prolific IDs are 24 hex
characters, so the purge can never reach participant data.

Safety guard: the balance test refuses to run once real participants have
claimed roles, because claiming 30 slots would distort a live draw.
"""
import json
import os
import re
import pathlib
import urllib.error
import urllib.request
import uuid

import pytest

LIVE = os.environ.get("COGEMI_LIVE_SUPABASE") == "1"
pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not LIVE, reason="set COGEMI_LIVE_SUPABASE=1 to run live tests"),
]

SURVEY = pathlib.Path("cogemi/survey/appropriateness_survey_aspects_park_prolific_v2_roles.html")
ROLES  = {"agent", "target", "observer"}
PREFIX = "__smoketest__"


def _config():
    """Read the endpoint and key from the survey page itself, so the tests
    exercise exactly what participants' browsers will use."""
    html = SURVEY.read_text(encoding="utf-8")
    url = re.search(r'var SUPABASE_URL\s*=\s*"([^"]+)"', html).group(1)
    key = re.search(r'var SUPABASE_ANON_KEY\s*=\s*"([^"]+)"', html).group(1)
    return url, key


SUPABASE_URL, ANON_KEY = _config() if SURVEY.exists() else ("", "")


def _post(path, payload, prefer=None):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(SUPABASE_URL + path, data=body, method="POST")
    req.add_header("apikey", ANON_KEY)
    req.add_header("Authorization", "Bearer " + ANON_KEY)
    req.add_header("Content-Type", "application/json")
    if prefer:
        req.add_header("Prefer", prefer)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        pytest.fail(f"{path} -> HTTP {e.code}: {e.read().decode()[:400]}")


def rpc(fn, **args):
    _, out = _post("/rest/v1/rpc/" + fn, args)
    return out


def insert(row):
    return _post("/rest/v1/responses_v2", row, prefer="return=minimal")[0]


def pid(tag=""):
    return f"{PREFIX}{tag}{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module", autouse=True)
def purge_around():
    rpc("purge_smoketest_data")
    yield
    rpc("purge_smoketest_data")


@pytest.fixture
def counts():
    return lambda: {r["role"]: r for r in rpc("role_assignment_counts")}


# ---------------------------------------------------------------------------
# claim_role
# ---------------------------------------------------------------------------

def test_claim_returns_a_known_role():
    assert rpc("claim_role", pid=pid()) in ROLES


def test_claim_is_idempotent():
    """A participant who reloads the page must not switch arms mid-study."""
    p = pid()
    first = rpc("claim_role", pid=p)
    assert all(rpc("claim_role", pid=p) == first for _ in range(4))


def test_claim_rejects_empty_id():
    with pytest.raises(Exception):
        req = urllib.request.Request(
            SUPABASE_URL + "/rest/v1/rpc/claim_role",
            data=json.dumps({"pid": ""}).encode(), method="POST")
        req.add_header("apikey", ANON_KEY)
        req.add_header("Authorization", "Bearer " + ANON_KEY)
        req.add_header("Content-Type", "application/json")
        urllib.request.urlopen(req, timeout=30)


def test_pool_draw_is_exactly_balanced(counts):
    """The point of the server-side draw: 30 entrants split 10/10/10, which a
    flat random assignment would not guarantee."""
    live = {r: c for r, c in counts().items() if c["claimed"] > c["smoketest"]}
    if live:
        pytest.skip(f"real participants already claimed roles: {live} — "
                    "would distort the live draw")

    rpc("purge_smoketest_data")   # start from an empty pool, not from earlier tests
    drawn = [rpc("claim_role", pid=pid("bal")) for _ in range(30)]
    per_role = {r: drawn.count(r) for r in ROLES}
    assert per_role == {"agent": 10, "target": 10, "observer": 10}, per_role


# ---------------------------------------------------------------------------
# complete_role
# ---------------------------------------------------------------------------

def test_complete_marks_the_claim(counts):
    p = pid("done")
    role = rpc("claim_role", pid=p)
    before = counts()[role]["completed"]
    rpc("complete_role", pid=p)
    assert counts()[role]["completed"] == before + 1


def test_complete_is_idempotent(counts):
    p = pid("done2")
    role = rpc("claim_role", pid=p)
    rpc("complete_role", pid=p)
    after_first = counts()[role]["completed"]
    rpc("complete_role", pid=p)
    assert counts()[role]["completed"] == after_first


# ---------------------------------------------------------------------------
# The rows the survey actually writes
# ---------------------------------------------------------------------------

def test_scenario_rows_insert(counts):
    p = pid("rows")
    role = rpc("claim_role", pid=p)
    base = {
        "prolific_id": p, "study_id": "smoke", "session_id": "smoke",
        "scenario_id": "yell_park_child", "language": "en",
        "aspect_ranking": "shouting loudly|a child playing|being in a public place",
        "is_repeat": False, "role": role, "target_directed": True,
    }
    for norm_type, response, value, extra in [
        ("personal",   "Appropriate", 4, {"confidence": 3}),
        ("injunctive", "Neutral",     3, {}),
        ("empirical",  "Often",       1, {}),
    ]:
        assert insert({**base, "norm_type": norm_type,
                       "response": response, "response_value": value, **extra}) in (201, 204)


def test_disagreement_row_carries_role():
    p = pid("disag")
    role = rpc("claim_role", pid=p)
    assert insert({
        "prolific_id": p, "study_id": "smoke", "session_id": "smoke",
        "scenario_id": "__disagreement_10__", "norm_type": "disagreement",
        "perceived_disagreement": 4, "language": "en", "role": role,
    }) in (201, 204)


def test_completion_row_carries_role_and_code():
    p = pid("compl")
    role = rpc("claim_role", pid=p)
    assert insert({
        "prolific_id": p, "study_id": "smoke", "session_id": "smoke",
        "scenario_id": "__completion__", "response": "completed",
        "completion_code": "SMOKETEST", "role": role,
    }) in (201, 204)


def test_unknown_column_is_rejected():
    """Guards the failure mode that would have burned the pilot: PostgREST
    rejects the whole insert when a posted field has no column."""
    body = json.dumps({"prolific_id": pid(), "no_such_column": 1}).encode()
    req = urllib.request.Request(SUPABASE_URL + "/rest/v1/responses_v2",
                                 data=body, method="POST")
    req.add_header("apikey", ANON_KEY)
    req.add_header("Authorization", "Bearer " + ANON_KEY)
    req.add_header("Content-Type", "application/json")
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req, timeout=30)
    assert exc.value.code == 400


def test_every_posted_field_has_a_column():
    """Each key the page posts must resolve, or the arm dies on scenario 1."""
    html = SURVEY.read_text(encoding="utf-8")
    # Only the row literals, i.e. from submitScenario onwards — the fetch
    # helpers above it have option keys ("method", "headers") that are not
    # columns.
    rows = html[html.index("function submitScenario()"):]
    fields = set(re.findall(r"^\s+(\w+):\s+\S", rows, re.M))
    assert {"prolific_id", "role", "norm_type", "completion_code",
            "perceived_disagreement", "is_repeat", "target_directed"} <= fields, fields

    for field in sorted(fields):
        url = f"{SUPABASE_URL}/rest/v1/responses_v2?select={field}&limit=1"
        req = urllib.request.Request(url)
        req.add_header("apikey", ANON_KEY)
        req.add_header("Authorization", "Bearer " + ANON_KEY)
        try:
            urllib.request.urlopen(req, timeout=30)
        except urllib.error.HTTPError as e:
            pytest.fail(f"column '{field}' missing from responses_v2: "
                        f"{e.read().decode()[:200]}")


# ---------------------------------------------------------------------------
# Cleanup works
# ---------------------------------------------------------------------------

def test_purge_removes_only_smoketest_rows(counts):
    real_before = {r: c["claimed"] - c["smoketest"] for r, c in counts().items()}

    rpc("claim_role", pid=pid("purge"))
    assert sum(c["smoketest"] for c in counts().values()) > 0

    rpc("purge_smoketest_data")
    after = counts()
    assert sum(c["smoketest"] for c in after.values()) == 0
    assert {r: c["claimed"] for r, c in after.items()} == real_before, \
        "purge removed rows it did not create"
