# TODO generalise and read from data file, json or csv
function doGet() {
  return HtmlService.createHtmlOutputFromFile('index');
}


// Scene data with English & French translations
var groupA = [
  { id: "K_1_1", en: "A doctor honors a terminally ill patient’s decision to stop treatment.", fr: "Un médecin respecte la décision d’un patient en phase terminale d’arrêter le traitement." },
  { id: "K_1_3", en: "A parent refuses life-saving treatment for their child due to personal beliefs.", fr: "Un parent refuse un traitement vital pour son enfant en raison de ses convictions personnelles." },
  { id: "K_1_5", en: "A doctor honors a court-approved decision for the euthanasia of a patient in a vegetative state.", fr: "Un médecin respecte une décision approuvée par un tribunal concernant l'euthanasie d’un patient en état végétatif." },
  { id: "K_1_7", en: "A doctor performs euthanasia on an elderly person without clear directives.", fr: "Un médecin pratique l'euthanasie sur une personne âgée sans directives claires." },
  { id: "K_1_9", en: "A doctor assists in ending a life without consulting family or legal authorities.", fr: "Un médecin aide à mettre fin à une vie sans consulter la famille ni les autorités légales." },
  { id: "K_2_1", en: "A bodyguard kills an assassin to protect a political leader.", fr: "Un garde du corps tue un assassin pour protéger un leader politique." },
  { id: "K_2_3", en: "A police officer kills a protester throwing rocks to stop further unrest.", fr: "Un policier tue un manifestant lançant des pierres pour arrêter les troubles." },
  { id: "K_2_5", en: "A father kills an armed attacker to protect her child.", fr: "Un père tue un assaillant armé pour protéger son enfant." },
  { id: "K_2_7", en: "A father kills a man on the beach because he walked on his son’s sand castle.", fr: "Un père tue un homme sur la plage parce qu’il a marché sur le château de sable de son fils." },
  { id: "K_2_9", en: "A farmer shoots a stranger walking toward his barn late at night.", fr: "Un fermier tire sur un inconnu qui s'approche de sa grange tard dans la nuit." },
  { id: "D_1_1", en: "A doctor lies to a patient about their terminal diagnosis to keep their spirits high.", fr: "Un médecin ment à un patient sur son diagnostic terminal pour lui remonter le moral." },
  { id: "D_1_3", en: "A parent lies to their child, saying their pet went to live on a farm instead of telling them it died.", fr: "Un parent ment à son enfant en disant que leur animal est parti vivre à la ferme au lieu de dire qu’il est mort." },
  { id: "D_1_5", en: "A teacher lies to a struggling student, saying they are improving, to boost their confidence.", fr: "Un professeur ment à un étudiant en difficulté en lui disant qu’il progresse, pour renforcer sa confiance." },
  { id: "D_1_7", en: "A spy lies to an enemy agent to protect national security.", fr: "Un espion ment à un agent ennemi pour protéger la sécurité nationale." },
  { id: "D_1_9", en: "A coach tells a young athlete they were chosen for the team because of their skill, even though the real reason was to include them out of pity.", fr: "Un entraîneur dit à un jeune athlète qu’il a été sélectionné dans l’équipe grâce à ses compétences, alors qu’en réalité, c’était par pitié." },
  { id: "D_2_1", en: "A student lies to their professor about being sick to get extra time for an exam.", fr: "Un étudiant ment à son professeur en disant qu’il est malade pour obtenir plus de temps pour un examen." },
  { id: "D_2_3", en: "A scientist lies to a funding agency about their research results to secure a grant.", fr: "Un scientifique ment à une agence de financement sur ses résultats de recherche pour obtenir une subvention." },
  { id: "D_2_5", en: "A refugee lies about their identity to escape persecution and seek asylum in a safer country.", fr: "Un réfugié ment sur son identité pour échapper à la persécution et demander l’asile dans un pays plus sûr." },
  { id: "D_2_7", en: "A teen lies about their sexual orientation in a hostile environment.", fr: "Un adolescent ment sur son orientation sexuelle dans un environnement hostile." },
  { id: "D_2_9", en: "An artist claims their work is entirely original, even though it heavily plagiarizes another’s style and concept.", fr: "Un artiste prétend que son œuvre est entièrement originale, même si elle plagie largement le style et le concept d’un autre." },
  { id: "L_1_1", en: "A father steals food to feed his starving children, despite knowing theft is illegal.", fr: "Un père vole de la nourriture pour nourrir ses enfants affamés, bien qu’il sache que le vol est illégal." },
  { id: "L_1_3", en: "A protester steals supplies from a corporate warehouse during a riot, even though looting is prohibited.", fr: "Un manifestant vole des fournitures dans un entrepôt d’entreprise pendant une émeute, bien que le pillage soit interdit." },
  { id: "L_1_5", en: "A struggling artist steals software to create art without paying for expensive tools, even though piracy is against the law.", fr: "Un artiste en difficulté vole des logiciels pour créer de l’art sans payer d’outils coûteux, même si la piraterie est illégale." },
  { id: "L_1_7", en: "A kid steals candies at the bakery.", fr: "Un enfant vole des bonbons à la boulangerie." },
  { id: "L_1_9", en: "Group steals electronics from department store.", fr: "Un groupe vole des appareils électroniques dans un grand magasin." },
  { id: "L_2_1", en: "A radical group organizes a rally encouraging violence against minorities.", fr: "Un groupe radical organise un rassemblement incitant à la violence contre les minorités." },
  { id: "L_2_3", en: "An activist joins a demonstration for human rights, even though it is illegal.", fr: "Un activiste rejoint une manifestation pour les droits de l’homme, bien que ce soit illégal." },
  { id: "L_2_5", en: "A person joins an illegal demonstration that promotes hate speech.", fr: "Une personne rejoint une manifestation illégale qui promeut des discours haineux." },
  { id: "L_2_7", en: "A group of students participate in a climate march, defying local restrictions.", fr: "Un groupe d’étudiants participe à une marche pour le climat, défiant les restrictions locales." },
  { id: "L_2_9", en: "A labor leader organizes a strike against unfair wages despite legal risks.", fr: "Un leader syndical organise une grève contre les salaires injustes malgré les risques juridiques." }
];


var groupB = [
  { id: "K_1_2", en: "A doctor injects lethal drugs to someone who has lost consciousness.", fr: "Un médecin injecte des drogues létales à une personne ayant perdu connaissance." },
  { id: "K_1_4", en: "A doctor follows a legally valid living will authorizing euthanasia.", fr: "Un médecin suit une directive anticipée légalement valide autorisant l’euthanasie." },
  { id: "K_1_6", en: "A hospital adheres to guidelines for assisted dying in terminal cases.", fr: "Un hôpital respecte les directives relatives à l’aide médicale à mourir dans les cas terminaux." },
  { id: "K_1_8", en: "A nurse administers lethal drugs without proper legal oversight.", fr: "Une infirmière administre des drogues létales sans surveillance légale appropriée." },
  { id: "K_1_10", en: "A doctor performs euthanasia after the person asked for when being valid.", fr: "Un médecin pratique l’euthanasie après que la personne l’ait demandée lorsqu’elle était valide." },
  { id: "K_2_2", en: "A bodyguard kills an unarmed intruder approaching their client.", fr: "Un garde du corps tue un intrus non armé qui s’approche de son client." },
  { id: "K_2_4", en: "A police officer kills a hostage-taker to save innocent lives.", fr: "Un policier tue un preneur d’otages pour sauver des vies innocentes." },
  { id: "K_2_6", en: "A mother kills an armed attacker to protect her child.", fr: "Une mère tue un assaillant armé pour protéger son enfant." },
  { id: "K_2_8", en: "A teacher tackles and fatally stabs an armed student during a school shooting", fr: "Un professeur plaque et poignarde mortellement un élève armé lors d’une fusillade scolaire." },
  { id: "K_2_10", en: "A nightclub bouncer kills a man who loudly threatens to 'burn this place down' after being denied entry.", fr: "Un videur de boîte de nuit tue un homme qui menace bruyamment de « brûler cet endroit » après s’être vu refuser l’entrée." },
  { id: "D_1_2", en: "A husband lies to his wife about losing his job to avoid worrying her.", fr: "Un mari ment à sa femme sur la perte de son emploi pour ne pas l’inquiéter." },
  { id: "D_1_4", en: "A mother lies about Santa Claus to her child.", fr: "Une mère ment à son enfant au sujet du Père Noël." },
  { id: "D_1_6", en: "A friend lies to someone about their appearance to spare their feelings.", fr: "Un ami ment à quelqu’un sur son apparence pour épargner ses sentiments." },
  { id: "D_1_8", en: "A psychiatrist tells a patient that their test results showed no signs of a disorder, even though they did.", fr: "Un psychiatre dit à un patient que ses résultats n’indiquent aucun trouble, même si ce n’est pas le cas." },
  { id: "D_1_10", en: "A nurse tells an elderly patient that their family is “just running late” every day, even though no one is visiting", fr: "Une infirmière dit chaque jour à un patient âgé que sa famille est « juste en retard », alors que personne ne vient le voir." },
  { id: "D_2_2", en: "A politician lies to the public about their intentions to gain votes.", fr: "Un politicien ment au public sur ses intentions pour obtenir des voix." },
  { id: "D_2_4", en: "A lawyer lies to the court about evidence to ensure their client is acquitted.", fr: "Un avocat ment au tribunal sur des preuves pour faire acquitter son client." },
  { id: "D_2_6", en: "A woman lies to her abusive ex, saying she moved abroad.", fr: "Une femme ment à son ex violent en disant qu’elle a déménagé à l’étranger." },
  { id: "D_2_8", en: "A startup founder lies to investors about user growth metrics to secure funding and keep the company afloat.", fr: "Un fondateur de startup ment aux investisseurs sur les indicateurs de croissance des utilisateurs pour obtenir des financements et maintenir l’entreprise à flot." },
  { id: "D_2_10", en: "A person lies about having a disability to get special accommodations on a standardized test.", fr: "Une personne ment sur un handicap pour bénéficier d’aménagements particuliers à un examen standardisé." },
  { id: "L_1_2", en: "A wealthy executive steals money from their company’s pension fund, even though it’s a serious crime.", fr: "Un dirigeant riche vole de l’argent dans le fonds de pension de son entreprise, bien que ce soit un crime grave." },
  { id: "L_1_4", en: "A hacker steals personal data to expose government corruption, even though hacking is illegal.", fr: "Un hacker vole des données personnelles pour exposer la corruption gouvernementale, même si le piratage est illégal." },
  { id: "L_1_6", en: "A soldier steals medical supplies from enemy territory during wartime, even though wartime looting is banned.", fr: "Un soldat vole des fournitures médicales sur le territoire ennemi en temps de guerre, bien que le pillage soit interdit." },
  { id: "L_1_8", en: "A man steals his neighbor newspaper because his monthly subscription is over.", fr: "Un homme vole le journal de son voisin parce que son abonnement est terminé." },
  { id: "L_1_10", en: "Student steals food from neighbor's house.", fr: "Un étudiant vole de la nourriture chez son voisin." },
  { id: "L_2_2", en: "A student participates in a manifestation for the climate defying local interdiction.", fr: "Un étudiant participe à une manifestation pour le climat en défiant une interdiction locale." },
  { id: "L_2_4", en: "An extremist protest violently, ignoring the law.", fr: "Un extrémiste manifeste violemment, ignorant la loi." },
  { id: "L_2_6", en: "A citizen joins a peaceful protest against government corruption despite a ban.", fr: "Un citoyen rejoint une manifestation pacifique contre la corruption gouvernementale malgré une interdiction." },
  { id: "L_2_8", en: "A doctor leads a march for better healthcare policies despite the government's opposition.", fr: "Un médecin dirige une marche pour de meilleures politiques de santé malgré l’opposition du gouvernement." },
  { id: "L_2_10", en: "A business leader stages a protest against environmental regulations for personal gain.", fr: "Un chef d’entreprise organise une manifestation contre les réglementations environnementales pour un gain personnel." }
];

var groupC = [
  {"id":"L_1_3", "en":"A protester steals supplies from a corporate warehouse during a riot, even though looting is prohibited.", "fr": "Un manifestant vole des fournitures dans un entrepôt d'entreprise pendant une émeute, bien que le pillage soit interdit." },
  {"id":"L_1_4", "en":"A hacker steals personal data to expose government corruption, even though hacking is illegal.", "fr": "Un hacker vole des données personnelles pour exposer la corruption gouvernementale, bien que le piratage soit illégal."},
  {"id" : "L_1_5", "en": "A struggling artist steals software to create art without paying for expensive tools, even though piracy is against the law.", "fr": "Un artiste en difficulté vole un logiciel pour créer de l'art sans payer pour des outils coûteux, bien que le piratage soit illégal."},
  {"id":"K_2_12", "en": "A bodyguard kills a protester who threw a rock at their client.", "fr": "Un garde du corps tue un manifestant qui a jeté une pierre sur son client." },
  {"id": "K_2_14", "en": "A bystander kills a robber threatening a cashier, unsure if the gun is real.", "fr": "Un passant tue un voleur menaçant un caissier, sans être sûr que l'arme est réelle."},
  {"id": "K_2_16", "en": "A child kills their father while protecting their mother from ongoing abuse.", "fr": "Un enfant tue son père pour protéger sa mère d’un abus continu."},
  {"id": "K_2_18", "en": "A dictator orders a journalist's death, claiming it protects national security.", "fr": "Un dictateur ordonne la mort d’un journaliste, affirmant que c’est pour protéger la sécurité nationale."},
  { "id": "L_1_9", "en": "Group steals electronics from department store.", "fr": "Un groupe vole des appareils électroniques dans un grand magasin." },
  { "id": "L_1_7", "en": "A kid steals candies at the bakery.", "fr": "Un enfant vole des bonbons à la boulangerie." },
  { "id": "L_1_50", "en": "An undocumented immigrant steals a fake ID to get a job.", "fr": "Un immigrant sans papiers vole une fausse pièce d'identité pour obtenir un emploi." },
  { "id": "L_1_49", "en": "An office worker steals a coworker’s lunch daily.", "fr": "Un employé de bureau vole quotidiennement le déjeuner d'un collègue." },
  { "id": "L_1_47", "en": "An artist copies designs from a mega-corporation and sells them independently.", "fr": "Un artiste copie des designs d'une méga-corporation et les vend indépendamment." },
  { "id": "L_1_45", "en": "A whistleblower steals documents to expose corporate wrongdoing.", "fr": "Un lanceur d'alerte vole des documents pour révéler des actes répréhensibles d'entreprise." },
  { "id": "L_1_43", "en": "A war nurse steals morphine from enemy supplies to ease the pain of wounded civilians left behind.", "fr": "Une infirmière de guerre vole de la morphine dans les fournitures ennemies pour soulager la douleur des civils blessés laissés pour compte." },
  { "id": "L_1_41", "en": "A teenager shoplifts a video game for fun, despite having money.", "fr": "Un adolescent vole un jeu vidéo pour s'amuser, malgré qu'il ait de l'argent." },
  { "id": "L_1_40", "en": "A teacher steals extra school lunches from the cafeteria to secretly feed a chronically hungry student.", "fr": "Un enseignant vole des repas supplémentaires à la cafétéria pour nourrir secrètement un élève chroniquement affamé." },
  { "id": "L_1_39", "en": "A student steals exam answers after repeated academic failures and pressure from parents.", "fr": "Un étudiant vole des réponses d'examen après des échecs répétés et des pressions parentales." },
  { "id": "L_1_37", "en": "A social worker steals back a girl’s diary from an abusive foster home.", "fr": "Un travailleur social vole le journal intime d'une fille dans un foyer d'accueil abusif." },
  { "id": "L_1_35", "en": "A resistance fighter steals uniforms to infiltrate enemy territory.", "fr": "Un résistant vole des uniformes pour infiltrer le territoire ennemi." },
  { "id": "L_1_33", "en": "A rebel steals weapons from an oppressive regime.", "fr": "Un rebelle vole des armes à un régime oppressif." },
  { "id": "L_1_31", "en": "A prisoner steals a weapon from another inmate to avoid being attacked.", "fr": "Un prisonnier vole une arme à un autre détenu pour éviter d'être attaqué." },
  { "id": "L_1_29", "en": "A nurse steals donor blood from the hospital to give to her cousin, bypassing a long but fair waitlist.", "fr": "Une infirmière vole du sang de donneur à l'hôpital pour le donner à son cousin, contournant une liste d'attente longue mais équitable." },
  { "id": "L_1_27", "en": "A mother steals clothes for her children after losing her job.", "fr": "Une mère vole des vêtements pour ses enfants après avoir perdu son emploi." },
  { "id": "L_1_25", "en": "A medic steals a vaccine during an outbreak to save lives.", "fr": "Un médecin vole un vaccin pendant une épidémie pour sauver des vies." },
  { "id": "L_1_23", "en": "A man steals electricity from a streetlamp to charge his phone.", "fr": "Un homme vole de l'électricité à un lampadaire pour recharger son téléphone." },
  { "id": "L_1_21", "en": "A laid-off worker steals tools from his old workplace to start freelancing.", "fr": "Un travailleur licencié vole des outils de son ancien lieu de travail pour se lancer en freelance." },
  { "id": "L_1_19", "en": "A hacker steals financial data to donate it to victims of a scam.", "fr": "Un hacker vole des données financières pour les donner aux victimes d'une escroquerie." },
  { "id": "L_1_17", "en": "A farmer steals water from a neighbor during a drought to save his crops.", "fr": "Un agriculteur vole de l'eau à un voisin pendant une sécheresse pour sauver ses cultures." },
  { "id": "L_1_15", "en": "A delivery driver reroutes a shipment of insulin meant for a pharmacy to his friend’s dying mother.", "fr": "Un livreur redirige une livraison d'insuline destinée à une pharmacie vers la mère mourante de son ami." },
  { "id": "L_1_13", "en": "A biker takes a water bottle from an aid station not meant for their race.", "fr": "Un cycliste prend une bouteille d'eau d'un poste de ravitaillement qui n'est pas destiné à sa course." },
  { "id": "L_1_11", "en": "A babysitter steals cash from a child’s piggy bank.", "fr": "Une baby-sitter vole de l'argent dans la tirelire d'un enfant." },
  { "id": "L_1_1", "en": "A father steals food to feed his starving children, despite knowing theft is illegal.", "fr": "Un père vole de la nourriture pour nourrir ses enfants affamés, bien qu'il sache que c'est illégal." },
  { "id": "K_2_9", "en": "A farmer shoots a stranger walking toward his barn late at night.", "fr": "Un fermier tire sur un inconnu s’approchant de sa grange tard dans la nuit." },
  { "id": "K_2_7", "en": "A father kills a man on the beach because he walked on his son’s sand castle.", "fr": "Un père tue un homme sur la plage parce qu’il a marché sur le château de sable de son fils." },
  { "id": "K_2_50", "en": "A farmer kills a rabid dog attacking his livestock.", "fr": "Un fermier tue un chien enragé attaquant son bétail." },
  { "id": "K_2_48", "en": "An eco-terrorist kills a construction worker to protect a forest.", "fr": "Un éco-terroriste tue un ouvrier du bâtiment pour protéger une forêt." },
  { "id": "K_2_46", "en": "A woman kills her abusive ex-partner during a violent break-in.", "fr": "Une femme tue son ex-partenaire violent lors d’une effraction." },
  { "id": "K_2_44", "en": "A veteran kills a man trying to destroy a war memorial.", "fr": "Un vétéran tue un homme qui tentait de détruire un mémorial de guerre." },
  { "id": "K_2_42", "en": "A teacher kills a student with a gun during a school shooting — but the student had already surrendered.", "fr": "Un enseignant tue un élève armé pendant une fusillade — mais l’élève s’était déjà rendu." },
  { "id": "K_2_40", "en": "A son kills his father for inheritance, framing it as protecting the family from poverty.", "fr": "Un fils tue son père pour l’héritage, prétendant protéger la famille de la pauvreté." },
  { "id": "K_2_38", "en": "A settler kills a native person to “protect” their claimed land.", "fr": "Un colon tue un autochtone pour « protéger » ses terres revendiquées." },
  { "id": "K_2_36", "en": "A security guard kills a homeless man who refused to leave a supermarket entrance.", "fr": "Un agent de sécurité tue un sans-abri qui refuse de quitter l’entrée d’un supermarché." },
  { "id": "K_2_34", "en": "A resistance fighter kills a suspected traitor.", "fr": "Un résistant tue un traître présumé." },
  { "id": "K_2_32", "en": "A protester kills a violent policeman attacking another demonstrator.", "fr": "Un manifestant tue un policier violent attaquant un autre manifestant." },
  { "id": "K_2_30", "en": "A police officer shoots a gunman holding schoolchildren hostage.", "fr": "Un policier abat un tireur retenant des écoliers en otage." },
  { "id": "K_2_28", "en": "A mother kills an intruder threatening her child at knifepoint.", "fr": "Une mère tue un intrus menaçant son enfant avec un couteau." },
  { "id": "K_2_26", "en": "A mob boss kills a rival to “protect his family” from economic decline.", "fr": "Un parrain de la mafia tue un rival pour « protéger sa famille » d’un déclin économique." },
  { "id": "K_2_24", "en": "A husband kills his wife’s attacker, even though the attacker was retreating.", "fr": "Un mari tue l’agresseur de sa femme, bien que celui-ci battait en retraite." },
  { "id": "K_2_22", "en": "A hacker crashes a plane remotely to stop a biological weapon from being spread.", "fr": "Un hacker fait s’écraser un avion à distance pour empêcher la propagation d’une arme biologique." },
  { "id": "K_2_20", "en": "A drone pilot bombs a building to protect troops, knowing civilians may be inside.", "fr": "Un pilote de drone bombarde un bâtiment pour protéger des troupes, sachant que des civils..." }
]


var groupD = [
  {"id": "K_2_4", "en": "A police officer kills a hostage-taker to save innocent lives.", "fr": "Un policier tue un preneur d’otages pour sauver des vies innocentes."},
  {"id": "K_2_2", "en": "A bodyguard kills an unarmed intruder approaching their client.", "fr": "Un garde du corps tue un intrus non armé s’approchant de son client."},
  {"id": "K_2_6", "en": "A mother kills an armed attacker to protect her child.", "fr": "Une mère tue un agresseur armé pour protéger son enfant."},
  {"id": "L_1_6", "en": "A soldier steals medical supplies from enemy territory during wartime, even though wartime looting is banned.", "fr": "Un soldat vole des fournitures médicales en territoire ennemi pendant la guerre, bien que le pillage en temps de guerre soit interdit."},
  { "id": "L_1_10", "en": "A person steals a bike to catch a job interview on time.", "fr": "Une personne vole un vélo pour arriver à l’heure à un entretien d’embauche." },
  { "id": "L_1_8", "en": "A woman steals medicine she can’t afford for her sick baby.", "fr": "Une femme vole des médicaments qu’elle ne peut pas se permettre pour son bébé malade." },
  { "id": "L_1_48", "en": "A hacker steals student loan data to erase the debts of thousands.", "fr": "Un hacker vole des données de prêts étudiants pour effacer les dettes de milliers de personnes." },
  { "id": "L_1_46", "en": "A protester steals surveillance footage to reveal police misconduct.", "fr": "Un manifestant vole des images de surveillance pour révéler des fautes policières." },
  { "id": "L_1_44", "en": "A refugee steals a border guard’s radio to call for help for their family lost in the mountains.", "fr": "Un réfugié vole la radio d’un garde-frontière pour appeler à l’aide pour sa famille perdue dans la montagne." },
  { "id": "L_1_42", "en": "A teenager steals a laptop from a bully to erase humiliating photos.", "fr": "Un adolescent vole l’ordinateur portable d’un harceleur pour effacer des photos humiliantes." },
  { "id": "L_1_38", "en": "A woman steals money from a charity she works for to pay for her mother’s surgery.", "fr": "Une femme vole de l’argent à l’association caritative où elle travaille pour payer l’opération de sa mère." },
  { "id": "L_1_36", "en": "A poor student steals books for class because they can't afford them.", "fr": "Un étudiant pauvre vole des livres pour ses cours parce qu’il ne peut pas se les permettre." },
  { "id": "L_1_34", "en": "A man steals spare change from a church donation box to eat.", "fr": "Un homme vole de la monnaie dans une boîte de dons d’église pour manger." },
  { "id": "L_1_32", "en": "A hacker steals corporate secrets to leak them publicly.", "fr": "Un hacker vole des secrets d’entreprise pour les divulguer publiquement." },
  { "id": "L_1_30", "en": "A journalist steals a USB drive containing evidence of a cover-up.", "fr": "Un journaliste vole une clé USB contenant des preuves d’un scandale dissimulé." },
  { "id": "L_1_28", "en": "A young man steals train tickets to attend his sister’s wedding.", "fr": "Un jeune homme vole des billets de train pour assister au mariage de sa sœur." },
  { "id": "L_1_26", "en": "A homeless person steals a blanket from a store during winter.", "fr": "Un sans-abri vole une couverture dans un magasin en hiver." },
  { "id": "L_1_24", "en": "A woman steals baby formula from a pharmacy.", "fr": "Une femme vole du lait infantile à la pharmacie." },
  { "id": "L_1_22", "en": "An activist steals a flag from a fascist rally.", "fr": "Un activiste vole un drapeau lors d’un rassemblement fasciste." },
  { "id": "L_1_20", "en": "A child steals toys from a wealthier friend out of envy.", "fr": "Un enfant vole des jouets à un ami plus riche par envie." },
  { "id": "L_1_18", "en": "A widow steals a diamond ring from a rich socialite out of revenge.", "fr": "Une veuve vole une bague en diamant à une mondaine riche par vengeance." },
  { "id": "L_1_16", "en": "An elderly man steals a wheelchair from a hospital to help his wife.", "fr": "Un vieil homme vole un fauteuil roulant à l’hôpital pour aider sa femme." },
  { "id": "L_1_14", "en": "A delivery worker steals packages to resell them for rent money.", "fr": "Un livreur vole des colis pour les revendre et payer son loyer." },
  { "id": "L_1_12", "en": "A musician steals another band’s song and claims it as their own.", "fr": "Un musicien vole la chanson d’un autre groupe et la revendique comme sienne." },
  { "id": "L_1_2", "en": "A woman steals a coat from a department store to survive the winter.", "fr": "Une femme vole un manteau dans un grand magasin pour survivre à l’hiver." },
  { "id": "K_2_10", "en": "A general orders the bombing of a village to eliminate a terrorist leader hiding there.", "fr": "Un général ordonne le bombardement d’un village pour éliminer un chef terroriste qui s’y cache." },
  { "id": "K_2_8", "en": "A soldier kills an unarmed enemy who might reveal their location.", "fr": "Un soldat tue un ennemi non armé qui pourrait révéler leur position." },
  { "id": "K_2_49", "en": "A scientist euthanizes a test animal to prevent extreme suffering.", "fr": "Un scientifique euthanasie un animal de laboratoire pour éviter des souffrances extrêmes." },
  { "id": "K_2_47", "en": "A man kills a mugger in a dark alley to defend himself.", "fr": "Un homme tue un agresseur dans une ruelle sombre pour se défendre." },
  { "id": "K_2_45", "en": "A woman poisons her elderly husband suffering from a painful terminal illness.", "fr": "Une femme empoisonne son mari âgé atteint d’une maladie en phase terminale douloureuse." },
  { "id": "K_2_43", "en": "A warlord kills villagers who refused to join his army.", "fr": "Un chef de guerre tue des villageois qui ont refusé de rejoindre son armée." },
  { "id": "K_2_41", "en": "A business owner kills a burglar breaking in at night.", "fr": "Un commerçant tue un cambrioleur qui s’introduit chez lui la nuit." },
  { "id": "K_2_39", "en": "A cult leader orders a mass suicide to escape prosecution.", "fr": "Un gourou ordonne un suicide collectif pour échapper à la justice." },
  { "id": "K_2_37", "en": "A prison guard kills an inmate attempting escape.", "fr": "Un gardien de prison tue un détenu tentant de s’échapper." },
  { "id": "K_2_35", "en": "A soldier kills a fellow comrade to stop them from betraying the unit.", "fr": "Un soldat tue un camarade pour l’empêcher de trahir l’unité." },
  { "id": "K_2_33", "en": "A man kills a corrupt judge who freed his daughter’s rapist.", "fr": "Un homme tue un juge corrompu qui a libéré le violeur de sa fille." },
  { "id": "K_2_31", "en": "A prisoner kills a fellow inmate in self-defense.", "fr": "Un prisonnier tue un codétenu en état de légitime défense." },
  { "id": "K_2_29", "en": "A son kills his terminally ill father at his request.", "fr": "Un fils tue son père en phase terminale à sa demande." },
  { "id": "K_2_27", "en": "A child soldier kills an enemy commander under orders.", "fr": "Un enfant soldat tue un commandant ennemi sur ordre." },
  { "id": "K_2_25", "en": "A gang member kills a traitor to prove loyalty.", "fr": "Un membre de gang tue un traître pour prouver sa loyauté." },
  { "id": "K_2_23", "en": "A pilot crashes a hijacked plane into the ocean to prevent a larger terrorist attack.", "fr": "Un pilote fait s’écraser un avion détourné dans l’océan pour empêcher une attaque terroriste plus importante." },
  { "id": "K_2_21", "en": "A scientist kills a lab assistant who discovered illegal experiments.", "fr": "Un scientifique tue un assistant qui a découvert des expériences illégales." },
  { "id": "K_2_19", "en": "A father kills the drunk driver who killed his daughter.", "fr": "Un père tue le conducteur ivre qui a tué sa fille." },
  { "id": "K_2_17", "en": "A spy kills a colleague who was about to defect to the enemy.", "fr": "Un espion tue un collègue sur le point de passer à l’ennemi." },
  { "id": "K_2_15", "en": "A police officer kills a suspect running away unarmed.", "fr": "Un policier tue un suspect non armé en fuite." },
  { "id": "K_2_13", "en": "A revolutionary kills a king to overthrow a monarchy.", "fr": "Un révolutionnaire tue un roi pour renverser une monarchie." },
  { "id": "K_2_11", "en": "A hunter kills another hunter by mistake, thinking he was a deer.", "fr": "Un chasseur tue un autre chasseur par erreur, pensant qu’il s’agissait d’un cerf." },
  { "id": "K_2_5", "en": "A woman kills her rapist in the act.", "fr": "Une femme tue son violeur pendant l’acte." },
  { "id": "K_2_3", "en": "A woman drowns her baby to stop it from crying and revealing their hiding place.", "fr": "Une femme noie son bébé pour l’empêcher de pleurer et de révéler leur cachette." },
  { "id": "K_2_1", "en": "A man kills a wounded soldier to stop his suffering.", "fr": "Un homme tue un soldat blessé pour mettre fin à ses souffrances." }
]




// Function to return dilemmas from assigned group
function getScenesByGroup(group) {
  var selectedGroup = group === 'A' ? groupC : groupD;
  return selectedGroup.sort(() => Math.random() - 0.5); // Shuffle the order within the group
}

// Function to submit participant responses
function submitResponse(participantId, consent_given, response, sceneId, age, sex, nationality, assignedGroup) {
  if (!sceneId || !response || !age || !sex || !nationality || !assignedGroup) return;

  var sheet = SpreadsheetApp.openById(‘yourId’).getSheetByName('New_responses');
  var timestamp = new Date();
  sheet.appendRow([timestamp, participantId, consent_given, sceneId, response, age, sex, nationality, assignedGroup]);
}





