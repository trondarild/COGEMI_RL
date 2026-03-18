// cogemi/survey/role_survey.gs
// Google Apps Script backend for the COGEMI Role-Indexed Justice survey.
//
// Deploy as a Web App (Execute as: Me; Who has access: Anyone).
// Set SHEET_ID to the ID of your Google Spreadsheet.
// The spreadsheet must have a sheet named "role_responses".
//
// Three Prolific study links, one per role perspective:
//   https://script.google.com/.../exec?role=agent
//   https://script.google.com/.../exec?role=target
//   https://script.google.com/.../exec?role=observer
//
// Output columns (appended per response):
//   timestamp | prolific_id | scenario_id | response | role_perspective |
//   agent_role | target_role | age | gender | country | language

var SHEET_ID = "YOUR_SPREADSHEET_ID_HERE";
var SHEET_NAME = "role_responses";

var SCENARIOS_PER_SESSION = 20;

// ---------------------------------------------------------------------------
// Scenario pool — mirrors cogemi/data/test_role_dataset.py
// { id, en, agent_role, target_role }
// id format: rj_{action}_{setting}  (ContextLearner: action=index1, state=index2)
// ---------------------------------------------------------------------------

var SCENARIOS = [
  // exploit
  {id:"rj_exploit_commission",  en:"An employer takes all sales commission earned by their employee.",              agent_role:"employer",    target_role:"salesperson"},
  {id:"rj_exploit_intern",      en:"A company uses unpaid interns for months of skilled work.",                     agent_role:"company",     target_role:"intern"},
  {id:"rj_exploit_franchise",   en:"A franchisor charges fees so high the franchisee cannot turn a profit.",        agent_role:"franchisor",  target_role:"franchisee"},
  {id:"rj_exploit_gig",         en:"A platform takes 40% of every payment earned by its gig workers.",             agent_role:"platform",    target_role:"gig worker"},
  {id:"rj_exploit_ideas",       en:"A manager presents a subordinate's idea as their own to senior leadership.",   agent_role:"manager",     target_role:"subordinate"},
  {id:"rj_exploit_overtime",    en:"A supervisor requires unpaid overtime without informing staff in advance.",     agent_role:"supervisor",  target_role:"employee"},
  {id:"rj_exploit_subcontract", en:"A contractor subcontracts work to labourers at a fraction of the billed rate.",agent_role:"contractor",  target_role:"labourer"},
  {id:"rj_exploit_tips",        en:"A restaurant owner keeps all tips collected by waiting staff.",                 agent_role:"owner",       target_role:"server"},
  {id:"rj_exploit_copyright",   en:"A record label takes full copyright of an artist's recordings by default.",    agent_role:"record label",target_role:"artist"},
  {id:"rj_exploit_bonus",       en:"A CEO cancels the performance bonuses of staff after they meet all targets.",  agent_role:"CEO",         target_role:"employee"},
  // deceive
  {id:"rj_deceive_investor",    en:"An entrepreneur overstates company revenue to secure investment.",              agent_role:"entrepreneur",target_role:"investor"},
  {id:"rj_deceive_patient",     en:"A doctor withholds a terminal diagnosis to avoid difficult conversations.",     agent_role:"doctor",      target_role:"patient"},
  {id:"rj_deceive_voter",       en:"A politician makes promises they have no intention of keeping.",                agent_role:"politician",  target_role:"voter"},
  {id:"rj_deceive_customer",    en:"A salesperson hides known defects when selling a used car.",                   agent_role:"salesperson", target_role:"customer"},
  {id:"rj_deceive_student",     en:"A teacher tells a struggling student they are progressing well to avoid conflict.",agent_role:"teacher", target_role:"student"},
  {id:"rj_deceive_spouse",      en:"A partner hides significant debt from their spouse during financial planning.", agent_role:"partner",     target_role:"spouse"},
  {id:"rj_deceive_tenant",      en:"A landlord misrepresents the state of the property to secure a rental.",       agent_role:"landlord",    target_role:"tenant"},
  {id:"rj_deceive_recruit",     en:"A recruiter exaggerates a job's salary and conditions to fill a vacancy.",     agent_role:"recruiter",   target_role:"candidate"},
  {id:"rj_deceive_client",      en:"A lawyer conceals a conflict of interest while representing a client.",        agent_role:"lawyer",      target_role:"client"},
  {id:"rj_deceive_public",      en:"A company hides environmental damage data from regulators and the public.",    agent_role:"company",     target_role:"public"},
  // coerce
  {id:"rj_coerce_worker",       en:"A factory owner threatens workers with dismissal if they unionise.",            agent_role:"owner",       target_role:"worker"},
  {id:"rj_coerce_debtor",       en:"A lender uses harassment and threats to collect a debt.",                      agent_role:"lender",      target_role:"debtor"},
  {id:"rj_coerce_witness",      en:"A defendant pressures a witness to change their testimony.",                   agent_role:"defendant",   target_role:"witness"},
  {id:"rj_coerce_employee",     en:"A manager pressures an employee to sign a non-compete under threat of firing.",agent_role:"manager",     target_role:"employee"},
  {id:"rj_coerce_tenant",       en:"A landlord threatens eviction to force a tenant to accept worse conditions.",  agent_role:"landlord",    target_role:"tenant"},
  {id:"rj_coerce_student",      en:"A professor withholds a grade to pressure a student into extra unpaid work.",  agent_role:"professor",   target_role:"student"},
  {id:"rj_coerce_patient",      en:"A caregiver uses emotional manipulation to control an elderly patient.",       agent_role:"caregiver",   target_role:"patient"},
  {id:"rj_coerce_partner",      en:"A person uses financial control to prevent their partner from leaving.",       agent_role:"controller",  target_role:"partner"},
  {id:"rj_coerce_supplier",     en:"A retailer demands suppliers cut prices or lose the contract.",                agent_role:"retailer",    target_role:"supplier"},
  {id:"rj_coerce_citizen",      en:"A government uses surveillance to deter citizens from political dissent.",     agent_role:"government",  target_role:"citizen"},
  // discriminate
  {id:"rj_discriminate_hire",   en:"An employer rejects a candidate solely because of their ethnic background.",   agent_role:"employer",    target_role:"candidate"},
  {id:"rj_discriminate_promote",en:"A manager overlooks a qualified woman for promotion in favour of a less experienced man.",agent_role:"manager",target_role:"employee"},
  {id:"rj_discriminate_serve",  en:"A shop owner refuses to serve a customer because of their religion.",          agent_role:"shopkeeper",  target_role:"customer"},
  {id:"rj_discriminate_seat",   en:"A restaurant seats guests of a certain race in a hidden corner.",              agent_role:"manager",     target_role:"guest"},
  {id:"rj_discriminate_lend",   en:"A bank charges higher interest rates to applicants from a specific postcode.", agent_role:"bank",        target_role:"applicant"},
  {id:"rj_discriminate_insure", en:"An insurer charges higher premiums based on the applicant's nationality.",    agent_role:"insurer",     target_role:"applicant"},
  {id:"rj_discriminate_rent",   en:"A landlord refuses to rent to a family with young children.",                  agent_role:"landlord",    target_role:"family"},
  {id:"rj_discriminate_admit",  en:"A university lowers admission standards for legacy applicants only.",          agent_role:"university",  target_role:"applicant"},
  {id:"rj_discriminate_pay",    en:"An employer pays workers of one gender less for identical work.",              agent_role:"employer",    target_role:"employee"},
  {id:"rj_discriminate_assign", en:"A teacher assigns the least desirable tasks to students from minority groups.",agent_role:"teacher",    target_role:"student"},
  // discipline
  {id:"rj_discipline_child",    en:"A parent grounds a teenager for coming home an hour late.",                    agent_role:"parent",      target_role:"teenager"},
  {id:"rj_discipline_employee", en:"A manager gives a written warning to a consistently late employee.",           agent_role:"manager",     target_role:"employee"},
  {id:"rj_discipline_student",  en:"A teacher detains a student for disrupting the class repeatedly.",             agent_role:"teacher",     target_role:"student"},
  {id:"rj_discipline_player",   en:"A coach drops a player from the team after they skip training without notice.",agent_role:"coach",      target_role:"player"},
  {id:"rj_discipline_soldier",  en:"An officer reprimands a soldier for failing to follow protocol.",              agent_role:"officer",     target_role:"soldier"},
  {id:"rj_discipline_prisoner", en:"A prison governor extends a prisoner's sentence for breaking facility rules.", agent_role:"governor",    target_role:"prisoner"},
  {id:"rj_discipline_trainee",  en:"A supervisor fails a trainee who did not meet the required standard.",         agent_role:"supervisor",  target_role:"trainee"},
  {id:"rj_discipline_member",   en:"A committee suspends a member who violated the code of conduct.",              agent_role:"committee",   target_role:"member"},
  {id:"rj_discipline_intern",   en:"A firm terminates an intern found sharing confidential documents externally.", agent_role:"firm",        target_role:"intern"},
  {id:"rj_discipline_subordinate",en:"A manager publicly criticises a subordinate's work in a team meeting.",     agent_role:"manager",     target_role:"subordinate"},
  // compete
  {id:"rj_compete_market",      en:"A supermarket chain opens a store next to a small independent grocer.",        agent_role:"chain",       target_role:"grocer"},
  {id:"rj_compete_election",    en:"A candidate runs a negative campaign targeting their opponent's record.",      agent_role:"candidate",   target_role:"opponent"},
  {id:"rj_compete_promotion",   en:"A colleague lobbies management intensively to be selected over a peer.",       agent_role:"colleague",   target_role:"peer"},
  {id:"rj_compete_scholarship", en:"A student applies for the same competitive scholarship as their close friend.",agent_role:"student",    target_role:"friend"},
  {id:"rj_compete_contract",    en:"A firm undercuts a rival's bid to win a government contract.",                 agent_role:"firm",        target_role:"rival"},
  {id:"rj_compete_grant",       en:"A researcher submits to the same funding call as a former collaborator.",      agent_role:"researcher",  target_role:"collaborator"},
  {id:"rj_compete_award",       en:"An artist submits to a prize knowing their mentor is also competing.",         agent_role:"artist",      target_role:"mentor"},
  {id:"rj_compete_position",    en:"A job applicant negotiates salary well above the advertised range.",           agent_role:"applicant",   target_role:"employer"},
  {id:"rj_compete_tender",      en:"A developer uses inside knowledge to outbid competitors on a project.",        agent_role:"developer",   target_role:"competitor"},
  {id:"rj_compete_prize",       en:"A sports team uses all legal tactics to prevent opponents from scoring.",      agent_role:"team",        target_role:"opponent"},
  // protect
  {id:"rj_protect_stranger",    en:"A bystander steps in when they see a stranger being harassed on the street.", agent_role:"bystander",   target_role:"stranger"},
  {id:"rj_protect_relative",    en:"A parent moves their child away from an abusive grandparent.",                agent_role:"parent",      target_role:"child"},
  {id:"rj_protect_bully",       en:"A teacher intervenes when a student is being bullied in the playground.",     agent_role:"teacher",     target_role:"student"},
  {id:"rj_protect_harassment",  en:"An employer disciplines a manager found harassing a junior colleague.",       agent_role:"employer",    target_role:"employee"},
  {id:"rj_protect_fraud",       en:"A bank flags and reverses an unauthorised transaction on a customer's account.",agent_role:"bank",      target_role:"customer"},
  {id:"rj_protect_medical",     en:"A paramedic performs emergency first aid on an unconscious pedestrian.",      agent_role:"paramedic",   target_role:"patient"},
  {id:"rj_protect_disaster",    en:"A rescue worker carries an injured person to safety during a flood.",         agent_role:"rescue worker",target_role:"survivor"},
  {id:"rj_protect_attack",      en:"A security guard physically defends a customer being attacked in a shop.",    agent_role:"guard",       target_role:"customer"},
  {id:"rj_protect_legal",       en:"A lawyer takes on a pro-bono case to protect a vulnerable person's rights.", agent_role:"lawyer",      target_role:"client"},
  {id:"rj_protect_domestic",    en:"A social worker removes a child from a home with documented abuse.",          agent_role:"social worker",target_role:"child"},
  // compensate
  {id:"rj_compensate_overtime", en:"An employer pays time-and-a-half for every overtime hour worked.",            agent_role:"employer",    target_role:"employee"},
  {id:"rj_compensate_danger",   en:"A company provides hazard pay to workers in high-risk environments.",         agent_role:"company",     target_role:"worker"},
  {id:"rj_compensate_achievement",en:"A manager awards a significant bonus to a team that exceeded targets.",     agent_role:"manager",     target_role:"team"},
  {id:"rj_compensate_loss",     en:"An insurance company pays full market value for a stolen vehicle.",           agent_role:"insurer",     target_role:"claimant"},
  {id:"rj_compensate_delay",    en:"An airline offers vouchers and hotel accommodation for a 12-hour delay.",     agent_role:"airline",     target_role:"passenger"},
  {id:"rj_compensate_effort",   en:"A client pays a freelancer extra for exceptional work delivered early.",      agent_role:"client",      target_role:"freelancer"},
  {id:"rj_compensate_skill",    en:"A firm raises salaries to match market rates after a benchmarking exercise.", agent_role:"firm",        target_role:"employee"},
  {id:"rj_compensate_loyalty",  en:"A company gives long-serving employees additional annual leave.",             agent_role:"company",     target_role:"employee"},
  {id:"rj_compensate_innovation",en:"An organisation pays royalties to an inventor for use of their patent.",    agent_role:"organisation",target_role:"inventor"},
  {id:"rj_compensate_sacrifice",en:"A government compensates families who lost members in a military conflict.",  agent_role:"government",  target_role:"family"},
  // advocate
  {id:"rj_advocate_rights",     en:"A lawyer publicly argues for the legal rights of a marginalised group.",      agent_role:"lawyer",      target_role:"community"},
  {id:"rj_advocate_raise",      en:"A manager argues to senior leadership that their team deserves a pay raise.", agent_role:"manager",     target_role:"team"},
  {id:"rj_advocate_promotion",  en:"A supervisor recommends a colleague for promotion based on merit.",           agent_role:"supervisor",  target_role:"colleague"},
  {id:"rj_advocate_asylum",     en:"A caseworker supports a refugee's asylum application with detailed evidence.",agent_role:"caseworker",  target_role:"refugee"},
  {id:"rj_advocate_release",    en:"A parole board member argues for early release of a rehabilitated prisoner.", agent_role:"board member",target_role:"prisoner"},
  {id:"rj_advocate_treatment",  en:"A nurse pushes back when a doctor dismisses a patient's reported symptoms.", agent_role:"nurse",       target_role:"patient"},
  {id:"rj_advocate_safety",     en:"A union representative raises health and safety concerns on behalf of staff.",agent_role:"rep",        target_role:"workers"},
  {id:"rj_advocate_recognition",en:"A professor credits a research assistant as co-author on a published paper.",agent_role:"professor",  target_role:"researcher"},
  {id:"rj_advocate_appeal",     en:"A lawyer files an appeal to overturn a wrongful conviction.",                 agent_role:"lawyer",      target_role:"client"},
  {id:"rj_advocate_parole",     en:"A social worker prepares a case for a juvenile offender's early release.",   agent_role:"social worker",target_role:"juvenile"},
  // assist
  {id:"rj_assist_groceries",    en:"A neighbour carries heavy shopping bags upstairs for an elderly resident.",   agent_role:"neighbour",   target_role:"resident"},
  {id:"rj_assist_directions",   en:"A local gives detailed directions to a lost tourist.",                        agent_role:"local",       target_role:"tourist"},
  {id:"rj_assist_stranded",     en:"A driver stops to help a motorist whose car has broken down on a motorway.", agent_role:"driver",      target_role:"motorist"},
  {id:"rj_assist_flooded",      en:"A volunteer sandbags a stranger's home during a flood emergency.",            agent_role:"volunteer",   target_role:"homeowner"},
  {id:"rj_assist_injured",      en:"A passer-by calls an ambulance and waits with an injured cyclist.",           agent_role:"passer-by",   target_role:"cyclist"},
  {id:"rj_assist_lost",         en:"A ranger guides a hiker who has strayed off-trail back to safety.",           agent_role:"ranger",      target_role:"hiker"},
  {id:"rj_assist_hungry",       en:"A charity worker distributes meals to people without homes.",                 agent_role:"charity worker",target_role:"recipient"},
  {id:"rj_assist_homeless",     en:"A citizen helps a rough sleeper find emergency shelter on a cold night.",     agent_role:"citizen",     target_role:"rough sleeper"},
  {id:"rj_assist_disabled",     en:"A commuter gives up their seat for a passenger with a visible disability.",  agent_role:"commuter",    target_role:"passenger"},
  {id:"rj_assist_elderly",      en:"A pharmacist helps an elderly customer understand their medication regimen.", agent_role:"pharmacist",  target_role:"patient"}
];

// Attention checks — obviously Just or Unjust from all three role perspectives
var ATTENTION_CHECKS = [
  {
    id: "rj_check_just",
    en: "A rescue worker carries an injured child to safety after a building collapse.",
    agent_role: "rescue worker", target_role: "child",
    expected: "Just"
  },
  {
    id: "rj_check_unjust",
    en: "A prison guard beats an unarmed prisoner without cause.",
    agent_role: "guard", target_role: "prisoner",
    expected: "Unjust"
  }
];

var RESPONSE_LABELS = {
  en: ["Unjust", "Neutral", "Just"],
  fr: ["Injuste", "Neutre", "Juste"]
};
var RESPONSE_VALUES = ["Unjust", "Neutral", "Just"];

// Role-specific question text
var ROLE_QUESTIONS = {
  agent: {
    en: "You are the {role}. How just is what you are doing?",
    fr: "Vous êtes {role}. Dans quelle mesure ce que vous faites est-il juste ?"
  },
  target: {
    en: "You are the {role}. How just is what is being done to you?",
    fr: "Vous êtes {role}. Dans quelle mesure ce qui vous est fait est-il juste ?"
  },
  observer: {
    en: "You are an observer. How just is the {agent}'s action toward the {target}?",
    fr: "Vous êtes un observateur. Dans quelle mesure l'action de {agent} envers {target} est-elle juste ?"
  }
};

// ---------------------------------------------------------------------------
// Web app entry point
// ---------------------------------------------------------------------------

function doGet(e) {
  var role = (e && e.parameter && e.parameter.role) ? e.parameter.role : null;
  return HtmlService.createHtmlOutputFromFile("role_survey")
    .setTitle("Justice Study")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
}

// ---------------------------------------------------------------------------
// Called by client
// ---------------------------------------------------------------------------

function getScenariosForSession(role, language) {
  var pool = SCENARIOS.slice();
  // Fisher-Yates shuffle
  for (var i = pool.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var tmp = pool[i]; pool[i] = pool[j]; pool[j] = tmp;
  }
  pool = pool.slice(0, SCENARIOS_PER_SESSION);
  // Insert attention checks at positions 5 and 14
  pool.splice(5,  0, ATTENTION_CHECKS[0]);
  pool.splice(14, 0, ATTENTION_CHECKS[1]);

  return pool.map(function(s) {
    return {
      id:          s.id,
      text:        s.en,
      agent_role:  s.agent_role,
      target_role: s.target_role,
      expected:    s.expected || null
    };
  });
}

function getResponseLabels(lang) {
  var labels = RESPONSE_LABELS[lang] || RESPONSE_LABELS.en;
  return RESPONSE_VALUES.map(function(v, i) {
    return { value: v, label: labels[i] };
  });
}

function submitResponse(prolificId, scenarioId, response, rolePerspective,
                        agentRole, targetRole, age, gender, country, language) {
  if (!prolificId || !scenarioId || !response) return { ok: false, error: "Missing fields" };
  var sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(SHEET_NAME);
  if (!sheet) return { ok: false, error: "Sheet not found" };
  sheet.appendRow([new Date(), prolificId, scenarioId, response, rolePerspective,
                   agentRole, targetRole, age, gender, country, language]);
  return { ok: true };
}
