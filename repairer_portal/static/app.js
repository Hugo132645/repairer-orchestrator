const loginView = document.querySelector("#login-view");
const portalView = document.querySelector("#portal-view");
const loginForm = document.querySelector("#login-form");
const chatForm = document.querySelector("#chat-form");
const messages = document.querySelector("#messages");
const input = document.querySelector("#message-input");
const newSessionButton = document.querySelector("#new-session");
const newSessionDialog = document.querySelector("#new-session-dialog");
const newSessionDialogTitle = newSessionDialog.querySelector("h2");
const newSessionDialogCopy = newSessionDialog.querySelector("p");
const newSessionDialogCancel = newSessionDialog.querySelector(".dialog-cancel");
const newSessionDialogConfirm = newSessionDialog.querySelector(".dialog-confirm");
const sendButton = chatForm.querySelector("button");
const repairOrdersView = document.querySelector("#repair-orders-view");
const serviceHistoryView = document.querySelector("#service-history-view");
const administrationView = document.querySelector("#administration-view");
const adminNav = document.querySelector("#admin-nav");
const viewEyebrow = document.querySelector("#view-eyebrow");
const viewTitle = document.querySelector("#view-title");
const loginLanguage = document.querySelector("#login-language");
const portalLanguage = document.querySelector("#portal-language");
const themeToggle = document.querySelector("#theme-toggle");
let requestInProgress = false;
let currentLanguage = "en";
let currentRole = "repairer";
let currentTheme = "tech";

function applyTheme(theme) {
  currentTheme = theme === "classic" ? "classic" : "tech";
  document.body.classList.toggle("theme-tech", currentTheme === "tech");
  themeToggle.textContent = currentTheme === "tech" ? "C" : "T";
  themeToggle.setAttribute(
    "aria-label",
    currentTheme === "tech" ? "Switch to classic theme" : "Switch to technology theme"
  );
  themeToggle.title = themeToggle.getAttribute("aria-label");
  try {
    window.localStorage.setItem("repairerPortalTheme", currentTheme);
  } catch {
    // Storage may be disabled; the theme still works until the page is closed.
  }
}

const translations = {
  en: {
    operations_workspace: "Repair operations workspace", clear_answers: "Clear answers.",
    connected_expertise: "Connected expertise.",
    brand_copy: "A multi-brand aftersales workspace connecting diagnostics, technical procedures, and parts availability.",
    local_environment: "Local prototype environment", synthetic_prototype: "Synthetic prototype",
    connected_services: "Connected services", diagnostics: "Diagnostics",
    service_library: "Service library", parts_inventory: "Parts inventory",
    demo_repairer: "Demo technician", assistant_name: "Workshop Assistant", you: "You",
    welcome_message: "Hello. I can coordinate synthetic diagnostics, technical procedures, and parts availability. Provide the vehicle model, market, diagnostic trouble code, and requested workshop task.",
    suggestion_diagnostic: "Assess P0301 for Demo Compact Hatchback in the EU",
    suggestion_procedure: "Find the P0301 procedure and ignition-coil availability",
    typing_message: "Validating the request and coordinating relevant services…",
    new_chat_message: "Hello. This is a new workshop conversation. Provide the vehicle model, market, diagnostic trouble code, and requested task.",
    secure_access: "Secure access", welcome_back: "Welcome back",
    sign_in_copy: "Sign in to open your repair desk.", username: "Username",
    password: "Password", language: "Language", enter_workspace: "Enter workspace",
    prototype_credentials: "Prototype credentials", assistant: "Assistant",
    repair_orders: "Repair orders", service_history: "Service history",
    log_out: "Log out", new_conversation: "New conversation",
    assistant_eyebrow: "AI workshop assistant", assistant_title: "What workshop task can I help with?",
    records_eyebrow: "Synthetic account records", request: "Request",
    view_response: "View assistant response", return_conversation: "Return to conversation",
    no_orders: "No synthetic repair orders yet",
    no_orders_copy: "A validated completed or partial chat request will appear here.",
    no_history: "No service history yet", no_history_copy: "Completed chat turns will appear here.",
    placeholder: "Describe the repair request…",
    synthetic_notice: "All responses are synthetic demonstration content, not repair authorization."
  },
  it: {
    operations_workspace: "Area operativa riparazioni", clear_answers: "Risposte chiare.",
    connected_expertise: "Competenze connesse.",
    brand_copy: "Uno spazio conversazionale che collega diagnostica, procedure e disponibilità sintetica dei ricambi.",
    local_environment: "Ambiente prototipo locale", synthetic_prototype: "Prototipo sintetico",
    connected_services: "Servizi connessi", diagnostics: "Diagnostica",
    service_library: "Libreria procedure", parts_inventory: "Inventario ricambi",
    demo_repairer: "Riparatore demo", assistant_name: "Assistente riparazioni", you: "Tu",
    welcome_message: "Ciao. Posso coordinare diagnostica sintetica, procedure di riparazione e disponibilità dei ricambi. Indicami il modello del veicolo, il codice guasto e cosa desideri controllare.",
    suggestion_diagnostic: "Valuta P0301 per Demo Compact Hatchback nell’UE",
    suggestion_procedure: "Trova una procedura e verifica la disponibilità della bobina",
    typing_message: "Convalida della richiesta e coordinamento dei servizi pertinenti…",
    new_chat_message: "Ciao. Questa è una nuova conversazione. Indicami il modello del veicolo, il codice guasto e cosa desideri controllare.",
    secure_access: "Accesso sicuro", welcome_back: "Bentornato",
    sign_in_copy: "Accedi per aprire la tua area riparazioni.", username: "Nome utente",
    password: "Password", language: "Lingua", enter_workspace: "Entra nell’area",
    prototype_credentials: "Credenziali del prototipo", assistant: "Assistente",
    repair_orders: "Ordini di riparazione", service_history: "Cronologia assistenza",
    log_out: "Esci", new_conversation: "Nuova conversazione",
    assistant_eyebrow: "Assistente IA per riparazioni", assistant_title: "Come posso aiutarti?",
    records_eyebrow: "Registri sintetici dell’account", request: "Richiesta",
    view_response: "Visualizza la risposta", return_conversation: "Torna alla conversazione",
    no_orders: "Nessun ordine di riparazione sintetico",
    no_orders_copy: "Una richiesta convalidata, completata o parziale, apparirà qui.",
    no_history: "Nessuna cronologia", no_history_copy: "Le chat completate appariranno qui.",
    placeholder: "Descrivi la richiesta di riparazione…",
    synthetic_notice: "Tutte le risposte sono contenuti sintetici e non autorizzano riparazioni."
  },
  de: {
    operations_workspace: "Arbeitsbereich Reparaturbetrieb", clear_answers: "Klare Antworten.",
    connected_expertise: "Vernetztes Fachwissen.",
    brand_copy: "Ein dialogbasierter Arbeitsbereich für Diagnose, Verfahren und synthetische Teileverfügbarkeit.",
    local_environment: "Lokale Prototypumgebung", synthetic_prototype: "Synthetischer Prototyp",
    connected_services: "Verbundene Dienste", diagnostics: "Diagnose",
    service_library: "Verfahrensbibliothek", parts_inventory: "Teilebestand",
    demo_repairer: "Demo-Reparateur", assistant_name: "Reparaturassistent", you: "Sie",
    welcome_message: "Hallo. Ich kann synthetische Diagnosen, Reparaturverfahren und Teileverfügbarkeit koordinieren. Nennen Sie Fahrzeugmodell, Fehlercode und die gewünschte Prüfung.",
    suggestion_diagnostic: "P0301 für Demo Compact Hatchback in der EU bewerten",
    suggestion_procedure: "Verfahren und Verfügbarkeit der Zündspule suchen",
    typing_message: "Anfrage wird validiert und relevante Dienste werden koordiniert…",
    new_chat_message: "Hallo. Dies ist eine neue Unterhaltung. Nennen Sie Fahrzeugmodell, Fehlercode und die gewünschte Prüfung.",
    secure_access: "Sicherer Zugang", welcome_back: "Willkommen zurück",
    sign_in_copy: "Melden Sie sich an, um den Reparaturbereich zu öffnen.",
    username: "Benutzername", password: "Passwort", language: "Sprache",
    enter_workspace: "Arbeitsbereich öffnen", prototype_credentials: "Prototyp-Zugangsdaten",
    assistant: "Assistent", repair_orders: "Reparaturaufträge",
    service_history: "Serviceverlauf", log_out: "Abmelden",
    new_conversation: "Neue Unterhaltung", assistant_eyebrow: "KI-Reparaturassistent",
    assistant_title: "Wie kann ich helfen?", records_eyebrow: "Synthetische Kontodaten",
    request: "Anfrage", view_response: "Antwort anzeigen",
    return_conversation: "Zur Unterhaltung zurückkehren",
    no_orders: "Noch keine synthetischen Reparaturaufträge",
    no_orders_copy: "Eine validierte vollständige oder teilweise Anfrage erscheint hier.",
    no_history: "Noch kein Serviceverlauf", no_history_copy: "Abgeschlossene Chats erscheinen hier.",
    placeholder: "Reparaturanfrage beschreiben…",
    synthetic_notice: "Alle Antworten sind synthetische Demoinhalte und keine Reparaturfreigabe."
  },
  fr: {
    operations_workspace: "Espace des opérations de réparation", clear_answers: "Des réponses claires.",
    connected_expertise: "Une expertise connectée.",
    brand_copy: "Un espace conversationnel reliant diagnostics, procédures et disponibilité synthétique des pièces.",
    local_environment: "Environnement prototype local", synthetic_prototype: "Prototype synthétique",
    connected_services: "Services connectés", diagnostics: "Diagnostic",
    service_library: "Bibliothèque de procédures", parts_inventory: "Stock de pièces",
    demo_repairer: "Réparateur démo", assistant_name: "Assistant de réparation", you: "Vous",
    welcome_message: "Bonjour. Je peux coordonner les diagnostics synthétiques, les procédures de réparation et la disponibilité des pièces. Indiquez le modèle, le code défaut et le contrôle souhaité.",
    suggestion_diagnostic: "Évaluer P0301 pour Demo Compact Hatchback dans l’UE",
    suggestion_procedure: "Trouver une procédure et vérifier la bobine d’allumage",
    typing_message: "Validation de la demande et coordination des services pertinents…",
    new_chat_message: "Bonjour. Ceci est une nouvelle conversation. Indiquez le modèle, le code défaut et le contrôle souhaité.",
    secure_access: "Accès sécurisé", welcome_back: "Bon retour",
    sign_in_copy: "Connectez-vous pour ouvrir votre espace de réparation.",
    username: "Nom d’utilisateur", password: "Mot de passe", language: "Langue",
    enter_workspace: "Ouvrir l’espace", prototype_credentials: "Identifiants du prototype",
    assistant: "Assistant", repair_orders: "Ordres de réparation",
    service_history: "Historique des services", log_out: "Se déconnecter",
    new_conversation: "Nouvelle conversation", assistant_eyebrow: "Assistant IA de réparation",
    assistant_title: "Comment puis-je vous aider ?", records_eyebrow: "Données synthétiques du compte",
    request: "Demande", view_response: "Voir la réponse",
    return_conversation: "Revenir à la conversation",
    no_orders: "Aucun ordre de réparation synthétique",
    no_orders_copy: "Une demande validée complète ou partielle apparaîtra ici.",
    no_history: "Aucun historique", no_history_copy: "Les conversations terminées apparaîtront ici.",
    placeholder: "Décrivez la demande de réparation…",
    synthetic_notice: "Toutes les réponses sont synthétiques et n’autorisent aucune réparation."
  },
  es: {
    operations_workspace: "Área de operaciones de reparación", clear_answers: "Respuestas claras.",
    connected_expertise: "Experiencia conectada.",
    brand_copy: "Un espacio conversacional que conecta diagnósticos, procedimientos y disponibilidad sintética de piezas.",
    local_environment: "Entorno de prototipo local", synthetic_prototype: "Prototipo sintético",
    connected_services: "Servicios conectados", diagnostics: "Diagnóstico",
    service_library: "Biblioteca de procedimientos", parts_inventory: "Inventario de piezas",
    demo_repairer: "Reparador de demostración", assistant_name: "Asistente de reparación", you: "Tú",
    welcome_message: "Hola. Puedo coordinar diagnósticos sintéticos, procedimientos de reparación y disponibilidad de piezas. Indica el modelo, el código de avería y qué deseas comprobar.",
    suggestion_diagnostic: "Evaluar P0301 para Demo Compact Hatchback en la UE",
    suggestion_procedure: "Buscar un procedimiento y disponibilidad de la bobina",
    typing_message: "Validando la solicitud y coordinando los servicios pertinentes…",
    new_chat_message: "Hola. Esta es una nueva conversación. Indica el modelo, el código de avería y qué deseas comprobar.",
    secure_access: "Acceso seguro", welcome_back: "Bienvenido de nuevo",
    sign_in_copy: "Inicia sesión para abrir tu espacio de reparación.",
    username: "Usuario", password: "Contraseña", language: "Idioma",
    enter_workspace: "Entrar al espacio", prototype_credentials: "Credenciales del prototipo",
    assistant: "Asistente", repair_orders: "Órdenes de reparación",
    service_history: "Historial de servicio", log_out: "Cerrar sesión",
    new_conversation: "Nueva conversación", assistant_eyebrow: "Asistente de reparación con IA",
    assistant_title: "¿Cómo puedo ayudarte?", records_eyebrow: "Registros sintéticos de la cuenta",
    request: "Solicitud", view_response: "Ver respuesta",
    return_conversation: "Volver a la conversación",
    no_orders: "No hay órdenes de reparación sintéticas",
    no_orders_copy: "Aquí aparecerá una solicitud validada completa o parcial.",
    no_history: "No hay historial", no_history_copy: "Las conversaciones completadas aparecerán aquí.",
    placeholder: "Describe la solicitud de reparación…",
    synthetic_notice: "Todas las respuestas son sintéticas y no autorizan reparaciones."
  },
  pl: {
    operations_workspace: "Obszar operacji naprawczych", clear_answers: "Jasne odpowiedzi.",
    connected_expertise: "Połączona wiedza.",
    brand_copy: "Konwersacyjny obszar łączący diagnostykę, procedury i syntetyczną dostępność części.",
    local_environment: "Lokalne środowisko prototypowe", synthetic_prototype: "Prototyp syntetyczny",
    connected_services: "Połączone usługi", diagnostics: "Diagnostyka",
    service_library: "Biblioteka procedur", parts_inventory: "Magazyn części",
    demo_repairer: "Mechanik demonstracyjny", assistant_name: "Asystent napraw", you: "Ty",
    welcome_message: "Dzień dobry. Mogę koordynować syntetyczną diagnostykę, procedury napraw i dostępność części. Podaj model pojazdu, kod usterki i zakres kontroli.",
    suggestion_diagnostic: "Oceń P0301 dla Demo Compact Hatchback w UE",
    suggestion_procedure: "Znajdź procedurę i sprawdź dostępność cewki zapłonowej",
    typing_message: "Walidacja zapytania i koordynowanie właściwych usług…",
    new_chat_message: "Dzień dobry. To nowa rozmowa. Podaj model pojazdu, kod usterki i zakres kontroli.",
    secure_access: "Bezpieczny dostęp", welcome_back: "Witamy ponownie",
    sign_in_copy: "Zaloguj się, aby otworzyć obszar napraw.", username: "Nazwa użytkownika",
    password: "Hasło", language: "Język", enter_workspace: "Otwórz obszar",
    prototype_credentials: "Dane logowania prototypu", assistant: "Asystent",
    repair_orders: "Zlecenia naprawy", service_history: "Historia serwisowa",
    log_out: "Wyloguj", new_conversation: "Nowa rozmowa",
    assistant_eyebrow: "Asystent napraw AI", assistant_title: "Jak mogę pomóc?",
    records_eyebrow: "Syntetyczne dane konta", request: "Zapytanie",
    view_response: "Pokaż odpowiedź", return_conversation: "Wróć do rozmowy",
    no_orders: "Brak syntetycznych zleceń naprawy",
    no_orders_copy: "Tutaj pojawi się zweryfikowane pełne lub częściowe zapytanie.",
    no_history: "Brak historii", no_history_copy: "Zakończone rozmowy pojawią się tutaj.",
    placeholder: "Opisz zapytanie dotyczące naprawy…",
    synthetic_notice: "Wszystkie odpowiedzi są syntetyczne i nie autoryzują napraw."
  },
  pt: {
    operations_workspace: "Área de operações de reparação", clear_answers: "Respostas claras.",
    connected_expertise: "Conhecimento ligado.",
    brand_copy: "Um espaço conversacional que liga diagnósticos, procedimentos e disponibilidade sintética de peças.",
    local_environment: "Ambiente de protótipo local", synthetic_prototype: "Protótipo sintético",
    connected_services: "Serviços ligados", diagnostics: "Diagnóstico",
    service_library: "Biblioteca de procedimentos", parts_inventory: "Inventário de peças",
    demo_repairer: "Reparador de demonstração", assistant_name: "Assistente de reparação", you: "Você",
    welcome_message: "Olá. Posso coordenar diagnósticos sintéticos, procedimentos de reparação e disponibilidade de peças. Indique o modelo, o código de avaria e o que pretende verificar.",
    suggestion_diagnostic: "Avaliar P0301 para Demo Compact Hatchback na UE",
    suggestion_procedure: "Encontrar um procedimento e verificar a bobina de ignição",
    typing_message: "A validar o pedido e a coordenar os serviços relevantes…",
    new_chat_message: "Olá. Esta é uma nova conversa. Indique o modelo, o código de avaria e o que pretende verificar.",
    secure_access: "Acesso seguro", welcome_back: "Bem-vindo de volta",
    sign_in_copy: "Inicie sessão para abrir a sua área de reparação.",
    username: "Nome de utilizador", password: "Palavra-passe", language: "Idioma",
    enter_workspace: "Entrar na área", prototype_credentials: "Credenciais do protótipo",
    assistant: "Assistente", repair_orders: "Ordens de reparação",
    service_history: "Histórico de serviço", log_out: "Terminar sessão",
    new_conversation: "Nova conversa", assistant_eyebrow: "Assistente de reparação com IA",
    assistant_title: "Como posso ajudar?", records_eyebrow: "Registos sintéticos da conta",
    request: "Pedido", view_response: "Ver resposta",
    return_conversation: "Voltar à conversa",
    no_orders: "Ainda não existem ordens de reparação sintéticas",
    no_orders_copy: "Um pedido validado completo ou parcial aparecerá aqui.",
    no_history: "Ainda não existe histórico", no_history_copy: "As conversas concluídas aparecerão aqui.",
    placeholder: "Descreva o pedido de reparação…",
    synthetic_notice: "Todas as respostas são sintéticas e não autorizam reparações."
  }
};

const dialogTranslations = {
  en: {
    title: "Start a new conversation?",
    copy: "The current conversation will be cleared from this prototype session. This cannot be undone.",
    cancel: "Keep conversation",
    confirm: "Start new conversation"
  },
  it: {
    title: "Avviare una nuova conversazione?",
    copy: "La conversazione attuale verrà rimossa da questa sessione del prototipo. L'operazione non può essere annullata.",
    cancel: "Mantieni la conversazione",
    confirm: "Avvia nuova conversazione"
  },
  de: {
    title: "Eine neue Unterhaltung beginnen?",
    copy: "Die aktuelle Unterhaltung wird aus dieser Prototyp-Sitzung entfernt. Dies kann nicht rückgängig gemacht werden.",
    cancel: "Unterhaltung behalten",
    confirm: "Neue Unterhaltung beginnen"
  },
  fr: {
    title: "Démarrer une nouvelle conversation ?",
    copy: "La conversation actuelle sera supprimée de cette session du prototype. Cette action est irréversible.",
    cancel: "Conserver la conversation",
    confirm: "Nouvelle conversation"
  },
  es: {
    title: "¿Iniciar una nueva conversación?",
    copy: "La conversación actual se eliminará de esta sesión del prototipo. Esta acción no se puede deshacer.",
    cancel: "Mantener conversación",
    confirm: "Iniciar nueva conversación"
  },
  pl: {
    title: "Rozpocząć nową rozmowę?",
    copy: "Bieżąca rozmowa zostanie usunięta z tej sesji prototypu. Tej operacji nie można cofnąć.",
    cancel: "Zachowaj rozmowę",
    confirm: "Rozpocznij nową rozmowę"
  },
  pt: {
    title: "Iniciar uma nova conversa?",
    copy: "A conversa atual será removida desta sessão do protótipo. Esta ação não pode ser anulada.",
    cancel: "Manter conversa",
    confirm: "Iniciar nova conversa"
  }
};

const adminTranslations = {
  en: {title: "Administration dashboard", eyebrow: "Prototype operations", model: "Configured model", calls: "LLM calls", tokens: "Tokens used", cost: "Estimated API cost", latency: "Average latency", uptime: "Portal uptime", activity: "Account activity", accounts: "Accounts", conversations: "Conversations", requests: "Service requests", orders: "Repair orders", health: "Service health", routing: "Protocol routing", users: "User profiles"},
  it: {title: "Dashboard amministrativa", eyebrow: "Operazioni del prototipo", model: "Modello configurato", calls: "Chiamate LLM", tokens: "Token utilizzati", cost: "Costo API stimato", latency: "Latenza media", uptime: "Attività del portale", activity: "Attività account", accounts: "Account", conversations: "Conversazioni", requests: "Richieste di servizio", orders: "Ordini di riparazione", health: "Stato dei servizi", routing: "Instradamento protocolli", users: "Profili utente"},
  de: {title: "Administrationsübersicht", eyebrow: "Prototypbetrieb", model: "Konfiguriertes Modell", calls: "LLM-Aufrufe", tokens: "Verwendete Token", cost: "Geschätzte API-Kosten", latency: "Mittlere Latenz", uptime: "Portal-Laufzeit", activity: "Kontoaktivität", accounts: "Konten", conversations: "Unterhaltungen", requests: "Serviceanfragen", orders: "Reparaturaufträge", health: "Dienststatus", routing: "Protokollrouting", users: "Benutzerprofile"},
  fr: {title: "Tableau de bord administrateur", eyebrow: "Exploitation du prototype", model: "Modèle configuré", calls: "Appels LLM", tokens: "Jetons utilisés", cost: "Coût API estimé", latency: "Latence moyenne", uptime: "Disponibilité du portail", activity: "Activité des comptes", accounts: "Comptes", conversations: "Conversations", requests: "Demandes de service", orders: "Ordres de réparation", health: "État des services", routing: "Routage des protocoles", users: "Profils utilisateurs"},
  es: {title: "Panel de administración", eyebrow: "Operaciones del prototipo", model: "Modelo configurado", calls: "Llamadas LLM", tokens: "Tokens utilizados", cost: "Coste API estimado", latency: "Latencia media", uptime: "Tiempo activo del portal", activity: "Actividad de cuentas", accounts: "Cuentas", conversations: "Conversaciones", requests: "Solicitudes de servicio", orders: "Órdenes de reparación", health: "Estado de servicios", routing: "Enrutamiento de protocolos", users: "Perfiles de usuario"},
  pl: {title: "Panel administratora", eyebrow: "Działanie prototypu", model: "Skonfigurowany model", calls: "Wywołania LLM", tokens: "Użyte tokeny", cost: "Szacowany koszt API", latency: "Średnie opóźnienie", uptime: "Czas działania portalu", activity: "Aktywność kont", accounts: "Konta", conversations: "Rozmowy", requests: "Żądania usług", orders: "Zlecenia naprawy", health: "Stan usług", routing: "Trasowanie protokołów", users: "Profile użytkowników"},
  pt: {title: "Painel de administração", eyebrow: "Operações do protótipo", model: "Modelo configurado", calls: "Chamadas LLM", tokens: "Tokens utilizados", cost: "Custo API estimado", latency: "Latência média", uptime: "Tempo ativo do portal", activity: "Atividade das contas", accounts: "Contas", conversations: "Conversas", requests: "Pedidos de serviço", orders: "Ordens de reparação", health: "Estado dos serviços", routing: "Encaminhamento de protocolos", users: "Perfis de utilizador"}
};

function adminText(key) {
  return adminTranslations[currentLanguage]?.[key] || adminTranslations.en[key] || key;
}

const usageChartTitles = {
  en: "Cumulative usage and estimated cost over time",
  it: "Utilizzo cumulativo e costo stimato nel tempo",
  de: "Kumulierte Nutzung und geschätzte Kosten im Zeitverlauf",
  fr: "Utilisation cumulée et coût estimé dans le temps",
  es: "Uso acumulado y coste estimado a lo largo del tiempo",
  pl: "Skumulowane użycie i szacowany koszt w czasie",
  pt: "Utilização acumulada e custo estimado ao longo do tempo"
};

const conversationSearchTranslations = {
  en: {title: "Conversation search", placeholder: "Search by user, words, fault code, or order reference", search: "Search", recent: "Recent conversations", no_matches: "No matching conversations found.", view: "View conversation", messages: "messages"},
  it: {title: "Ricerca conversazioni", placeholder: "Cerca per utente, parole, codice guasto o riferimento ordine", search: "Cerca", recent: "Conversazioni recenti", no_matches: "Nessuna conversazione corrispondente.", view: "Visualizza conversazione", messages: "messaggi"},
  de: {title: "Unterhaltungssuche", placeholder: "Nach Benutzer, Wörtern oder Fehlercode suchen", search: "Suchen", recent: "Letzte Unterhaltungen", no_matches: "Keine passenden Unterhaltungen gefunden.", view: "Unterhaltung anzeigen", messages: "Nachrichten"},
  fr: {title: "Recherche de conversations", placeholder: "Rechercher par utilisateur, mots ou code défaut", search: "Rechercher", recent: "Conversations récentes", no_matches: "Aucune conversation correspondante.", view: "Afficher la conversation", messages: "messages"},
  es: {title: "Búsqueda de conversaciones", placeholder: "Buscar por usuario, palabras o código de avería", search: "Buscar", recent: "Conversaciones recientes", no_matches: "No se encontraron conversaciones.", view: "Ver conversación", messages: "mensajes"},
  pl: {title: "Wyszukiwanie rozmów", placeholder: "Szukaj według użytkownika, słów lub kodu usterki", search: "Szukaj", recent: "Ostatnie rozmowy", no_matches: "Nie znaleziono pasujących rozmów.", view: "Wyświetl rozmowę", messages: "wiadomości"},
  pt: {title: "Pesquisa de conversas", placeholder: "Pesquisar por utilizador, palavras ou código de avaria", search: "Pesquisar", recent: "Conversas recentes", no_matches: "Não foram encontradas conversas.", view: "Ver conversa", messages: "mensagens"}
};

function conversationSearchText(key) {
  const values = conversationSearchTranslations[currentLanguage] ||
    conversationSearchTranslations.en;
  return values[key] || conversationSearchTranslations.en[key] || key;
}

function t(key) {
  return translations[currentLanguage]?.[key] || translations.en[key] || key;
}

function applyLanguage(language) {
  currentLanguage = translations[language] ? language : "en";
  try {
    window.localStorage.setItem("repairerPortalLanguage", currentLanguage);
  } catch {
    // Storage may be disabled; keep using the language for this page.
  }
  document.documentElement.lang = currentLanguage;
  loginLanguage.value = currentLanguage;
  portalLanguage.value = currentLanguage;
  document.querySelectorAll("[data-i18n]").forEach((element) => {
    element.textContent = t(element.dataset.i18n);
  });
  newSessionButton.lastChild.textContent = ` ${t("new_conversation")}`;
  document.querySelectorAll(".header-logout").forEach((button) => {
    button.textContent = t("log_out");
  });
  input.placeholder = t("placeholder");
  chatForm.querySelector("small").textContent = t("synthetic_notice");
  const dialogText = dialogTranslations[currentLanguage] || dialogTranslations.en;
  newSessionDialogTitle.textContent = dialogText.title;
  newSessionDialogCopy.textContent = dialogText.copy;
  newSessionDialogCancel.textContent = dialogText.cancel;
  newSessionDialogConfirm.textContent = dialogText.confirm;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {"Content-Type": "application/json"},
    ...options
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail;
    const error = new Error(
      typeof detail === "object" ? detail.message : detail || "Something went wrong."
    );
    error.requestId = typeof detail === "object" ? detail.request_id : null;
    throw error;
  }
  return data;
}

function showPortal(username, language = currentLanguage, role = "repairer", displayName = "") {
  currentRole = role;
  applyLanguage(language);
  loginView.classList.add("hidden");
  portalView.classList.remove("hidden");
  document.querySelector("#current-user").childNodes[0].textContent = username;
  document.querySelector("#current-user small").textContent =
    displayName || (role === "administrator" ? "Administrator" : t("demo_repairer"));
  adminNav.classList.toggle("hidden", role !== "administrator");
  refreshHealth();
}

function appendInlineMarkdown(target, text) {
  const pattern = /(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g;
  let cursor = 0;
  for (const match of text.matchAll(pattern)) {
    target.append(document.createTextNode(text.slice(cursor, match.index)));
    const token = match[0];
    const element = document.createElement(
      token.startsWith("**") ? "strong" : token.startsWith("`") ? "code" : "em"
    );
    element.textContent = token.startsWith("**") ? token.slice(2, -2) : token.slice(1, -1);
    target.append(element);
    cursor = match.index + token.length;
  }
  target.append(document.createTextNode(text.slice(cursor)));
}

function renderMarkdown(target, source) {
  target.replaceChildren();
  const lines = source.replace(/\r/g, "").split("\n");
  let list = null;

  const closeList = () => { list = null; };
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      closeList();
      continue;
    }
    if (/^---+$/.test(line)) {
      closeList();
      target.append(document.createElement("hr"));
      continue;
    }
    const heading = line.match(/^(#{2,4})\s+(.+)$/);
    if (heading) {
      closeList();
      const element = document.createElement(`h${heading[1].length}`);
      appendInlineMarkdown(element, heading[2]);
      target.append(element);
      continue;
    }
    const item = line.match(/^(\*|-|\d+\.)\s+(.+)$/);
    if (item) {
      const type = /\d+\./.test(item[1]) ? "ol" : "ul";
      if (!list || list.tagName.toLowerCase() !== type) {
        list = document.createElement(type);
        target.append(list);
      }
      const element = document.createElement("li");
      appendInlineMarkdown(element, item[2]);
      list.append(element);
      continue;
    }
    closeList();
    const paragraph = document.createElement("p");
    appendInlineMarkdown(paragraph, line);
    target.append(paragraph);
  }
}

const fieldLabels = {
  vehicle_model: "field_vehicle",
  fault_codes: "field_fault_codes",
  part_name: "field_part",
  market: "field_market",
  requested_capabilities: "field_services"
};

const serviceLabels = {
  diagnostics_agent: "diagnostics",
  service_library_agent: "service_library",
  parts_agent: "parts_inventory"
};

const metadataTranslations = {
  en: ["Vehicle", "Fault codes", "Part", "Market", "Requested services", "Request completed", "Partial result", "Clarification required", "Validation not completed", "Not supplied", "Request validation", "Not called", "Ref"],
  it: ["Veicolo", "Codici guasto", "Ricambio", "Mercato", "Servizi richiesti", "Richiesta completata", "Risultato parziale", "Chiarimento richiesto", "Convalida non completata", "Non fornito", "Convalida richiesta", "Non chiamato", "Rif."],
  de: ["Fahrzeug", "Fehlercodes", "Teil", "Markt", "Angeforderte Dienste", "Anfrage abgeschlossen", "Teilergebnis", "Klärung erforderlich", "Validierung nicht abgeschlossen", "Nicht angegeben", "Anfragevalidierung", "Nicht aufgerufen", "Ref."],
  fr: ["Véhicule", "Codes défaut", "Pièce", "Marché", "Services demandés", "Demande terminée", "Résultat partiel", "Précision requise", "Validation non terminée", "Non renseigné", "Validation de la demande", "Non appelé", "Réf."],
  es: ["Vehículo", "Códigos de avería", "Pieza", "Mercado", "Servicios solicitados", "Solicitud completada", "Resultado parcial", "Se requiere aclaración", "Validación no completada", "No proporcionado", "Validación de la solicitud", "No llamado", "Ref."],
  pl: ["Pojazd", "Kody usterek", "Część", "Rynek", "Żądane usługi", "Zapytanie zakończone", "Wynik częściowy", "Wymagane wyjaśnienie", "Walidacja nieukończona", "Nie podano", "Walidacja zapytania", "Nie wywołano", "Nr"],
  pt: ["Veículo", "Códigos de avaria", "Peça", "Mercado", "Serviços pedidos", "Pedido concluído", "Resultado parcial", "É necessário esclarecer", "Validação não concluída", "Não fornecido", "Validação do pedido", "Não chamado", "Ref."]
};
const metadataKeys = [
  "field_vehicle", "field_fault_codes", "field_part", "field_market", "field_services",
  "request_completed", "partial_result", "clarification_required",
  "validation_incomplete", "not_supplied", "request_validation", "not_called", "reference"
];
const displayedStatuses = {
  en: {success: "Success", no_match: "No match", missing_information: "Missing information", invalid_request: "Invalid request", temporary_failure: "Temporary failure", internal_error: "Internal error", not_run: "Not run"},
  it: {success: "Completato", no_match: "Nessuna corrispondenza", missing_information: "Informazioni mancanti", invalid_request: "Richiesta non valida", temporary_failure: "Errore temporaneo", internal_error: "Errore interno", not_run: "Non eseguito"},
  de: {success: "Erfolgreich", no_match: "Keine Übereinstimmung", missing_information: "Angaben fehlen", invalid_request: "Ungültige Anfrage", temporary_failure: "Temporärer Fehler", internal_error: "Interner Fehler", not_run: "Nicht ausgeführt"},
  fr: {success: "Réussi", no_match: "Aucune correspondance", missing_information: "Informations manquantes", invalid_request: "Demande non valide", temporary_failure: "Échec temporaire", internal_error: "Erreur interne", not_run: "Non exécuté"},
  es: {success: "Correcto", no_match: "Sin coincidencias", missing_information: "Falta información", invalid_request: "Solicitud no válida", temporary_failure: "Fallo temporal", internal_error: "Error interno", not_run: "No ejecutado"},
  pl: {success: "Sukces", no_match: "Brak dopasowania", missing_information: "Brakujące dane", invalid_request: "Nieprawidłowe zapytanie", temporary_failure: "Błąd tymczasowy", internal_error: "Błąd wewnętrzny", not_run: "Nie wykonano"},
  pt: {success: "Concluído", no_match: "Sem correspondência", missing_information: "Informação em falta", invalid_request: "Pedido inválido", temporary_failure: "Falha temporária", internal_error: "Erro interno", not_run: "Não executado"}
};

const progressTranslations = {
  en: {
    title: "Processing request", details: "Process details",
    reading: "Interpreting vehicle, market, DTC, part, and requested workshop task",
    validating: "Applying scope, security, ambiguity, and required-field guardrails",
    routing: "Evaluating Diagnostics (A2A), Service Library (MCP), and Parts Inventory (MCP)",
    coordinating: "Calling only selected agents and consolidating structured statuses",
    validated: "Request validation completed", not_validated: "Request needs clarification",
    called: "Selected agent", skipped: "Not selected", context: "Validated context",
    selection_reason: "Capability requested", no_selection: "No matching capability requested",
    agent_message: "Agent report"
  },
  it: {
    title: "Elaborazione della richiesta", details: "Dettagli del processo",
    reading: "Lettura e interpretazione della richiesta",
    validating: "Verifica delle informazioni necessarie e ambigue",
    routing: "Individuazione dei servizi pertinenti",
    coordinating: "Attesa del risultato consolidato dell'orchestratore",
    validated: "Convalida della richiesta completata", not_validated: "La richiesta necessita di chiarimenti",
    called: "Consultato", skipped: "Non necessario"
  },
  de: {
    title: "Anfrage wird verarbeitet", details: "Prozessdetails",
    reading: "Anfrage wird gelesen und interpretiert",
    validating: "Erforderliche und mehrdeutige Angaben werden geprüft",
    routing: "Relevante Dienste werden ermittelt",
    coordinating: "Der Orchestrator führt die Ergebnisse zusammen",
    validated: "Anfragevalidierung abgeschlossen", not_validated: "Für die Anfrage ist eine Klärung erforderlich",
    called: "Abgefragt", skipped: "Nicht erforderlich"
  },
  fr: {
    title: "Traitement de la demande", details: "Détails du processus",
    reading: "Lecture et interprétation de votre demande",
    validating: "Vérification des informations requises ou ambiguës",
    routing: "Identification des services pertinents",
    coordinating: "Attente de la synthèse de l’orchestrateur",
    validated: "Validation de la demande terminée", not_validated: "La demande nécessite une précision",
    called: "Consulté", skipped: "Non requis"
  },
  es: {
    title: "Procesando la solicitud", details: "Detalles del proceso",
    reading: "Lectura e interpretación de la solicitud",
    validating: "Comprobación de la información necesaria o ambigua",
    routing: "Determinación de los servicios pertinentes",
    coordinating: "Esperando el resultado consolidado del orquestador",
    validated: "Validación de la solicitud completada", not_validated: "La solicitud necesita una aclaración",
    called: "Consultado", skipped: "No necesario"
  },
  pl: {
    title: "Przetwarzanie zapytania", details: "Szczegóły procesu",
    reading: "Odczytywanie i interpretowanie zapytania",
    validating: "Sprawdzanie wymaganych i niejednoznacznych informacji",
    routing: "Ustalanie odpowiednich usług",
    coordinating: "Oczekiwanie na połączony wynik orkiestratora",
    validated: "Walidacja zapytania zakończona", not_validated: "Zapytanie wymaga wyjaśnienia",
    called: "Wywołano", skipped: "Niewymagane"
  },
  pt: {
    title: "A processar o pedido", details: "Detalhes do processo",
    reading: "A ler e interpretar o pedido",
    validating: "A verificar informações necessárias ou ambíguas",
    routing: "A determinar os serviços relevantes",
    coordinating: "A aguardar o resultado consolidado do orquestrador",
    validated: "Validação do pedido concluída", not_validated: "O pedido necessita de esclarecimento",
    called: "Consultado", skipped: "Não necessário"
  }
};

function progressText(key) {
  return progressTranslations[currentLanguage]?.[key] || progressTranslations.en[key] || key;
}

function addLiveProgress(article) {
  const bubble = article.querySelector(".bubble");
  bubble.replaceChildren();
  bubble.classList.add("progress-bubble");
  const title = document.createElement("strong");
  title.className = "progress-title";
  title.textContent = progressText("title");
  const list = document.createElement("ol");
  list.className = "progress-list";
  bubble.append(title, list);
  let renderedCount = 0;
  let stopped = false;

  const eventText = (event) => {
    const agentKey = serviceLabels[event.agent_name];
    const agent = agentKey ? t(agentKey) : event.agent_name;
    const protocol = event.protocol ? event.protocol.toUpperCase() : "";
    if (event.event === "request_received") return "Request accepted for this conversation";
    if (event.event === "extracting_request") return "Cross-matching the latest request with recent conversation context";
    if (event.event === "extraction_completed") {
      const terms = [
        event.vehicle_model,
        ...(event.fault_codes || []),
        event.part_name,
        event.market
      ].filter(Boolean);
      return `Matched workshop terms: ${terms.join(" · ") || "none yet"}`;
    }
    if (event.event === "validating_request") return "Checking scope, ambiguity, and mandatory fields before routing";
    if (event.event === "validation_completed") {
      if (event.validated) return "Validation passed; remote-agent routing is permitted";
      const fields = [...(event.missing_fields || []), ...(event.ambiguous_fields || [])];
      return `Validation stopped routing; clarification required for: ${fields.join(", ")}`;
    }
    if (event.event === "routing_completed") {
      return `Selected for this request: ${(event.selected_agents || []).join(", ") || "no remote agents"}`;
    }
    if (event.event === "agent_started") {
      return `Consulting ${agent} through ${protocol} for ${event.capability}`;
    }
    if (event.event === "agent_completed") {
      const status = displayedStatus(event.status);
      const continuation = !["success", "no_match"].includes(event.status) && event.continuing
        ? "; preserving this status and continuing with the other selected agents"
        : "";
      return `${agent} returned ${status}${continuation}`;
    }
    if (event.event === "consolidating_results") {
      const statuses = Object.entries(event.result_statuses || {})
        .map(([capability, status]) => `${capability}: ${displayedStatus(status)}`);
      return `Consolidating structured results${statuses.length ? ` (${statuses.join(", ")})` : ""}`;
    }
    if (event.event === "guardrail_blocked") return `Request stopped by the ${event.category} guardrail; no agent was called`;
    if (event.event === "response_completed") return "Response prepared from the validated agent results";
    return event.event;
  };

  const refresh = async () => {
    if (stopped) return;
    try {
      const progress = await api("/api/chat/progress");
      for (const event of (progress.events || []).slice(renderedCount)) {
        list.lastElementChild?.classList.remove("progress-active");
        list.lastElementChild?.classList.add("progress-complete");
        const item = document.createElement("li");
        item.className = "progress-active";
        item.textContent = eventText(event);
        list.append(item);
        renderedCount += 1;
      }
    } catch {
      // The chat request below will show any API error to the user.
    }
  };
  refresh();
  const timer = window.setInterval(refresh, 300);
  return async () => {
    await refresh();
    stopped = true;
    window.clearInterval(timer);
  };
}

function addProcessTrace(article, metadata) {
  if (!metadata?.validation) return;
  const details = document.createElement("details");
  details.className = "process-trace";
  const summary = document.createElement("summary");
  summary.textContent = progressText("details");
  const list = document.createElement("ol");
  const validation = document.createElement("li");
  validation.textContent = metadata.validation.validated
    ? progressText("validated")
    : progressText("not_validated");
  list.append(validation);
  const request = metadata.validation.normalized_request || {};
  const contextValues = [
    request.vehicle_model,
    (request.fault_codes || []).join(", "),
    request.part_name,
    request.market
  ].filter(Boolean);
  if (contextValues.length) {
    const context = document.createElement("li");
    context.textContent = `${progressText("context")}: ${contextValues.join(" · ")}`;
    list.append(context);
  }
  const selectedAgents = new Set(
    (metadata.services || []).map((service) => service.agent_name)
  );
  for (const candidate of [
    ["diagnostics_agent", "a2a"],
    ["service_library_agent", "mcp"],
    ["parts_agent", "mcp"]
  ]) {
    if (selectedAgents.has(candidate[0])) continue;
    const evaluation = document.createElement("li");
    const labelKey = serviceLabels[candidate[0]];
    const label = labelKey ? t(labelKey) : candidate[0];
    evaluation.textContent = `${progressText("skipped")}: ${label} ` +
      `[${candidate[1].toUpperCase()}] — ${progressText("no_selection")}`;
    list.append(evaluation);
  }
  for (const service of metadata.services || []) {
    const item = document.createElement("li");
    const labelKey = serviceLabels[service.agent_name];
    const label = labelKey ? t(labelKey) : service.agent_name;
    const protocol = service.protocol && service.protocol !== "not_called"
      ? ` [${service.protocol.toUpperCase()}]`
      : "";
    item.textContent = service.called
      ? `${progressText("called")}: ${label}${protocol} — ` +
        `${progressText("selection_reason")}: ${service.capability}; ` +
        `${displayedStatus(service.status)}. ` +
        `${progressText("agent_message")}: ${service.message}`
      : `${progressText("skipped")}: ${label} — ` +
        `${displayedStatus(service.status)}. ${service.message}`;
    list.append(item);
  }
  details.append(summary, list);
  const container = article.querySelector(".message-content");
  container?.insertBefore(details, container.querySelector(".bubble"));
}

function metadataText(key) {
  const index = metadataKeys.indexOf(key);
  const values = metadataTranslations[currentLanguage] || metadataTranslations.en;
  return index >= 0 ? values[index] : key;
}

function completionStatusText(status) {
  const keys = {
    complete: "request_completed",
    partial: "partial_result",
    needs_clarification: "clarification_required",
    validation_not_run: "validation_incomplete"
  };
  return keys[status] ? metadataText(keys[status]) : status.replaceAll("_", " ");
}

function displayedStatus(status) {
  return displayedStatuses[currentLanguage]?.[status]
    || displayedStatuses.en[status]
    || status.replaceAll("_", " ");
}

function readableValue(value, key = "") {
  if (Array.isArray(value)) {
    if (key === "requested_capabilities") {
      return value.map((capability) => {
        const capabilityKeys = {
          diagnostics: "diagnostics",
          service_library: "service_library",
          parts: "parts_inventory"
        };
        return t(capabilityKeys[capability] || capability);
      }).join(", ");
    }
    return value.join(", ");
  }
  return value ?? metadataText("not_supplied");
}

function addMetadata(article, metadata) {
  if (!metadata) return;
  const container = article.querySelector(".message-content");
  const panel = document.createElement("section");
  panel.className = `request-panel request-${metadata.completion_status}`;

  const header = document.createElement("div");
  header.className = "request-panel-header";
  const title = document.createElement("strong");
  title.textContent = metadata.completion_status === "complete"
    ? metadataText("request_completed")
    : metadata.completion_status === "partial"
      ? metadataText("partial_result")
      : metadata.completion_status === "needs_clarification"
        ? metadataText("clarification_required")
        : metadataText("validation_incomplete");
  const reference = document.createElement("span");
  reference.textContent = `${metadataText("reference")} ${metadata.request_id.slice(0, 8).toUpperCase()}`;
  reference.title = metadata.request_id;
  header.append(title, reference);
  panel.append(header);

  const normalized = metadata.validation?.normalized_request || {};
  const fields = document.createElement("div");
  fields.className = "request-fields";
  for (const [key, labelKey] of Object.entries(fieldLabels)) {
    if (!(key in normalized)) continue;
    const item = document.createElement("div");
    const term = document.createElement("span");
    const value = document.createElement("strong");
    term.textContent = metadataText(labelKey);
    value.textContent = readableValue(normalized[key], key);
    if (metadata.validation.ambiguous_fields?.includes(key)) item.classList.add("field-ambiguous");
    if (metadata.validation.missing_fields?.includes(key)) item.classList.add("field-missing");
    item.append(term, value);
    fields.append(item);
  }
  if (fields.children.length) panel.append(fields);

  const workflow = document.createElement("div");
  workflow.className = "workflow";
  const validationStep = document.createElement("div");
  validationStep.className = `workflow-step status-${metadata.validation.status}`;
  const validationDot = document.createElement("i");
  const validationLabel = document.createElement("span");
  validationLabel.textContent = metadataText("request_validation");
  validationStep.append(validationDot, validationLabel);
  workflow.append(validationStep);
  for (const service of metadata.services || []) {
    const step = document.createElement("div");
    step.className = `workflow-step status-${service.status}`;
    const dot = document.createElement("i");
    const label = document.createElement("span");
    const status = document.createElement("small");
    label.textContent = t(serviceLabels[service.agent_name] || service.agent_name);
    status.textContent = service.called
      ? displayedStatus(service.status)
      : metadataText("not_called");
    step.append(dot, label, status);
    workflow.append(step);
  }
  panel.append(workflow);
  container.insertBefore(panel, container.querySelector(".bubble"));
}

function addMessage(role, text, extraClass = "", metadata = null) {
  const article = document.createElement("article");
  article.className = `message ${role} ${extraClass}`;
  const inner = role === "assistant"
    ? '<div class="avatar">✦</div><div class="message-content"><p class="speaker">Repairer Assistant</p><div class="bubble"></div></div>'
    : '<div class="message-content"><p class="speaker">You</p><div class="bubble"></div></div>';
  article.innerHTML = inner;
  article.querySelector(".speaker").textContent = role === "assistant" ? t("assistant_name") : t("you");
  const bubble = article.querySelector(".bubble");
  if (role === "assistant" && extraClass !== "typing") renderMarkdown(bubble, text);
  else bubble.textContent = text;
  if (role === "assistant") {
    addProcessTrace(article, metadata);
    addMetadata(article, metadata);
  }
  messages.append(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

function showConversation(conversationMessages) {
  messages.replaceChildren();
  if (!conversationMessages.length) {
    addMessage(
      "assistant",
      t("new_chat_message")
    );
    return;
  }
  conversationMessages.forEach((message) => {
    addMessage(message.role, message.text, "", message.metadata);
  });
}

function formatError(error) {
  return error.requestId
    ? `${error.message}\nReference: ${error.requestId.slice(0, 8).toUpperCase()}`
    : error.message;
}

function formatTimestamp(value) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

function emptyState(title, message) {
  const section = document.createElement("section");
  section.className = "empty-state";
  const heading = document.createElement("h3");
  const copy = document.createElement("p");
  heading.textContent = title;
  copy.textContent = message;
  section.append(heading, copy);
  return section;
}

function recordCard(record, isRepairOrder) {
  const article = document.createElement("article");
  article.className = "record-card";

  const header = document.createElement("div");
  header.className = "record-header";
  const title = document.createElement("strong");
  title.textContent = isRepairOrder
    ? record.repair_order_id
    : `Chat ${record.request_id.slice(0, 8).toUpperCase()}`;
  const timestamp = document.createElement("time");
  timestamp.dateTime = record.occurred_at;
  timestamp.textContent = formatTimestamp(record.occurred_at);
  header.append(title, timestamp);

  const status = document.createElement("span");
  status.className = `record-status status-${record.completion_status}`;
  status.textContent = completionStatusText(record.completion_status);

  const requestLabel = document.createElement("small");
  requestLabel.textContent = t("request");
  const request = document.createElement("p");
  request.textContent = record.request;

  article.append(header, status, requestLabel, request);

  const normalized = record.validation?.normalized_request || {};
  if (Object.keys(normalized).length) {
    const fields = document.createElement("dl");
    fields.className = "record-fields";
    for (const [key, value] of Object.entries(normalized)) {
      if (value === null || value === "" || (Array.isArray(value) && !value.length)) continue;
      const term = document.createElement("dt");
      const detail = document.createElement("dd");
      term.textContent = fieldLabels[key]
        ? metadataText(fieldLabels[key])
        : key.replaceAll("_", " ");
      detail.textContent = readableValue(value, key);
      fields.append(term, detail);
    }
    if (fields.children.length) article.append(fields);
  }

  const details = document.createElement("details");
  const summary = document.createElement("summary");
  const response = document.createElement("div");
  response.className = "record-response";
  summary.textContent = t("view_response");
  renderMarkdown(response, record.response);
  details.append(summary, response);
  article.append(details);

  if (!isRepairOrder) {
    const resume = document.createElement("button");
    resume.className = "resume-conversation";
    resume.type = "button";
    resume.textContent = t("return_conversation");
    resume.addEventListener("click", async () => {
      if (requestInProgress) return;
      requestInProgress = true;
      resume.disabled = true;
      try {
        const data = await api(
          `/api/service-history/${encodeURIComponent(record.conversation_id)}/resume`,
          {method: "POST"}
        );
        showConversation(data.messages);
        await switchView("assistant");
      } catch (error) {
        window.alert(formatError(error));
      } finally {
        requestInProgress = false;
        resume.disabled = false;
      }
    });
    article.append(resume);
  }
  return article;
}

async function loadRepairOrders() {
  repairOrdersView.replaceChildren();
  const data = await api("/api/repair-orders");
  if (!data.repair_orders.length) {
    repairOrdersView.append(
      emptyState(
        t("no_orders"),
        t("no_orders_copy")
      )
    );
    return;
  }
  data.repair_orders.forEach((record) => {
    repairOrdersView.append(recordCard(record, true));
  });
}

async function loadServiceHistory() {
  serviceHistoryView.replaceChildren();
  const data = await api("/api/service-history");
  if (!data.service_history.length) {
    serviceHistoryView.append(
      emptyState(t("no_history"), t("no_history_copy"))
    );
    return;
  }
  data.service_history.forEach((record) => {
    serviceHistoryView.append(recordCard(record, false));
  });
}

function usageChart(usage) {
  const section = document.createElement("article");
  section.className = "record-card admin-chart";
  const title = document.createElement("h3");
  title.textContent = usageChartTitles[currentLanguage] || usageChartTitles.en;
  section.append(title);

  if (!usage.timeline?.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = "No LLM usage has been recorded yet.";
    section.append(empty);
    return section;
  }

  const width = 900;
  const height = 280;
  const padding = 48;
  const plotWidth = width - padding * 2;
  const plotHeight = height - padding * 2;
  const points = usage.timeline;
  const maxTokens = Math.max(...points.map((point) => point.tokens), 1);
  const maxCost = Math.max(...points.map((point) => point.cost_usd), 0.000001);
  const xAt = (index) => points.length === 1
    ? padding + plotWidth / 2
    : padding + (index / (points.length - 1)) * plotWidth;
  const yAt = (value, maximum) => padding + plotHeight - (value / maximum) * plotHeight;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", title.textContent);

  for (let index = 0; index <= 4; index += 1) {
    const y = padding + (index / 4) * plotHeight;
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.setAttribute("x1", padding);
    line.setAttribute("x2", width - padding);
    line.setAttribute("y1", y);
    line.setAttribute("y2", y);
    line.setAttribute("class", "chart-grid");
    svg.append(line);
  }

  const addSeries = (values, maximum, className) => {
    const polyline = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
    const coordinates = values.map((value, index) =>
      `${xAt(index)},${yAt(value, maximum)}`
    );
    if (coordinates.length === 1) {
      coordinates.unshift(`${padding},${yAt(values[0], maximum)}`);
      coordinates.push(`${width - padding},${yAt(values[0], maximum)}`);
    }
    polyline.setAttribute("points", coordinates.join(" "));
    polyline.setAttribute("class", className);
    svg.append(polyline);
  };

  addSeries(points.map((point) => point.tokens), maxTokens, "chart-tokens");
  if (points.some((point) => point.has_cost)) {
    addSeries(points.map((point) => point.cost_usd), maxCost, "chart-cost");
  }
  section.append(svg);

  const footer = document.createElement("div");
  footer.className = "chart-footer";
  const first = new Date(points[0].timestamp).toLocaleString();
  const last = new Date(points.at(-1).timestamp).toLocaleString();
  footer.innerHTML = `<small></small><div><span class="legend-tokens"></span><b></b><span class="legend-cost"></span><b></b></div><small></small>`;
  footer.querySelector("small:first-child").textContent = first;
  footer.querySelector("small:last-child").textContent = last;
  const labels = footer.querySelectorAll("b");
  labels[0].textContent = adminText("tokens");
  labels[1].textContent = adminText("cost");
  section.append(footer);
  return section;
}

async function loadConversationMatches(query, target) {
  target.replaceChildren();
  const data = await api(
    `/api/admin/conversations?q=${encodeURIComponent(query)}&limit=25`
  );
  if (!data.conversations.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = conversationSearchText("no_matches");
    target.append(empty);
    return;
  }

  data.conversations.forEach((conversation) => {
    const card = document.createElement("article");
    card.className = "admin-conversation-result";
    const heading = document.createElement("div");
    heading.className = "admin-conversation-heading";
    const identity = document.createElement("strong");
    identity.textContent = `${conversation.display_name} (${conversation.username})`;
    const timestamp = document.createElement("time");
    timestamp.textContent = new Date(conversation.updated_at).toLocaleString();
    heading.append(identity, timestamp);
    const snippet = document.createElement("p");
    snippet.textContent = conversation.match_text || conversationSearchText("recent");
    const meta = document.createElement("small");
    const matchedOrder = conversation.match_repair_order
      ? ` · ${conversation.match_repair_order}`
      : "";
    meta.textContent =
      `${conversation.message_count} ${conversationSearchText("messages")} · ${conversation.conversation_id.slice(0, 8).toUpperCase()}${matchedOrder}`;
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = conversationSearchText("view");
    const detail = document.createElement("div");
    detail.className = "admin-conversation-detail hidden";
    button.addEventListener("click", async () => {
      button.disabled = true;
      try {
        if (!detail.dataset.loaded) {
          const response = await api(
            `/api/admin/conversations/${encodeURIComponent(conversation.conversation_id)}`
          );
          const relatedRecords = document.createElement("section");
          relatedRecords.className = "admin-related-records";
          const orderTitle = document.createElement("h4");
          orderTitle.textContent = `${adminText("orders")}:`;
          relatedRecords.append(orderTitle);
          if (!response.conversation.repair_orders.length) {
            const none = document.createElement("p");
            none.className = "muted";
            none.textContent = "No repair orders are associated with this conversation.";
            relatedRecords.append(none);
          }
          response.conversation.repair_orders.forEach((order) => {
            const record = document.createElement("div");
            record.className = "admin-related-order";
            const reference = document.createElement("strong");
            reference.textContent = order.repair_order_id;
            const status = document.createElement("span");
            status.textContent = order.completion_status;
            const request = document.createElement("p");
            request.textContent = order.request;
            record.append(reference, status, request);
            relatedRecords.append(record);
          });

          const serviceTitle = document.createElement("h4");
          serviceTitle.textContent = `${adminText("requests")}:`;
          relatedRecords.append(serviceTitle);
          response.conversation.service_history.forEach((history) => {
            const record = document.createElement("div");
            record.className = "admin-related-service";
            const request = document.createElement("strong");
            request.textContent = history.request;
            const services = document.createElement("p");
            services.textContent = history.services
              .map((service) =>
                `${service.agent_name} [${service.protocol.toUpperCase()}]: ${service.status}`
              )
              .join(" · ");
            record.append(request, services);
            relatedRecords.append(record);
          });
          detail.append(relatedRecords);

          const transcriptTitle = document.createElement("h4");
          transcriptTitle.textContent = `${conversationSearchText("view")}:`;
          detail.append(transcriptTitle);
          response.conversation.messages.forEach((message) => {
            const entry = document.createElement("div");
            entry.className = `admin-transcript-${message.role}`;
            const role = document.createElement("strong");
            role.textContent = `${message.role}:`;
            const text = document.createElement("p");
            text.textContent = message.text;
            entry.append(role, text);
            detail.append(entry);
          });
          detail.dataset.loaded = "true";
        }
        detail.classList.toggle("hidden");
      } finally {
        button.disabled = false;
      }
    });
    card.append(heading, snippet, meta, button, detail);
    target.append(card);
  });
}

async function conversationSearchPanel() {
  const section = document.createElement("article");
  section.className = "record-card admin-conversation-search";
  const title = document.createElement("h3");
  title.textContent = conversationSearchText("title");
  const form = document.createElement("form");
  form.className = "admin-search-form";
  const input = document.createElement("input");
  input.type = "search";
  input.maxLength = 120;
  input.placeholder = conversationSearchText("placeholder");
  const button = document.createElement("button");
  button.type = "submit";
  button.textContent = conversationSearchText("search");
  form.append(input, button);
  const results = document.createElement("div");
  results.className = "admin-search-results";
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    button.disabled = true;
    try {
      await loadConversationMatches(input.value.trim(), results);
    } finally {
      button.disabled = false;
    }
  });
  section.append(title, form, results);
  await loadConversationMatches("", results);
  return section;
}

async function loadAdministration() {
  administrationView.replaceChildren();
  const data = await api("/api/admin/overview");

  const metricGrid = document.createElement("section");
  metricGrid.className = "admin-metric-grid";
  const cost = data.usage.cost_usd == null
    ? "Unavailable"
    : `$${Number(data.usage.cost_usd).toFixed(6)} (${data.usage.cost_coverage})`;
  const resolvedModel = data.usage.models?.[0]?.resolved_model;
  const metrics = [
    [adminText("model"), resolvedModel
      ? `${data.model.configured_model} · ${resolvedModel}`
      : data.model.configured_model],
    [adminText("calls"), `${data.usage.calls || 0} (${data.usage.failed_calls || 0} failed)`],
    [adminText("tokens"), `${Number(data.usage.total_tokens || 0).toLocaleString()} · in ${Number(data.usage.prompt_tokens || 0).toLocaleString()} / out ${Number(data.usage.completion_tokens || 0).toLocaleString()}`],
    [adminText("cost"), cost],
    [adminText("latency"), `${Math.round(data.usage.average_latency_ms || 0)} ms`],
    [adminText("uptime"), `${Math.round(data.runtime.uptime_seconds / 60)} min`]
  ];
  metrics.forEach(([label, value]) => {
    const metric = document.createElement("article");
    metric.className = "admin-metric";
    const labelNode = document.createElement("span");
    labelNode.textContent = label;
    const valueNode = document.createElement("strong");
    valueNode.textContent = value;
    metric.append(labelNode, valueNode);
    metricGrid.append(metric);
  });
  administrationView.append(metricGrid);
  administrationView.append(usageChart(data.usage));
  administrationView.append(await conversationSearchPanel());

  const activity = document.createElement("article");
  activity.className = "record-card admin-section";
  activity.innerHTML = `<h3></h3><div class="admin-stat-row"></div>`;
  activity.querySelector("h3").textContent = adminText("activity");
  [
    [adminText("accounts"), data.activity.accounts],
    [adminText("conversations"), data.activity.conversations],
    [adminText("requests"), data.activity.service_requests],
    [adminText("orders"), data.activity.repair_orders]
  ].forEach(([label, value]) => {
    const item = document.createElement("div");
    item.innerHTML = "<span></span><strong></strong>";
    item.querySelector("span").textContent = label;
    item.querySelector("strong").textContent = value;
    activity.querySelector(".admin-stat-row").append(item);
  });
  administrationView.append(activity);

  const operations = document.createElement("section");
  operations.className = "admin-two-column";
  const health = document.createElement("article");
  health.className = "record-card admin-section";
  health.innerHTML = "<h3></h3><div class='admin-list'></div>";
  health.querySelector("h3").textContent = adminText("health");
  data.services.forEach((service) => {
    const row = document.createElement("div");
    row.innerHTML = "<span></span><strong></strong>";
    row.querySelector("span").textContent = service.display_name;
    row.querySelector("strong").textContent =
      `${service.status}${service.latency_ms == null ? "" : ` · ${service.latency_ms} ms`}`;
    health.querySelector(".admin-list").append(row);
  });
  const routing = document.createElement("article");
  routing.className = "record-card admin-section";
  routing.innerHTML = "<h3></h3><div class='admin-list'></div>";
  routing.querySelector("h3").textContent = adminText("routing");
  Object.entries(data.activity.protocol_invocations).forEach(([protocol, count]) => {
    const row = document.createElement("div");
    row.innerHTML = "<span></span><strong></strong>";
    row.querySelector("span").textContent = protocol.toUpperCase();
    row.querySelector("strong").textContent = count;
    routing.querySelector(".admin-list").append(row);
  });
  operations.append(health, routing);
  administrationView.append(operations);

  const notice = document.createElement("p");
  notice.className = "admin-cost-notice";
  notice.textContent = data.cost_notice;
  administrationView.append(notice);

  const usersTitle = document.createElement("h3");
  usersTitle.className = "admin-users-title";
  usersTitle.textContent = adminText("users");
  administrationView.append(usersTitle);
  data.accounts.forEach((account) => {
    const card = document.createElement("article");
    card.className = "record-card";
    card.innerHTML = `
      <div class="record-header"><strong></strong><span class="record-status"></span></div>
      <dl class="record-fields">
        <div><dt>Conversations</dt><dd></dd></div>
        <div><dt>Service requests</dt><dd></dd></div>
        <div><dt>Repair orders</dt><dd></dd></div>
        <div><dt>Language</dt><dd></dd></div>
      </dl>`;
    card.querySelector("strong").textContent = account.display_name;
    card.querySelector(".record-status").textContent = account.role;
    const values = card.querySelectorAll("dd");
    [account.conversations, account.service_requests, account.repair_orders, account.language]
      .forEach((value, index) => { values[index].textContent = value; });
    administrationView.append(card);
  });
}

async function switchView(view) {
  document.querySelectorAll("nav [data-view]").forEach((button) => {
    button.classList.toggle("nav-active", button.dataset.view === view);
  });
  messages.classList.toggle("hidden", view !== "assistant");
  chatForm.classList.toggle("hidden", view !== "assistant");
  repairOrdersView.classList.toggle("hidden", view !== "repair-orders");
  serviceHistoryView.classList.toggle("hidden", view !== "service-history");
  administrationView.classList.toggle("hidden", view !== "administration");
  newSessionButton.classList.toggle("hidden", view !== "assistant");

  if (view === "assistant") {
    viewEyebrow.textContent = t("assistant_eyebrow");
    viewTitle.textContent = t("assistant_title");
    input.focus();
  } else if (view === "repair-orders") {
    viewEyebrow.textContent = t("records_eyebrow");
    viewTitle.textContent = t("repair_orders");
    await loadRepairOrders();
  } else if (view === "service-history") {
    viewEyebrow.textContent = t("records_eyebrow");
    viewTitle.textContent = t("service_history");
    await loadServiceHistory();
  } else if (view === "administration" && currentRole === "administrator") {
    viewEyebrow.textContent = adminText("eyebrow");
    viewTitle.textContent = adminText("title");
    await loadAdministration();
  }
}

async function refreshHealth() {
  const refresh = document.querySelector("#refresh-health");
  refresh.classList.add("spinning");
  try {
    const data = await api("/api/services/health");
    for (const service of data.services) {
      const row = document.querySelector(`[data-service="${service.name}"]`);
      if (!row) continue;
      const indicator = row.querySelector("i");
      indicator.className = `health-${service.status}`;
      const detail = row.querySelector("small");
      detail.textContent = service.status === "available"
        ? `${service.latency_ms} ms`
        : service.status;
      row.title = `${service.display_name}: ${service.status}`;
    }
  } catch {
    document.querySelectorAll(".services [data-service] i").forEach((indicator) => {
      indicator.className = "health-unavailable";
    });
  } finally {
    refresh.classList.remove("spinning");
  }
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const error = document.querySelector("#login-error");
  error.textContent = "";
  try {
    const data = await api("/api/login", {
      method: "POST",
      body: JSON.stringify({
        username: document.querySelector("#username").value,
        password: document.querySelector("#password").value,
        language: loginLanguage.value
      })
    });
    document.querySelector("#password").value = "";
    showPortal(data.username, data.language, data.role, data.display_name);
  } catch (err) {
    error.textContent = formatError(err);
  }
});

loginLanguage.addEventListener("change", () => {
  applyLanguage(loginLanguage.value);
});

portalLanguage.addEventListener("change", async () => {
  const previousLanguage = currentLanguage;
  portalLanguage.disabled = true;
  try {
    const data = await api("/api/language", {
      method: "PUT",
      body: JSON.stringify({language: portalLanguage.value})
    });
    applyLanguage(data.language);
    const activeView = document.querySelector("nav .nav-active")?.dataset.view || "assistant";
    await switchView(activeView);
  } catch (error) {
    applyLanguage(previousLanguage);
    window.alert(formatError(error));
  } finally {
    portalLanguage.disabled = false;
  }
});

input.addEventListener("keydown", (event) => {
  if (
    event.key !== "Enter"
    || event.shiftKey
    || event.isComposing
    || event.keyCode === 229
  ) {
    return;
  }

  event.preventDefault();
  if (!requestInProgress) sendButton.click();
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (requestInProgress) return;
  const text = input.value.trim();
  if (!text) return;
  requestInProgress = true;
  input.value = "";
  document.querySelector(".suggestions")?.remove();
  addMessage("user", text);
  const typing = addMessage(
    "assistant",
    t("typing_message"),
    "typing"
  );
  const stopProgress = addLiveProgress(typing);
  sendButton.disabled = true;
  newSessionButton.disabled = true;
  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({message: text})
    });
    await stopProgress();
    typing.remove();
    addMessage("assistant", data.reply, "", data);
    refreshHealth();
  } catch (err) {
    await stopProgress();
    typing.querySelector(".bubble").textContent = formatError(err);
    typing.classList.remove("typing");
  } finally {
    requestInProgress = false;
    sendButton.disabled = false;
    newSessionButton.disabled = false;
    input.focus();
  }
});

document.querySelectorAll(".suggestions button").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.textContent;
    input.focus();
  });
});

document.querySelectorAll("nav [data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    if (!requestInProgress) {
      switchView(button.dataset.view).catch((error) => {
        const target = button.dataset.view === "repair-orders"
          ? repairOrdersView
          : serviceHistoryView;
        target.replaceChildren(emptyState("Unable to load records", formatError(error)));
      });
    }
  });
});

document.querySelectorAll("[data-logout]").forEach((button) => {
  button.addEventListener("click", async () => {
    if (requestInProgress) return;
    button.disabled = true;
    try {
      await api("/api/logout", {method: "POST"});
      location.reload();
    } catch (error) {
      button.disabled = false;
      window.alert(formatError(error));
    }
  });
});

newSessionButton.addEventListener("click", () => {
  if (!requestInProgress) newSessionDialog.showModal();
});

newSessionDialog.addEventListener("close", async () => {
  if (newSessionDialog.returnValue !== "confirm" || requestInProgress) return;
  requestInProgress = true;
  newSessionButton.disabled = true;
  sendButton.disabled = true;
  try {
    await api("/api/session/new", {method: "POST"});
    messages.querySelectorAll(".message, .suggestions").forEach((item) => item.remove());
    addMessage(
      "assistant",
      t("new_chat_message")
    );
    input.focus();
  } catch (err) {
    addMessage("assistant", formatError(err));
  } finally {
    requestInProgress = false;
    newSessionButton.disabled = false;
    sendButton.disabled = false;
  }
});

document.querySelector("#refresh-health").addEventListener("click", refreshHealth);

themeToggle.addEventListener("click", () => {
  applyTheme(currentTheme === "tech" ? "classic" : "tech");
});

api("/api/session").then((data) => {
  showPortal(data.username, data.language, data.role, data.display_name);
  if (data.messages.length) showConversation(data.messages);
}).catch(() => {});

let savedLanguage = "en";
try {
  savedLanguage = window.localStorage.getItem("repairerPortalLanguage") || "en";
} catch {
  savedLanguage = "en";
}
applyLanguage(savedLanguage);

let savedTheme = "tech";
try {
  savedTheme = window.localStorage.getItem("repairerPortalTheme") || "tech";
} catch {
  savedTheme = "tech";
}
applyTheme(savedTheme);
