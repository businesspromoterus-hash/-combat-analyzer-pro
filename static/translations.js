/**
 * Traducciones: español e inglés
 * La app detecta el idioma del navegador automáticamente.
 */
const TRANSLATIONS = {
  es: {
    // Navegación
    "nav.home": "Inicio",
    "nav.new_fighter": "Nuevo peleador",
    "nav.new_plan": "Nuevo plan",
    "nav.logout": "Cerrar sesión",

    // Dashboard
    "dashboard.title": "Plan estratégico de combate",
    "dashboard.subtitle": "Crea perfiles de tu peleador y el rival, analiza videos de peleas con IA, y genera un plan táctico completo en PDF.",
    "dashboard.our_fighter": "+ Nuestro peleador",
    "dashboard.opponent": "+ Oponente",
    "dashboard.generate_plan": "→ Generar plan de combate",
    "dashboard.our_fighters": "Nuestros peleadores",
    "dashboard.opponents": "Oponentes",
    "dashboard.no_fighters": "Aún no tienes peleadores registrados.",
    "dashboard.no_opponents": "Aún no tienes oponentes registrados.",
    "dashboard.create_one": "Crear uno",

    // Peleador
    "fighter.new_our": "Nuevo peleador — Nuestro equipo",
    "fighter.new_opponent": "Nuevo oponente — Rival",
    "fighter.name": "Nombre completo",
    "fighter.sport": "Deporte",
    "fighter.country": "País",
    "fighter.age": "Edad",
    "fighter.weight": "Peso (kg)",
    "fighter.division": "División / Categoría",
    "fighter.height": "Estatura (cm)",
    "fighter.reach": "Alcance (cm)",
    "fighter.stance": "Guardia",
    "fighter.record": "Récord",
    "fighter.wins": "Victorias",
    "fighter.losses": "Derrotas",
    "fighter.draws": "Empates",
    "fighter.ko_wins": "KOs / TKOs",
    "fighter.sub_wins": "Sumisiones",
    "fighter.experience": "Años de experiencia",
    "fighter.notes": "Notas del entrenador",
    "fighter.save": "Guardar peleador",
    "fighter.saving": "Guardando...",
    "fighter.profile": "Perfil táctico consolidado",
    "fighter.generate_profile": "Generar / actualizar",
    "fighter.fights": "Peleas analizadas",
    "fighter.add_fight": "+ Agregar pelea",
    "fighter.analyze": "Analizar",
    "fighter.analyzing": "Analizando...",
    "fighter.edit": "Editar perfil",
    "fighter.delete": "Borrar peleador",

    // Peleas
    "fight.youtube_url": "Link de YouTube",
    "fight.title": "Título / descripción",
    "fight.opponent": "Oponente en esta pelea",
    "fight.result": "Resultado",
    "fight.date": "Fecha",
    "fight.notes": "Notas del entrenador para esta pelea",
    "fight.add": "Agregar pelea",
    "fight.win": "Victoria",
    "fight.loss": "Derrota",
    "fight.draw": "Empate",

    // Análisis
    "analysis.failed": "FALLIDO",
    "analysis.completed": "COMPLETADO",
    "analysis.pending": "PENDIENTE",
    "analysis.processing": "PROCESANDO",
    "analysis.no_video": "Sin video",

    // Plan
    "plan.new": "Nuevo plan de combate",
    "plan.our_fighter": "Nuestro peleador",
    "plan.opponent": "Oponente",
    "plan.select_fighter": "Seleccionar peleador...",
    "plan.select_opponent": "Seleccionar oponente...",
    "plan.context": "Contexto adicional (opcional)",
    "plan.context_placeholder": "Ej: Pelea en 3 semanas, rival zurdo, pelea a 10 rounds...",
    "plan.generate": "Generar plan de combate",
    "plan.generating": "Generando plan con IA...",
    "plan.download_pdf": "Descargar PDF",
    "plan.prediction": "Predicción del combate",

    // Deportes
    "sport.boxing": "Boxeo",
    "sport.mma": "MMA",
    "sport.judo": "Judo",
    "sport.kickboxing": "Kickboxing",
    "sport.muay_thai": "Muay Thai",
    "sport.bjj": "BJJ",
    "sport.karate": "Karate",
    "sport.taekwondo": "Taekwondo",
    "sport.wrestling": "Lucha",
    "sport.other": "Otro",

    // Guardias
    "stance.orthodox": "Orthodox",
    "stance.southpaw": "Southpaw",
    "stance.switch": "Switch",
    "stance.na": "N/A",

    // General
    "general.save": "Guardar",
    "general.cancel": "Cancelar",
    "general.delete": "Borrar",
    "general.edit": "Editar",
    "general.back": "← Volver",
    "general.loading": "Cargando...",
    "general.error": "Error",
    "general.success": "Guardado correctamente",
    "general.confirm_delete": "¿Estás seguro? Esta acción no se puede deshacer.",

    // Auth
    "auth.login": "Iniciar sesión",
    "auth.register": "Crear cuenta",
    "auth.logout": "Cerrar sesión",
    "auth.email": "Email",
    "auth.password": "Contraseña",
    "auth.name": "Tu nombre",
    "auth.no_account": "¿No tienes cuenta?",
    "auth.have_account": "¿Ya tienes cuenta?",
    "auth.create_free": "Crear cuenta gratis",
    "auth.wrong_credentials": "Email o contraseña incorrectos",
    "auth.passwords_no_match": "Las contraseñas no coinciden",
    "auth.password_short": "La contraseña debe tener al menos 8 caracteres",

    // Footer
    "footer.tagline": "Plataforma táctica para deportes de combate",
  },

  en: {
    // Navigation
    "nav.home": "Home",
    "nav.new_fighter": "New fighter",
    "nav.new_plan": "New plan",
    "nav.logout": "Logout",

    // Dashboard
    "dashboard.title": "Combat Strategy Plan",
    "dashboard.subtitle": "Create profiles for your fighter and the rival, analyze fight videos with AI, and generate a complete tactical plan in PDF.",
    "dashboard.our_fighter": "+ Our fighter",
    "dashboard.opponent": "+ Opponent",
    "dashboard.generate_plan": "→ Generate fight plan",
    "dashboard.our_fighters": "Our fighters",
    "dashboard.opponents": "Opponents",
    "dashboard.no_fighters": "No fighters registered yet.",
    "dashboard.no_opponents": "No opponents registered yet.",
    "dashboard.create_one": "Create one",

    // Fighter
    "fighter.new_our": "New fighter — Our team",
    "fighter.new_opponent": "New opponent — Rival",
    "fighter.name": "Full name",
    "fighter.sport": "Sport",
    "fighter.country": "Country",
    "fighter.age": "Age",
    "fighter.weight": "Weight (kg)",
    "fighter.division": "Division / Weight class",
    "fighter.height": "Height (cm)",
    "fighter.reach": "Reach (cm)",
    "fighter.stance": "Stance",
    "fighter.record": "Record",
    "fighter.wins": "Wins",
    "fighter.losses": "Losses",
    "fighter.draws": "Draws",
    "fighter.ko_wins": "KOs / TKOs",
    "fighter.sub_wins": "Submissions",
    "fighter.experience": "Years of experience",
    "fighter.notes": "Coach notes",
    "fighter.save": "Save fighter",
    "fighter.saving": "Saving...",
    "fighter.profile": "Consolidated tactical profile",
    "fighter.generate_profile": "Generate / update",
    "fighter.fights": "Analyzed fights",
    "fighter.add_fight": "+ Add fight",
    "fighter.analyze": "Analyze",
    "fighter.analyzing": "Analyzing...",
    "fighter.edit": "Edit profile",
    "fighter.delete": "Delete fighter",

    // Fights
    "fight.youtube_url": "YouTube link",
    "fight.title": "Title / description",
    "fight.opponent": "Opponent in this fight",
    "fight.result": "Result",
    "fight.date": "Date",
    "fight.notes": "Coach notes for this fight",
    "fight.add": "Add fight",
    "fight.win": "Win",
    "fight.loss": "Loss",
    "fight.draw": "Draw",

    // Analysis
    "analysis.failed": "FAILED",
    "analysis.completed": "COMPLETED",
    "analysis.pending": "PENDING",
    "analysis.processing": "PROCESSING",
    "analysis.no_video": "No video",

    // Plan
    "plan.new": "New fight plan",
    "plan.our_fighter": "Our fighter",
    "plan.opponent": "Opponent",
    "plan.select_fighter": "Select fighter...",
    "plan.select_opponent": "Select opponent...",
    "plan.context": "Additional context (optional)",
    "plan.context_placeholder": "E.g.: Fight in 3 weeks, southpaw rival, 10-round fight...",
    "plan.generate": "Generate fight plan",
    "plan.generating": "Generating plan with AI...",
    "plan.download_pdf": "Download PDF",
    "plan.prediction": "Fight prediction",

    // Sports
    "sport.boxing": "Boxing",
    "sport.mma": "MMA",
    "sport.judo": "Judo",
    "sport.kickboxing": "Kickboxing",
    "sport.muay_thai": "Muay Thai",
    "sport.bjj": "BJJ",
    "sport.karate": "Karate",
    "sport.taekwondo": "Taekwondo",
    "sport.wrestling": "Wrestling",
    "sport.other": "Other",

    // Stances
    "stance.orthodox": "Orthodox",
    "stance.southpaw": "Southpaw",
    "stance.switch": "Switch",
    "stance.na": "N/A",

    // General
    "general.save": "Save",
    "general.cancel": "Cancel",
    "general.delete": "Delete",
    "general.edit": "Edit",
    "general.back": "← Back",
    "general.loading": "Loading...",
    "general.error": "Error",
    "general.success": "Saved successfully",
    "general.confirm_delete": "Are you sure? This action cannot be undone.",

    // Auth
    "auth.login": "Log in",
    "auth.register": "Create account",
    "auth.logout": "Log out",
    "auth.email": "Email",
    "auth.password": "Password",
    "auth.name": "Your name",
    "auth.no_account": "Don't have an account?",
    "auth.have_account": "Already have an account?",
    "auth.create_free": "Create free account",
    "auth.wrong_credentials": "Incorrect email or password",
    "auth.passwords_no_match": "Passwords don't match",
    "auth.password_short": "Password must be at least 8 characters",

    // Footer
    "footer.tagline": "Tactical platform for combat sports",
  }
};

/**
 * Detecta el idioma del navegador/teléfono.
 * Si es español → 'es'. Si es cualquier otro → 'en'.
 */
function detectLanguage() {
  const saved = localStorage.getItem('combat_lang');
  if (saved && ['es', 'en'].includes(saved)) return saved;

  const browserLang = navigator.language || navigator.userLanguage || 'en';
  return browserLang.toLowerCase().startsWith('es') ? 'es' : 'en';
}

/**
 * Cambia el idioma manualmente y recarga la página.
 */
function setLanguage(lang) {
  localStorage.setItem('combat_lang', lang);
  location.reload();
}

/**
 * Traduce una clave. Si no existe en el idioma actual, usa inglés como fallback.
 */
function t(key) {
  const lang = detectLanguage();
  return (TRANSLATIONS[lang] && TRANSLATIONS[lang][key])
    || TRANSLATIONS['en'][key]
    || key;
}

/**
 * Aplica traducciones a todos los elementos con data-i18n="clave"
 * Usar en el body onload o DOMContentLoaded.
 */
function applyTranslations() {
  const lang = detectLanguage();
  document.documentElement.lang = lang;

  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const translation = (TRANSLATIONS[lang] && TRANSLATIONS[lang][key])
      || TRANSLATIONS['en'][key];
    if (translation) {
      if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.placeholder = translation;
      } else {
        el.textContent = translation;
      }
    }
  });

  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    const translation = (TRANSLATIONS[lang] && TRANSLATIONS[lang][key])
      || TRANSLATIONS['en'][key];
    if (translation) el.placeholder = translation;
  });
}

// Aplicar traducciones cuando carga el DOM
document.addEventListener('DOMContentLoaded', applyTranslations);
