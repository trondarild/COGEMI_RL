# tests/test_role_router_survey.py
"""
Structural tests for the single-study role-router survey:
  appropriateness_survey_aspects_park_prolific_v2_roles.html

This file supersedes the three per-arm files. It carries all three role
framings and draws the arm from claim_role() at entry, which is what makes
the arms disjoint: Prolific blocks a second submission to the same study,
whereas its "exclude previous participants" prescreener does not reliably
separate studies running at the same time.

Tests verify:
  - All three framings present, keyed by role, none hard-coded as the default
  - Role assignment happens before consent and is idempotent server-side
  - `role` reaches every row type: scenario, disagreement, completion
  - A single completion-code placeholder, no per-arm leftovers
  - The instrument itself is byte-identical to the agent arm outside the
    role-specific lines
  - The setup SQL declares the functions the page calls, with anon grants
"""
import re
import pathlib
import pytest

SURVEY_DIR = pathlib.Path("cogemi/survey")
ROUTER     = SURVEY_DIR / "appropriateness_survey_aspects_park_prolific_v2_roles.html"
AGENT_ARM  = SURVEY_DIR / "appropriateness_survey_aspects_park_prolific_v2_agent.html"
V2_BASE    = SURVEY_DIR / "appropriateness_survey_aspects_park_prolific_v2.html"
SETUP_SQL  = SURVEY_DIR / "appropriateness_survey_supabase_setup.sql"

ROLES = ["agent", "target", "observer"]


@pytest.fixture(scope="module")
def html():
    return ROUTER.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def sql():
    return SETUP_SQL.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# File exists and is labelled
# ---------------------------------------------------------------------------

def test_file_exists():
    assert ROUTER.exists(), f"Missing file: {ROUTER}"


def test_header_labels_it_as_the_router(html):
    assert "SINGLE-STUDY ROLE ROUTER" in html
    assert "supersedes the three separate arm files" in html


def test_title_does_not_advertise_a_role(html):
    title = re.search(r"<title>(.*?)</title>", html).group(1)
    assert title == "Social Appropriateness Study", title
    for role in ROLES:
        assert role.capitalize() + " Perspective" not in title


# ---------------------------------------------------------------------------
# Role framing table
# ---------------------------------------------------------------------------

EXPECTED_LABEL = {
    "agent":    "AGENT PERSPECTIVE",
    "target":   "TARGET PERSPECTIVE",
    "observer": "OBSERVER PERSPECTIVE",
}

EXPECTED_Q1 = {
    "agent":    "Imagining yourself as the person performing this action",
    "target":   "Imagining yourself as the person named under the situation",
    "observer": "Imagining yourself as an outside observer",
}

EXPECTED_Q2 = {
    "agent":    "in the same position (performing this action)",
    "target":   "in that position",
    "observer": "observing this situation",
}

EXPECTED_CONSENT = {
    "agent":    "the person performing the action",
    "target":   "the person on the receiving end of the action",
    "observer": "an outside observer watching the scene",
}


@pytest.mark.parametrize("role", ROLES)
def test_role_text_key_present(role, html):
    assert re.search(rf"^\s+{role}: \{{", html, re.M), \
        f"ROLE_TEXT has no '{role}' key"


@pytest.mark.parametrize("role", ROLES)
@pytest.mark.parametrize("table,name", [
    (EXPECTED_LABEL,   "phase label"),
    (EXPECTED_Q1,      "Q1 framing"),
    (EXPECTED_Q2,      "Q2 framing"),
    (EXPECTED_CONSENT, "consent framing"),
])
def test_all_role_framings_present(role, table, name, html):
    assert table[role] in html, f"{name} for '{role}' missing"


# The target framing was rewritten after the merge: the arm assumed every
# action has an addressee, which fails for the half of the pool that has none.
# Agent and observer must still match their arms verbatim.
UNCHANGED_FROM_ARMS = ["agent", "observer"]


def test_framings_carried_over_verbatim_from_the_arms():
    """Every framing string must match the arm file it came from, so the merge
    cannot have quietly reworded an arm."""
    router = ROUTER.read_text(encoding="utf-8")
    for role in UNCHANGED_FROM_ARMS:
        arm = (SURVEY_DIR / f"appropriateness_survey_aspects_park_prolific_v2_{role}.html")
        if not arm.exists():          # arms may be retired once the router ships
            pytest.skip(f"{arm.name} no longer present")
        arm_html = arm.read_text(encoding="utf-8")
        for table in (EXPECTED_LABEL, EXPECTED_Q1, EXPECTED_Q2, EXPECTED_CONSENT):
            assert table[role] in arm_html and table[role] in router


def test_target_framing_deliberately_differs_from_its_arm():
    """The one arm the merge was allowed to reword, and only in the two places
    that assumed an addressee."""
    arm = SURVEY_DIR / "appropriateness_survey_aspects_park_prolific_v2_target.html"
    if not arm.exists():
        pytest.skip(f"{arm.name} no longer present")
    arm_html = arm.read_text(encoding="utf-8")
    assert "Imagining yourself as the person this action is directed at" in arm_html
    assert EXPECTED_LABEL["target"] in arm_html
    assert EXPECTED_CONSENT["target"] in arm_html


def test_no_role_is_hard_coded(html):
    assert "var ROLE = null;" in html, "ROLE must start unassigned"
    for role in ROLES:
        assert f'var ROLE = "{role}"' not in html, \
            f"'{role}' is hard-coded — the router would not draw a role"


def test_unknown_role_from_server_is_rejected(html):
    assert 'if (!ROLE_TEXT[role]) throw new Error("unknown role: " + role);' in html


# ---------------------------------------------------------------------------
# Assignment flow
# ---------------------------------------------------------------------------

def test_role_claimed_before_consent(html):
    """Consent text is role-specific, so the claim must resolve first."""
    assert 'rpc("claim_role", { pid: PROLIFIC_PID })' in html
    assert 'applyRoleText(role);\n      show("page-consent");' in html
    # entry point must not jump straight to consent
    assert 'show(!PROLIFIC_PID ? "page-invalid" : "page-consent")' not in html


def test_missing_prolific_id_still_blocks(html):
    assert 'if (!PROLIFIC_PID) { show("page-invalid"); return; }' in html


def test_loading_and_error_pages_exist(html):
    for page in ("page-loading", "page-error"):
        assert f'id="{page}"' in html, f"{page} div missing"
    assert 'onclick="assignRole()"' in html, "no retry path on assignment failure"


def test_show_knows_every_page(html):
    listed = re.search(r'\[([^\]]*?)\]\.forEach\(function\(p\)', html).group(1)
    for page in ("page-invalid", "page-loading", "page-error",
                 "page-consent", "page-survey", "page-done"):
        assert f'"{page}"' in listed, f"show() would not hide {page}"


def test_rpc_helper_targets_postgrest(html):
    assert 'SUPABASE_URL + "/rest/v1/rpc/" + fn' in html


# ---------------------------------------------------------------------------
# role reaches every row type
# ---------------------------------------------------------------------------

def test_role_on_scenario_rows(html):
    assert "role:        ROLE" in html, "scenario base row lacks role"


def test_role_on_disagreement_row(html):
    block = re.search(r'norm_type:\s+"disagreement".*?\}', html, re.S).group(0)
    assert "role:" in block, "disagreement row lacks role"


def test_role_on_completion_row(html):
    block = re.search(r'scenario_id:\s+"__completion__".*?\}', html, re.S).group(0)
    assert "role:            ROLE" in block, "completion row lacks role"


def test_completion_releases_the_claim(html):
    assert 'rpc("complete_role", { pid: PROLIFIC_PID })' in html, \
        "completed participants would stay reclaimable by the pool sweep"


# ---------------------------------------------------------------------------
# Completion code
# ---------------------------------------------------------------------------

def test_one_completion_code_used_consistently(html):
    """Holds before and after set_completion_code_roles.sh runs: the redirect
    URL and the completion row must never disagree, or a participant is paid
    against a code the study does not recognise."""
    url_code = re.search(r'complete\?cc=([^"]+)"', html).group(1)
    const    = re.search(r'var COMPLETION_CODE\s*=\s*"([^"]+)"', html).group(1)
    assert url_code == const, f"redirect uses {url_code}, row writes {const}"
    assert html.count(const) == 2, \
        f"'{const}' should appear exactly twice, found {html.count(const)}"
    assert 'completion_code: COMPLETION_CODE' in html


def test_completion_code_is_unset_before_deployment(html):
    """Informational: fails once the code is patched in, which is expected."""
    if "ROLES_CC_PLACEHOLDER" not in html:
        pytest.skip("completion code already set — file is ready to deploy")
    assert html.count("ROLES_CC_PLACEHOLDER") == 2


def test_no_per_arm_completion_codes(html):
    for role in ROLES:
        assert f"{role.upper()}_CC_PLACEHOLDER" not in html


# ---------------------------------------------------------------------------
# Instrument unchanged by the merge
# ---------------------------------------------------------------------------

def _scenario_ids(text):
    return re.findall(r'\{ id:"([^"]+)"', text)


def test_scenario_pool_matches_v2_base():
    assert _scenario_ids(ROUTER.read_text(encoding="utf-8")) == \
           _scenario_ids(V2_BASE.read_text(encoding="utf-8"))


def test_scenario_pool_size():
    assert len(_scenario_ids(ROUTER.read_text(encoding="utf-8"))) == 42


def test_supabase_target_unchanged(html):
    base = V2_BASE.read_text(encoding="utf-8")
    assert re.search(r'var SUPABASE_URL\s*=\s*"([^"]+)"', html).group(1) == \
           re.search(r'var SUPABASE_URL\s*=\s*"([^"]+)"', base).group(1)
    assert "/rest/v1/responses_v2" in html


def test_scale_labels_unchanged(html):
    assert '"Strongly\\ninappropriate", "Inappropriate", "Neutral", "Appropriate", "Strongly\\nappropriate"' in html
    assert '"Rarely", "Sometimes", "Often"' in html


def _region(text, start, end):
    i = text.index(start)
    return text[i:text.index(end, i)]


# The parts of the instrument the merge was not allowed to touch. Anything
# that differs here means the merge changed what participants actually see or
# how their answers are recorded, not just the role framing.
INVARIANT_REGIONS = {
    "stylesheet":     ("<style>", "</style>"),
    "response scales":("var Q1_LABELS", "// ---"),
    "scenario data":  ("var SCENARIO_POOL", "// ---------------------------------------------------------------------------\n// State"),
    "session build":  ("function shuffle(arr)", "// ---------------------------------------------------------------------------\n// Supabase"),
    "phase machine":  ("function nextStep()", "function enterAspectPhase()"),
    "aspect ranking": ("function enterAspectPhase()", "// ---------------------------------------------------------------------------\n// Submit"),
}


# The router adds one stylesheet rule the arms never had: the target-arm
# anchor box. Removing it must leave the agent arm's stylesheet exactly.
ANCHOR_CSS = re.compile(
    r"\n +/\* Target arm only[^\n]*\n +\.target-anchor \{.*?\n +\}\n", re.S)


@pytest.mark.parametrize("name", list(INVARIANT_REGIONS))
def test_instrument_unchanged_by_the_merge(name):
    if not AGENT_ARM.exists():
        pytest.skip("agent arm no longer present")
    start, end = INVARIANT_REGIONS[name]
    router = _region(ROUTER.read_text(encoding="utf-8"), start, end)
    agent  = _region(AGENT_ARM.read_text(encoding="utf-8"), start, end)
    if name == "stylesheet":
        router, n = ANCHOR_CSS.subn("\n", router)
        assert n == 1, "target-anchor rule missing or no longer matched"
    assert router == agent, f"{name} differs between the agent arm and the router"


# ---------------------------------------------------------------------------
# Target anchors
#
# About half the pool has no addressee — nobody is on the receiving end of
# someone applying makeup or leaving litter. Each scenario therefore names one
# position for the target arm, tagged directed (the action is aimed at that
# person) or incidental (it merely lands on them).
# ---------------------------------------------------------------------------

def _anchors(text):
    block = _region(text, "var TARGET_ANCHORS = {", "\n};")
    return {
        m.group(1): (m.group(2), m.group(3) == "true")
        for m in re.finditer(
            r'(\w+):\s*\{ who:"([^"]+)",\s*directed:(true|false)\s*\}', block)
    }


def test_every_scenario_has_an_anchor(html):
    anchors = _anchors(html)
    missing = [i for i in _scenario_ids(html) if i not in anchors]
    assert not missing, f"no target anchor for: {missing}"


def test_no_anchor_without_a_scenario(html):
    ids = set(_scenario_ids(html))
    orphans = [k for k in _anchors(html) if k not in ids]
    assert not orphans, f"anchor for unknown scenario: {orphans}"


def test_anchors_name_a_person(html):
    for sid, (who, _) in _anchors(html).items():
        assert len(who) > 5, f"{sid}: anchor too thin to locate a position"
        assert not who.endswith("."), f"{sid}: anchor supplies its own full stop"


def test_both_directedness_levels_are_populated(html):
    directed = [d for _, d in _anchors(html).values()]
    assert directed.count(True) >= 8, "too few directed items to test within"
    assert directed.count(False) >= 8, "too few incidental items to test within"


def test_anchor_shown_only_in_the_target_arm(html):
    body = _region(html, "function renderTargetAnchor(s)", "\n}")
    assert 'ROLE !== "target"' in body, "anchor not gated on the target arm"
    assert 'classList.add("hidden")' in body, "no arm hides the anchor box"
    assert '<div class="target-anchor hidden" id="target-anchor">' in html, \
        "anchor box must start hidden so a stalled claim cannot leak it"
    assert "renderTargetAnchor(s)" in _region(
        html, "function renderScenario()", "\n}"), "anchor never rendered"


def test_target_framing_covers_incidental_items(html):
    target = _region(html, "target: {", "observer: {")
    assert "whether or not it is aimed at them" in target, \
        "target framing still assumes every action has an addressee"


def test_target_directed_posted_on_scenario_rows(html):
    submit = html[html.index("function submitScenario()"):]
    assert "target_directed: anchor ? anchor.directed : null" in submit, \
        "directedness not recorded per row"


def test_target_directed_column_declared(sql):
    assert "add column if not exists target_directed boolean" in sql


# ---------------------------------------------------------------------------
# Setup SQL backs the page
# ---------------------------------------------------------------------------

def test_role_assignments_table_declared(sql):
    assert "create table if not exists role_assignments" in sql
    assert "prolific_id  text primary key" in sql
    assert "check (role in ('agent','target','observer'))" in sql


@pytest.mark.parametrize("fn", ["claim_role", "complete_role",
                                "role_assignment_counts", "purge_smoketest_data"])
def test_function_declared_and_granted(fn, sql):
    assert f"create or replace function {fn}(" in sql, f"{fn} not declared"
    assert re.search(rf"grant execute on function {fn}\([^)]*\)\s+to anon", sql), \
        f"{fn} not granted to anon"


def test_claim_role_is_idempotent_and_serialised(sql):
    body = sql[sql.index("function claim_role("):sql.index("function complete_role(")]
    assert "select role into r from role_assignments where prolific_id = pid" in body
    assert "pg_advisory_xact_lock" in body, "concurrent claims could collide"
    assert body.count("select role into r from role_assignments where prolific_id = pid") == 2, \
        "must re-check membership after taking the lock"
    assert "order by count(ra.prolific_id)" in body, "not a least-filled draw"


def test_reclaim_only_touches_unfinished_claims(sql):
    body = sql[sql.index("function claim_role("):sql.index("function complete_role(")]
    delete = body[body.index("delete from role_assignments"):]
    assert "completed_at is null" in delete.split(";")[0]


def test_purge_prefix_is_not_a_parameter(sql):
    assert "create or replace function purge_smoketest_data()" in sql, \
        "purge must take no arguments, or anon could aim it at real rows"
    body = sql[sql.index("function purge_smoketest_data("):]
    assert body.count(r"like '\_\_smoketest\_\_%'") == 2


def test_rls_on_role_assignments(sql):
    assert "alter table role_assignments enable row level security;" in sql
    tail = sql[sql.index("create table if not exists role_assignments"):]
    assert "on role_assignments\n  for" not in tail, \
        "role_assignments must have no anon policy — access goes through the functions"


# ---------------------------------------------------------------------------
# Deployment protocol
# ---------------------------------------------------------------------------

DEPLOY = SURVEY_DIR / "deploy_to_pages.sh"


@pytest.fixture(scope="module")
def deploy():
    return DEPLOY.read_text(encoding="utf-8")


def _manifest(text):
    block = text[text.index("MANIFEST=("):text.index(")", text.index("MANIFEST=("))]
    return re.findall(r"^\s*(\S+\.html)", block, re.M)


def test_deploy_script_is_executable():
    assert DEPLOY.exists(), "no deploy script"
    assert DEPLOY.stat().st_mode & 0o111, "deploy script is not executable"


def test_router_is_in_the_manifest(deploy):
    assert ROUTER.name in _manifest(deploy)


def test_manifest_files_all_exist(deploy):
    for name in _manifest(deploy):
        assert (SURVEY_DIR / name).exists(), f"manifest lists a missing file: {name}"


def test_manifest_publishes_nothing_but_html(deploy):
    """The survey directory also holds pw.txt and the Supabase schema. An
    explicit manifest is what keeps them off a public site."""
    block = deploy[deploy.index("MANIFEST=("):deploy.index(")", deploy.index("MANIFEST=("))]
    listed = _manifest(deploy)
    assert listed, "manifest is empty"
    for name in listed:
        assert name.endswith(".html"), name
    for secret in ("pw.txt", "linktest.txt", "appropriateness_survey_supabase_setup.sql"):
        assert secret not in block, f"{secret} must never be deployed"


def test_superseded_arms_are_opt_in(deploy):
    """They still carry placeholders, so they would block every deploy if the
    default manifest listed them."""
    manifest = _manifest(deploy)
    for role in ROLES:
        arm = f"appropriateness_survey_aspects_park_prolific_v2_{role}.html"
        assert arm not in manifest, f"{arm} must not deploy by default"
        assert arm in deploy, f"{arm} should still be reachable with --only"
    assert "SUPERSEDED=(" in deploy
    assert 'for f in "${MANIFEST[@]}" "${SUPERSEDED[@]}"' in deploy


def test_deploy_refuses_placeholders(deploy):
    """The expensive failure: a live study redirecting to an invalid Prolific
    URL because the completion code was never filled in."""
    assert 'grep -q "_CC_PLACEHOLDER"' in deploy
    assert "exit 1" in deploy[deploy.index('grep -q "_CC_PLACEHOLDER"'):]


def test_deploy_runs_the_tests_before_pushing(deploy):
    assert "pytest" in deploy
    i_test, i_push = deploy.index("pytest"), deploy.index("git push")
    assert i_test < i_push, "tests must run before the push"


def test_deploy_confirms_before_publishing(deploy):
    assert "ASSUME_YES" in deploy and "read -r reply" in deploy
    assert "--dry-run" in deploy


def test_patch_scripts_do_not_publish():
    """Patching and publishing are separate steps, so the deploy checks
    cannot be bypassed by the convenience of a copy."""
    for name in ("set_completion_code_roles.sh", "set_completion_codes.sh"):
        text = (SURVEY_DIR / name).read_text(encoding="utf-8")
        assert "deploy_to_pages.sh" in text, f"{name} does not point at the deploy step"
        assert not re.search(r"^\s*cp .*PAGES", text, re.M), \
            f"{name} still copies to the pages repo"
        assert not re.search(r"^\s*git (add|commit|push)", text, re.M), \
            f"{name} still touches git"


def test_page_calls_only_granted_functions(html, sql):
    called = set(re.findall(r'rpc\("(\w+)"', html))
    for fn in called:
        assert re.search(rf"grant execute on function {fn}\([^)]*\)\s+to anon", sql), \
            f"page calls {fn}() but it is not granted to anon"
