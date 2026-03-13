# cogemi/data/test_role_dataset.py
"""
Synthetic test dataset for role-indexed COGEMI scenarios.

Contains 10 actions × 10 settings = 100 scenarios, each with simulated
survey responses from three role perspectives (agent, target, observer).
Responses are seeded for reproducibility and tuned to reflect realistic
perspective divergence.

Judgment map (for HumanSurveyEvaluator):
    {"Unjust": -1, "Neutral": 0, "Just": 1}

Usage
-----
    from cogemi.data.test_role_dataset import load_test_role_dataset, JUDGMENT_MAP
    scenarios, responses = load_test_role_dataset()

Scenario ID format: ``rj_{action}_{setting}``
  - action: index 1 when split on "_" (used by ContextLearner)
  - setting: index 2 when split on "_"
"""

import random
from typing import List, Tuple

from cogemi.observe.scenario import Scenario
from cogemi.survey.survey_response import SurveyResponse

JUDGMENT_MAP = {"Unjust": -1, "Neutral": 0, "Just": 1}
ROLES = ("agent", "target", "observer")

# ---------------------------------------------------------------------------
# Action × setting definitions
# ---------------------------------------------------------------------------
# Each entry: (action_slug, setting_slug, description, agent_role, target_role)

_SCENARIOS_RAW = [
    # --- exploit (clearly unjust from target's view) ---
    ("exploit", "commission",   "An employer takes all sales commission earned by their employee.",              "employer",    "salesperson"),
    ("exploit", "intern",       "A company uses unpaid interns for months of skilled work.",                     "company",     "intern"),
    ("exploit", "franchise",    "A franchisor charges fees so high the franchisee cannot turn a profit.",        "franchisor",  "franchisee"),
    ("exploit", "gig",          "A platform takes 40% of every payment earned by its gig workers.",             "platform",    "gig worker"),
    ("exploit", "ideas",        "A manager presents a subordinate's idea as their own to senior leadership.",   "manager",     "subordinate"),
    ("exploit", "overtime",     "A supervisor requires unpaid overtime without informing staff in advance.",     "supervisor",  "employee"),
    ("exploit", "subcontract",  "A contractor subcontracts work to labourers at a fraction of the billed rate.","contractor",  "labourer"),
    ("exploit", "tips",         "A restaurant owner keeps all tips collected by waiting staff.",                 "owner",       "server"),
    ("exploit", "copyright",    "A record label takes full copyright of an artist's recordings by default.",    "record label","artist"),
    ("exploit", "bonus",        "A CEO cancels the performance bonuses of staff after they meet all targets.",  "CEO",         "employee"),

    # --- deceive (clearly unjust from target's view) ---
    ("deceive", "investor",     "An entrepreneur overstates company revenue to secure investment.",              "entrepreneur","investor"),
    ("deceive", "patient",      "A doctor withholds a terminal diagnosis to avoid difficult conversations.",     "doctor",      "patient"),
    ("deceive", "voter",        "A politician makes promises they have no intention of keeping.",                "politician",  "voter"),
    ("deceive", "customer",     "A salesperson hides known defects when selling a used car.",                   "salesperson", "customer"),
    ("deceive", "student",      "A teacher tells a struggling student they are progressing well to avoid conflict.","teacher", "student"),
    ("deceive", "spouse",       "A partner hides significant debt from their spouse during financial planning.", "partner",     "spouse"),
    ("deceive", "tenant",       "A landlord misrepresents the state of the property to secure a rental.",       "landlord",    "tenant"),
    ("deceive", "recruit",      "A recruiter exaggerates a job's salary and conditions to fill a vacancy.",     "recruiter",   "candidate"),
    ("deceive", "client",       "A lawyer conceals a conflict of interest while representing a client.",        "lawyer",      "client"),
    ("deceive", "public",       "A company hides environmental damage data from regulators and the public.",    "company",     "public"),

    # --- coerce (clearly unjust from target's view) ---
    ("coerce", "worker",        "A factory owner threatens workers with dismissal if they unionise.",            "owner",       "worker"),
    ("coerce", "debtor",        "A lender uses harassment and threats to collect a debt.",                      "lender",      "debtor"),
    ("coerce", "witness",       "A defendant pressures a witness to change their testimony.",                   "defendant",   "witness"),
    ("coerce", "employee",      "A manager pressures an employee to sign a non-compete under threat of firing.","manager",     "employee"),
    ("coerce", "tenant",        "A landlord threatens eviction to force a tenant to accept worse conditions.",  "landlord",    "tenant"),
    ("coerce", "student",       "A professor withholds a grade to pressure a student into extra unpaid work.",  "professor",   "student"),
    ("coerce", "patient",       "A caregiver uses emotional manipulation to control an elderly patient.",       "caregiver",   "patient"),
    ("coerce", "partner",       "A person uses financial control to prevent their partner from leaving.",       "controller",  "partner"),
    ("coerce", "supplier",      "A retailer demands suppliers cut prices or lose the contract.",                "retailer",    "supplier"),
    ("coerce", "citizen",       "A government uses surveillance to deter citizens from political dissent.",     "government",  "citizen"),

    # --- discriminate (clearly unjust from target's view) ---
    ("discriminate", "hire",    "An employer rejects a candidate solely because of their ethnic background.",   "employer",    "candidate"),
    ("discriminate", "promote", "A manager overlooks a qualified woman for promotion in favour of a less experienced man.", "manager", "employee"),
    ("discriminate", "serve",   "A shop owner refuses to serve a customer because of their religion.",          "shopkeeper",  "customer"),
    ("discriminate", "seat",    "A restaurant seats guests of a certain race in a hidden corner.",              "manager",     "guest"),
    ("discriminate", "lend",    "A bank charges higher interest rates to applicants from a specific postcode.", "bank",        "applicant"),
    ("discriminate", "insure",  "An insurer charges higher premiums based on the applicant's nationality.",    "insurer",     "applicant"),
    ("discriminate", "rent",    "A landlord refuses to rent to a family with young children.",                  "landlord",    "family"),
    ("discriminate", "admit",   "A university lowers admission standards for legacy applicants only.",          "university",  "applicant"),
    ("discriminate", "pay",     "An employer pays workers of one gender less for identical work.",              "employer",    "employee"),
    ("discriminate", "assign",  "A teacher assigns the least desirable tasks to students from minority groups.","teacher",    "student"),

    # --- discipline (ambiguous: legitimate authority vs. disproportionate punishment) ---
    ("discipline", "child",     "A parent grounds a teenager for coming home an hour late.",                    "parent",      "teenager"),
    ("discipline", "employee",  "A manager gives a written warning to a consistently late employee.",           "manager",     "employee"),
    ("discipline", "student",   "A teacher detains a student for disrupting the class repeatedly.",             "teacher",     "student"),
    ("discipline", "player",    "A coach drops a player from the team after they skip training without notice.","coach",       "player"),
    ("discipline", "soldier",   "An officer reprimands a soldier for failing to follow protocol.",              "officer",     "soldier"),
    ("discipline", "prisoner",  "A prison governor extends a prisoner's sentence for breaking facility rules.", "governor",    "prisoner"),
    ("discipline", "trainee",   "A supervisor fails a trainee who did not meet the required standard.",         "supervisor",  "trainee"),
    ("discipline", "member",    "A committee suspends a member who violated the code of conduct.",              "committee",   "member"),
    ("discipline", "intern",    "A firm terminates an intern found sharing confidential documents externally.", "firm",        "intern"),
    ("discipline", "subordinate","A manager publicly criticises a subordinate's work in a team meeting.",      "manager",     "subordinate"),

    # --- compete (ambiguous: fair rivalry vs. undermining another) ---
    ("compete", "market",       "A supermarket chain opens a store next to a small independent grocer.",        "chain",       "grocer"),
    ("compete", "election",     "A candidate runs a negative campaign targeting their opponent's record.",      "candidate",   "opponent"),
    ("compete", "promotion",    "A colleague lobbies management intensively to be selected over a peer.",       "colleague",   "peer"),
    ("compete", "scholarship",  "A student applies for the same competitive scholarship as their close friend.","student",     "friend"),
    ("compete", "contract",     "A firm undercuts a rival's bid to win a government contract.",                 "firm",        "rival"),
    ("compete", "grant",        "A researcher submits to the same funding call as a former collaborator.",      "researcher",  "collaborator"),
    ("compete", "award",        "An artist submits to a prize knowing their mentor is also competing.",         "artist",      "mentor"),
    ("compete", "position",     "A job applicant negotiates salary well above the advertised range.",           "applicant",   "employer"),
    ("compete", "tender",       "A developer uses inside knowledge to outbid competitors on a project.",        "developer",   "competitor"),
    ("compete", "prize",        "A sports team uses all legal tactics to prevent opponents from scoring.",      "team",        "opponent"),

    # --- protect (clearly just from target's view) ---
    ("protect", "stranger",     "A bystander steps in when they see a stranger being harassed on the street.", "bystander",   "stranger"),
    ("protect", "relative",     "A parent moves their child away from an abusive grandparent.",                "parent",      "child"),
    ("protect", "bully",        "A teacher intervenes when a student is being bullied in the playground.",     "teacher",     "student"),
    ("protect", "harassment",   "An employer disciplines a manager found harassing a junior colleague.",       "employer",    "employee"),
    ("protect", "fraud",        "A bank flags and reverses an unauthorised transaction on a customer's account.","bank",      "customer"),
    ("protect", "medical",      "A paramedic performs emergency first aid on an unconscious pedestrian.",      "paramedic",   "patient"),
    ("protect", "disaster",     "A rescue worker carries an injured person to safety during a flood.",         "rescue worker","survivor"),
    ("protect", "attack",       "A security guard physically defends a customer being attacked in a shop.",    "guard",       "customer"),
    ("protect", "legal",        "A lawyer takes on a pro-bono case to protect a vulnerable person's rights.", "lawyer",      "client"),
    ("protect", "domestic",     "A social worker removes a child from a home with documented abuse.",          "social worker","child"),

    # --- compensate (clearly just from target's view) ---
    ("compensate", "overtime",  "An employer pays time-and-a-half for every overtime hour worked.",            "employer",    "employee"),
    ("compensate", "danger",    "A company provides hazard pay to workers in high-risk environments.",         "company",     "worker"),
    ("compensate", "achievement","A manager awards a significant bonus to a team that exceeded targets.",      "manager",     "team"),
    ("compensate", "loss",      "An insurance company pays full market value for a stolen vehicle.",           "insurer",     "claimant"),
    ("compensate", "delay",     "An airline offers vouchers and hotel accommodation for a 12-hour delay.",     "airline",     "passenger"),
    ("compensate", "effort",    "A client pays a freelancer extra for exceptional work delivered early.",      "client",      "freelancer"),
    ("compensate", "skill",     "A firm raises salaries to match market rates after a benchmarking exercise.", "firm",        "employee"),
    ("compensate", "loyalty",   "A company gives long-serving employees additional annual leave.",             "company",     "employee"),
    ("compensate", "innovation","An organisation pays royalties to an inventor for use of their patent.",     "organisation","inventor"),
    ("compensate", "sacrifice", "A government compensates families who lost members in a military conflict.",  "government",  "family"),

    # --- advocate (clearly just from target's view) ---
    ("advocate", "rights",      "A lawyer publicly argues for the legal rights of a marginalised group.",      "lawyer",      "community"),
    ("advocate", "raise",       "A manager argues to senior leadership that their team deserves a pay raise.", "manager",     "team"),
    ("advocate", "promotion",   "A supervisor recommends a colleague for promotion based on merit.",           "supervisor",  "colleague"),
    ("advocate", "asylum",      "A caseworker supports a refugee's asylum application with detailed evidence.","caseworker",  "refugee"),
    ("advocate", "release",     "A parole board member argues for early release of a rehabilitated prisoner.", "board member","prisoner"),
    ("advocate", "treatment",   "A nurse pushes back when a doctor dismisses a patient's reported symptoms.", "nurse",       "patient"),
    ("advocate", "safety",      "A union representative raises health and safety concerns on behalf of staff.","rep",        "workers"),
    ("advocate", "recognition", "A professor credits a research assistant as co-author on a published paper.", "professor",   "researcher"),
    ("advocate", "appeal",      "A lawyer files an appeal to overturn a wrongful conviction.",                 "lawyer",      "client"),
    ("advocate", "parole",      "A social worker prepares a case for a juvenile offender's early release.",   "social worker","juvenile"),

    # --- assist (clearly just from target's view) ---
    ("assist", "groceries",     "A neighbour carries heavy shopping bags upstairs for an elderly resident.",   "neighbour",   "resident"),
    ("assist", "directions",    "A local gives detailed directions to a lost tourist.",                        "local",       "tourist"),
    ("assist", "stranded",      "A driver stops to help a motorist whose car has broken down on a motorway.", "driver",      "motorist"),
    ("assist", "flooded",       "A volunteer sandbags a stranger's home during a flood emergency.",            "volunteer",   "homeowner"),
    ("assist", "injured",       "A passer-by calls an ambulance and waits with an injured cyclist.",           "passer-by",   "cyclist"),
    ("assist", "lost",          "A ranger guides a hiker who has strayed off-trail back to safety.",           "ranger",      "hiker"),
    ("assist", "hungry",        "A charity worker distributes meals to people without homes.",                 "charity worker","recipient"),
    ("assist", "homeless",      "A citizen helps a rough sleeper find emergency shelter on a cold night.",     "citizen",     "rough sleeper"),
    ("assist", "disabled",      "A commuter gives up their seat for a passenger with a visible disability.",  "commuter",    "passenger"),
    ("assist", "elderly",       "A pharmacist helps an elderly customer understand their medication regimen.", "pharmacist",  "patient"),
]

# ---------------------------------------------------------------------------
# Response generation
# ---------------------------------------------------------------------------
# Probability distributions [p(Unjust), p(Neutral), p(Just)] per (action_type, role)

_RESPONSE_PROBS = {
    #                agent              target             observer
    "exploit":     ([0.05, 0.30, 0.65], [0.80, 0.15, 0.05], [0.75, 0.20, 0.05]),
    "deceive":     ([0.05, 0.25, 0.70], [0.75, 0.20, 0.05], [0.70, 0.25, 0.05]),
    "coerce":      ([0.05, 0.20, 0.75], [0.85, 0.10, 0.05], [0.80, 0.15, 0.05]),
    "discriminate":([0.05, 0.15, 0.80], [0.90, 0.08, 0.02], [0.85, 0.12, 0.03]),
    "discipline":  ([0.05, 0.20, 0.75], [0.35, 0.35, 0.30], [0.15, 0.40, 0.45]),
    "compete":     ([0.05, 0.20, 0.75], [0.30, 0.40, 0.30], [0.10, 0.45, 0.45]),
    "protect":     ([0.02, 0.10, 0.88], [0.02, 0.08, 0.90], [0.02, 0.08, 0.90]),
    "compensate":  ([0.02, 0.10, 0.88], [0.02, 0.08, 0.90], [0.02, 0.10, 0.88]),
    "advocate":    ([0.03, 0.12, 0.85], [0.02, 0.08, 0.90], [0.02, 0.10, 0.88]),
    "assist":      ([0.02, 0.08, 0.90], [0.01, 0.07, 0.92], [0.01, 0.07, 0.92]),
}

_LABELS = ["Unjust", "Neutral", "Just"]


def _sample_responses(
    scenario_id: str,
    action: str,
    n_per_role: int,
    rng: random.Random,
) -> List[SurveyResponse]:
    probs = _RESPONSE_PROBS.get(action, ([0.33, 0.34, 0.33],) * 3)
    responses = []
    for role_idx, role in enumerate(ROLES):
        p = probs[role_idx]
        for i in range(n_per_role):
            label = rng.choices(_LABELS, weights=p, k=1)[0]
            responses.append(SurveyResponse(
                participant_id=f"sim_{scenario_id}_{role}_{i}",
                scenario_id=scenario_id,
                response=label,
                role_perspective=role,
            ))
    return responses


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_test_role_dataset(
    n_responses_per_role: int = 8,
    seed: int = 42,
) -> Tuple[List[Scenario], List[SurveyResponse]]:
    """Return (scenarios, survey_responses) for the 100-scenario role dataset.

    Parameters
    ----------
    n_responses_per_role:
        Number of simulated responses per (scenario, role) triple.
        Default 8 gives stable distributions while keeping the dataset small.
    seed:
        Random seed for reproducibility.

    Returns
    -------
    scenarios:
        100 Scenario objects (10 actions × 10 settings).
        ID format: ``rj_{action}_{setting}``
    survey_responses:
        n_responses_per_role × 3 roles × 100 scenarios SurveyResponse objects.
    """
    rng = random.Random(seed)
    scenarios: List[Scenario] = []
    responses: List[SurveyResponse] = []

    for action, setting, description, agent_role, target_role in _SCENARIOS_RAW:
        scenario_id = f"rj_{action}_{setting}"
        scenario = Scenario(
            id=scenario_id,
            representation=description,
            anchors={"action": action, "setting": setting},
            roles={"agent": agent_role, "target": target_role},
            origin={"source": "test_role_dataset"},
        )
        scenarios.append(scenario)
        responses.extend(_sample_responses(scenario_id, action, n_responses_per_role, rng))

    return scenarios, responses


def action_names() -> List[str]:
    """Return the 10 action slugs in the dataset."""
    seen = []
    for action, *_ in _SCENARIOS_RAW:
        if action not in seen:
            seen.append(action)
    return seen
