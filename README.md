# Combat Analyzer Pro

Plataforma profesional de análisis táctico para deportes de combate (Boxeo, MMA, Judo, Kickboxing, Muay Thai, BJJ, Karate, Taekwondo).

## Misión

Analizar a ambos peleadores (nuestro peleador y el oponente), estudiar sus peleas anteriores con motores de IA, y generar un plan de combate estratégico completo en PDF profesional para entrenador y peleador.

## Arquitectura

**Stack:**
- Backend: Python 3.11+ / FastAPI
- IA: Gemini (video), Claude (estrategia), GPT-4o (visión) — arquitectura multi-motor
- Base de datos: SQLite (MVP) → PostgreSQL (producción)
- Generación PDF: ReportLab
- Frontend: HTML + Tailwind + Alpine.js (server-rendered, ligero)
- Futuro: OpenCV / MediaPipe / OpenPose para análisis biomecánico

**Estructura modular:**
```
app/
├── api/          # Endpoints REST FastAPI
├── core/         # Configuración, seguridad, DB
├── models/       # Modelos SQLAlchemy + Pydantic
├── services/     # Lógica de negocio (peleadores, peleas, planes)
├── engines/      # Motores de IA intercambiables
│   ├── base.py           # Interfaz abstracta
│   ├── gemini_engine.py  # Análisis de video con Gemini
│   ├── claude_engine.py  # Estrategia con Claude
│   ├── openai_engine.py  # Visión con GPT-4o
│   └── registry.py       # Orquestador de motores
└── utils/        # Generación PDF, helpers YouTube, etc.
```

## Flujo del sistema

1. Crear perfil de nuestro peleador
2. Crear perfil del oponente
3. Subir/pegar links de peleas del oponente → análisis IA
4. Subir/pegar links de peleas nuestras → análisis IA
5. Cruce comparativo de ambos perfiles
6. Plan de combate (A, B, C) por rounds
7. Plan que el rival probablemente usará contra nosotros
8. Contramedidas
9. Perfil ideal de sparrings
10. Plan de campamento (físico, técnico, táctico)
11. Reporte PDF profesional

## Instalación

```bash
# Clonar y entrar al proyecto
cd combat-analyzer

# Crear venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus API keys (Gemini, Anthropic, OpenAI)

# Inicializar base de datos
python -m app.core.init_db

# Correr servidor
uvicorn app.main:app --reload --port 8000
```

Abrir http://localhost:8000

## Variables de entorno (.env)

```
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
DATABASE_URL=sqlite:///./combat.db
SECRET_KEY=cambia-esto-en-produccion
UPLOAD_DIR=./uploads
REPORTS_DIR=./reports
MAX_VIDEO_SIZE_MB=500
```

## Roadmap

**MVP (este release):**
- ✅ Perfiles de peleadores
- ✅ Carga de peleas (YouTube + archivo)
- ✅ Análisis con Gemini (video real)
- ✅ Estrategia con Claude
- ✅ Reporte PDF profesional
- ✅ Sistema modular de motores

**Próximas fases:**
- Análisis biomecánico con MediaPipe (postura, ángulos, distancia)
- Detección automática de técnicas con visión computacional
- Dashboard de progreso del campamento
- Multi-usuario con autenticación
- Comparación histórica entre análisis
- App móvil para entrenadores

## Licencia
Propietario. Todos los derechos reservados. 
