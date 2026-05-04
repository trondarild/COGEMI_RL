// cogemi/survey/appropriateness_survey_ghpages.gs
// Google Apps Script backend for the COGEMI Social Appropriateness survey,
// adapted for use with a static frontend hosted on GitHub Pages.
//
// --- Deployment ---
// 1. Paste this file into a new Apps Script project (script.google.com).
// 2. Set SHEET_ID below to your Google Spreadsheet ID.
// 3. Deploy > New deployment > Web App
//      Execute as: Me
//      Who has access: Anyone
// 4. Copy the /exec URL into appropriateness_survey_ghpages.html as GAS_URL.
// 5. On re-deploy, always create a "New deployment" (not "Manage existing") to
//    get a stable URL that doesn't require token refresh.
//
// --- How it works ---
// All operations use doGet(e) with an `action` query parameter so that
// cross-origin requests work without a preflight (GAS redirects POST, breaking CORS).
//
//   ?action=scenarios&lang=en   → shuffled [{id, text}]
//   ?action=labels&lang=en      → [{value, label}]
//   ?action=submit&pid=...&sid=...&resp=...&age=...&gender=...&country=...&lang=...
//                               → {ok:true} or {ok:false, error:"..."}
//
// Output sheet columns:
//   timestamp | prolific_id | scenario_id | response | age | gender | country | language

var SHEET_ID   = "YOUR_SPREADSHEET_ID_HERE";
var SHEET_NAME = "responses";

// ---------------------------------------------------------------------------
// Scenario pool  { id, en, fr }
// ---------------------------------------------------------------------------

var SCENARIOS = [
  // --- cutinline ---
  { id: "sa_cutinline_supermarket",     en: "Someone walks past a queue of people and goes straight to the front at the supermarket checkout.", fr: "Quelqu'un dépasse la file et passe directement à la caisse du supermarché." },
  { id: "sa_cutinline_cinema",          en: "Someone pushes in front of others waiting to buy tickets at the cinema.", fr: "Quelqu'un s'insère devant les autres dans la file d'attente au cinéma." },
  { id: "sa_cutinline_busstop",         en: "Someone jumps the queue at a busy bus stop, boarding before people who have waited longer.", fr: "Quelqu'un grille la priorité à un arrêt de bus bondé." },
  { id: "sa_cutinline_emergency",       en: "Someone who is visibly unwell asks to move to the front of the queue at a pharmacy.", fr: "Une personne visiblement malade demande à passer devant dans la file d'attente à la pharmacie." },
  { id: "sa_cutinline_border",          en: "A traveller with a connecting flight in 20 minutes asks to move ahead in the passport control queue.", fr: "Un voyageur avec une correspondance dans 20 minutes demande à passer devant au contrôle des passeports." },
  // --- holdoor ---
  { id: "sa_holdoor_office",            en: "Someone holds the door open for a colleague directly behind them at the office entrance.", fr: "Quelqu'un tient la porte à un collègue juste derrière lui à l'entrée du bureau." },
  { id: "sa_holdoor_elevator",          en: "Someone holds the elevator for a person running toward it from across the lobby.", fr: "Quelqu'un retient l'ascenseur pour quelqu'un qui court depuis l'autre bout du hall." },
  { id: "sa_holdoor_shop",              en: "Someone holds the door open for a stranger carrying heavy shopping bags.", fr: "Quelqu'un tient la porte à un inconnu chargé de sacs de courses." },
  { id: "sa_holdoor_street",            en: "Someone holds a heavy gate open for a cyclist they don't know on the street.", fr: "Quelqu'un maintient un portail pour un cycliste inconnu dans la rue." },
  { id: "sa_holdoor_rain",              en: "Someone stands in the rain for a full minute holding a door because a person is still far away.", fr: "Quelqu'un reste sous la pluie pendant une minute entière à tenir la porte alors que la personne est encore loin." },
  // --- speakloud ---
  { id: "sa_speakloud_library",         en: "Someone takes a phone call and speaks at normal conversational volume in a quiet library.", fr: "Quelqu'un répond à un appel et parle normalement dans une bibliothèque silencieuse." },
  { id: "sa_speakloud_cafe",            en: "Someone has a loud, laughing conversation on their phone in a busy café.", fr: "Quelqu'un rit et parle fort au téléphone dans un café animé." },
  { id: "sa_speakloud_restaurant",      en: "Someone speaks so loudly on a call that nearby diners at a restaurant can hear every word.", fr: "Quelqu'un parle si fort au téléphone dans un restaurant que les clients voisins entendent tout." },
  { id: "sa_speakloud_cinema",          en: "Someone narrates the film to their companion in a normal speaking voice during a screening.", fr: "Quelqu'un commente le film à voix normale pendant une projection." },
  { id: "sa_speakloud_publictransport", en: "Someone listens to music without headphones on a busy commuter train.", fr: "Quelqu'un écoute de la musique sans écouteurs dans un train bondé." },
  // --- phonetable ---
  { id: "sa_phonetable_family_dinner",  en: "Someone scrolls through their phone throughout a family dinner without joining the conversation.", fr: "Quelqu'un fait défiler son téléphone tout au long d'un dîner de famille sans participer à la conversation." },
  { id: "sa_phonetable_date",           en: "Someone checks their phone several times while on a first date at a restaurant.", fr: "Quelqu'un vérifie son téléphone plusieurs fois lors d'un premier rendez-vous au restaurant." },
  { id: "sa_phonetable_meeting",        en: "Someone replies to messages on their phone during a work meeting.", fr: "Quelqu'un répond à des messages sur son téléphone pendant une réunion de travail." },
  { id: "sa_phonetable_funeral",        en: "Someone silently reads messages on their phone during a funeral reception.", fr: "Quelqu'un lit silencieusement des messages sur son téléphone lors d'une réception funèbre." },
  { id: "sa_phonetable_cafe",           en: "Someone places their phone face-up on the café table but does not look at it during a conversation.", fr: "Quelqu'un pose son téléphone face visible sur la table au café mais ne le regarde pas pendant la conversation." },
  // --- littering ---
  { id: "sa_littering_park",            en: "Someone drops an empty crisp packet on the ground in a public park.", fr: "Quelqu'un jette un paquet de chips vide par terre dans un parc public." },
  { id: "sa_littering_beach",           en: "Someone leaves their picnic rubbish on the beach when they leave.", fr: "Quelqu'un laisse ses déchets de pique-nique sur la plage en partant." },
  { id: "sa_littering_street",          en: "Someone drops a cigarette butt on the pavement rather than using a bin.", fr: "Quelqu'un jette un mégot sur le trottoir plutôt que de le mettre à la poubelle." },
  { id: "sa_littering_publictransport", en: "Someone leaves a newspaper on their seat when getting off the bus.", fr: "Quelqu'un laisse un journal sur son siège en descendant du bus." },
  { id: "sa_littering_forest",          en: "Someone buries their food waste in the forest while hiking and leaves no trace on the surface.", fr: "Quelqu'un enfouit ses déchets alimentaires dans la forêt pendant une randonnée sans laisser de trace en surface." },
  // --- ignoregreet ---
  { id: "sa_ignoregreet_office",        en: "A colleague says good morning and the person walks past without responding.", fr: "Un collègue dit bonjour et la personne passe sans répondre." },
  { id: "sa_ignoregreet_neighborhood",  en: "A neighbour waves hello and the person pretends not to see them.", fr: "Un voisin fait un signe de la main et la personne fait semblant de ne pas le voir." },
  { id: "sa_ignoregreet_gym",           en: "A regular gym acquaintance greets someone and they put their headphones on without acknowledging them.", fr: "Une connaissance habituelle de la salle de sport salue quelqu'un qui met ses écouteurs sans lui répondre." },
  { id: "sa_ignoregreet_elevator",      en: "Someone steps into an elevator, makes eye contact with another person already inside, and says nothing.", fr: "Quelqu'un entre dans un ascenseur, croise le regard de l'autre personne et ne dit rien." },
  { id: "sa_ignoregreet_party",         en: "A person at a party ignores someone who introduces themselves and turns away to talk to someone else.", fr: "Une personne à une fête ignore quelqu'un qui se présente et se retourne pour parler à quelqu'un d'autre." },
  // --- offerhelp ---
  { id: "sa_offerhelp_directions",      en: "Someone overhears a tourist looking confused and offers directions unprompted.", fr: "Quelqu'un entend un touriste perdu et lui propose spontanément de l'aider." },
  { id: "sa_offerhelp_grocerybags",     en: "Someone offers to carry an elderly person's heavy grocery bags to their car.", fr: "Quelqu'un propose de porter les lourds sacs de course d'une personne âgée jusqu'à sa voiture." },
  { id: "sa_offerhelp_door",            en: "Someone rushes ahead to open a door for a person in a wheelchair.", fr: "Quelqu'un se dépêche d'ouvrir une porte à une personne en fauteuil roulant." },
  { id: "sa_offerhelp_crying",          en: "A stranger sitting nearby is crying quietly; someone touches their arm and asks if they are okay.", fr: "Un inconnu assis à côté pleure silencieusement ; quelqu'un lui touche le bras et lui demande si ça va." },
  { id: "sa_offerhelp_fallen",          en: "Someone falls on the street and a passer-by immediately stops to help them up.", fr: "Quelqu'un tombe dans la rue et un passant s'arrête immédiatement pour l'aider à se relever." },
  // --- personalspace ---
  { id: "sa_personalspace_queue",       en: "Someone stands very close behind the person in front of them in a queue, almost touching.", fr: "Quelqu'un se tient très près derrière la personne devant lui dans une file, presque en contact." },
  { id: "sa_personalspace_elevator",    en: "Someone stands in the centre of an empty elevator, leaving only a small space for another person who enters.", fr: "Quelqu'un se place au centre d'un ascenseur vide, laissant peu de place à la personne qui entre." },
  { id: "sa_personalspace_emptybus",    en: "Someone chooses to sit directly next to a stranger on an otherwise empty bus.", fr: "Quelqu'un choisit de s'asseoir juste à côté d'un inconnu dans un bus autrement vide." },
  { id: "sa_personalspace_bench",       en: "Someone sits at the far end of a park bench to maintain distance from the only other person there.", fr: "Quelqu'un s'assoit à l'autre bout d'un banc de parc pour maintenir une distance avec l'autre personne." },
  { id: "sa_personalspace_waiting_room",en: "Someone sits directly next to a person in a waiting room when many other seats are available.", fr: "Quelqu'un s'assoit juste à côté d'une personne dans une salle d'attente alors que beaucoup d'autres sièges sont libres." }
];

var ATTENTION_CHECKS = [
  { id: "sa_check_appropriate",   en: "Someone holds the door open for the person directly behind them.", fr: "Quelqu'un tient la porte à la personne juste derrière lui." },
  { id: "sa_check_inappropriate", en: "Someone pushes past everyone waiting and barges to the front of the queue at a hospital reception.", fr: "Quelqu'un bouscule tout le monde et se place en tête de file à l'accueil d'un hôpital." }
];

var RESPONSE_LABELS = {
  en: ["Inappropriate", "Neutral", "Appropriate"],
  fr: ["Inapproprié",   "Neutre",  "Approprié"]
};
var RESPONSE_VALUES = ["Inappropriate", "Neutral", "Appropriate"];

// ---------------------------------------------------------------------------
// Web app entry point — all operations via GET with ?action=
// ---------------------------------------------------------------------------

function doGet(e) {
  var params = e && e.parameter ? e.parameter : {};
  var action = params.action || "";
  var lang   = params.lang   || "en";
  var result;

  if (action === "scenarios") {
    result = getScenariosForSession(lang);
  } else if (action === "labels") {
    result = getResponseLabels(lang);
  } else if (action === "submit") {
    result = submitResponse(
      params.pid    || "",
      params.sid    || "",
      params.resp   || "",
      params.age    || "",
      params.gender || "",
      params.country|| "",
      lang
    );
  } else {
    result = { ok: false, error: "Unknown action: " + action };
  }

  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

// ---------------------------------------------------------------------------
// Scenario / label helpers
// ---------------------------------------------------------------------------

function getScenariosForSession(language) {
  var pool = SCENARIOS.slice();
  for (var i = pool.length - 1; i > 0; i--) {
    var j = Math.floor(Math.random() * (i + 1));
    var tmp = pool[i]; pool[i] = pool[j]; pool[j] = tmp;
  }
  pool.splice(7,  0, ATTENTION_CHECKS[0]);
  pool.splice(17, 0, ATTENTION_CHECKS[1]);
  return pool.map(function(s) {
    return { id: s.id, text: language === "fr" ? s.fr : s.en };
  });
}

function getResponseLabels(lang) {
  var labels = RESPONSE_LABELS[lang] || RESPONSE_LABELS.en;
  return RESPONSE_VALUES.map(function(v, i) {
    return { value: v, label: labels[i] };
  });
}

// ---------------------------------------------------------------------------
// Submit a single response
// ---------------------------------------------------------------------------

function submitResponse(prolificId, scenarioId, response, age, gender, country, language) {
  if (!prolificId || !scenarioId || !response) {
    return { ok: false, error: "Missing required fields" };
  }
  try {
    var sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(SHEET_NAME);
    if (!sheet) return { ok: false, error: "Sheet '" + SHEET_NAME + "' not found" };
    sheet.appendRow([new Date(), prolificId, scenarioId, response, age, gender, country, language]);
    return { ok: true };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}

// ---------------------------------------------------------------------------
// Utility: export as COGEMI SurveyResponse objects (call from Apps Script editor)
// ---------------------------------------------------------------------------

function exportAsCogemiResponses() {
  var sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName(SHEET_NAME);
  var rows  = sheet.getDataRange().getValues();
  return rows.slice(1).map(function(r) {
    return { participant_id: r[1], scenario_id: r[2], response: r[3] };
  });
}
