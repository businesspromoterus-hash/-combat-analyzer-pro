# Deploy desde iPhone — Combat Analyzer Pro

Guía 100% mobile. Todo desde Safari del iPhone. Sin computadora. Sin terminal.

**Arquitectura:** Gemini analiza videos → Claude diseña el plan ganador.

---

## ⏱ Tiempo total: 25-30 minutos

---

## PARTE 1 — API Keys (10 min)

### 1.1 Gemini API key (motor de análisis de video)

1. Safari → **https://aistudio.google.com/apikey**
2. Login con tu cuenta de Google
3. Toca **"Create API key"** → selecciona un proyecto
4. Copia la key (empieza con `AIza...`) → guárdala en Notas

### 1.2 Anthropic API key (motor de estrategia)

1. Safari → **https://console.anthropic.com**
2. Crear cuenta (o login)
3. Anthropic da **$5 de crédito gratis** para empezar
4. Ve a **"API Keys"** en el menú lateral
5. Toca **"Create Key"** → ponle nombre "combat-analyzer"
6. Copia la key (empieza con `sk-ant-...`) → guárdala en Notas

⚠️ **Importante:** ambas keys son como contraseñas. No las compartas ni las subas a un repo público.

---

## PARTE 2 — Subir código a GitHub (10 min)

### 2.1 Crear cuenta de GitHub (si no tienes)

1. Safari → **https://github.com/signup**
2. Email, contraseña, username, verifica email

### 2.2 Crear repositorio

1. Logueado, toca **"+"** arriba derecha → **"New repository"**
2. Nombre: `combat-analyzer-pro`
3. **Privacy: Private** (importante)
4. NO marques "Initialize with README"
5. Toca **"Create repository"**

### 2.3 Subir el código

1. Toca el ZIP `combat-analyzer-pro.zip` en Notas/Files → iOS lo descomprime
2. En el repo de GitHub, toca **"uploading an existing file"**
3. Toca **"choose your files"**
4. Navega a la carpeta `combat-analyzer` descomprimida
5. Selecciona **TODOS los archivos y subcarpetas** de adentro
6. Espera la subida (1-2 min)
7. Commit message: `Initial commit`
8. Toca **"Commit changes"**

---

## PARTE 3 — Deploy en Railway (10 min)

### 3.1 Crear cuenta de Railway

1. Safari → **https://railway.app**
2. **"Login with GitHub"** → autoriza
3. Railway te da $5 de crédito de prueba

### 3.2 Crear proyecto

1. Dashboard → **"+ New Project"**
2. **"Deploy from GitHub repo"**
3. Autoriza acceso si pide
4. Selecciona **`combat-analyzer-pro`**
5. Railway empieza a buildear (3-5 min)

### 3.3 Variables de entorno

Mientras buildea, ve a la pestaña **"Variables"** y añade UNA POR UNA:

```
GEMINI_API_KEY=AIza... (tu key de Google)
ANTHROPIC_API_KEY=sk-ant-... (tu key de Anthropic)
DEFAULT_VIDEO_ENGINE=gemini
DEFAULT_STRATEGY_ENGINE=claude
ENVIRONMENT=production
SECRET_KEY=combat-analyzer-cambiar-luego
```

Railway redeploya automáticamente cuando guardas variables.

### 3.4 Generar dominio público

1. Pestaña **"Settings"** → sección **"Networking"** (o "Domains")
2. Toca **"Generate Domain"**
3. Te da una URL tipo: `combat-analyzer-pro-production.up.railway.app`
4. **¡Copia esa URL!**

---

## PARTE 4 — Probar desde el iPhone (5 min)

1. Espera deploy en verde / Active (revisa pestaña "Deployments")
2. Abre la URL de Railway en Safari
3. Si carga el dashboard de Combat Analyzer Pro: 🎉 ¡FUNCIONA!
4. **Verifica motores activos:** en el dashboard debes ver Gemini y Claude en verde
5. **Flujo de prueba:**
   - **+ Nuestro peleador** → llenar datos básicos
   - **+ Oponente** → llenar datos básicos
   - Tocar el oponente → agregar 1 link de YouTube CORTO (5-10 min)
   - **🤖 Analizar** → espera 1-3 min (Gemini procesa el video)
   - **🔄 Generar perfil** → espera 30-60 seg (Claude sintetiza)
   - Repetir con nuestro peleador
   - **Nuevo plan** → elegir ambos → **Generar plan**
   - Espera 1-2 min (Claude diseña la estrategia completa)
   - Descargar el PDF profesional

---

## Costos esperados durante MVP

- **GitHub:** gratis (repo privado)
- **Gemini API:** gratis hasta 15 req/min (suficiente para MVP)
- **Anthropic API:** $5 crédito gratis. Cada plan completo cuesta ~$0.10-0.30 con Claude
- **Railway:** $5 crédito gratis inicial. Después $5/mes mínimo si lo mantienes

Para validar el MVP completo gastarás <$1 de Anthropic y <$0 de Gemini.

---

## Problemas comunes

### "Application failed to respond"
- Verifica variables de entorno (especialmente las API keys)
- Mira logs: Railway → pestaña **"Deployments"** → último deploy → "View logs"

### "Engine claude no está configurado"
- Revisa que `ANTHROPIC_API_KEY` está en Variables y bien escrita
- La key debe empezar con `sk-ant-`

### El análisis tarda mucho
- Videos largos (>15 min) con Gemini pueden tardar varios minutos
- Para validar, usa videos cortos primero (5-10 min)

### La UI se ve rara en iPhone
- Limpia caché de Safari y recarga
- Mándame screenshot del problema y lo arreglo

---

## Cuando termines

Reporta:
- ✅ Tu URL pública si funcionó
- ❌ El error específico y el paso donde falló

Y de ahí afinamos.
