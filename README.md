# Calculadora Simplex — Programación Lineal

**Autor:** Prof. Neme Gastón

Calculadora profesional de Programación Lineal para estudiantes y docentes de Métodos Cuantitativos / Investigación Operativa. Resuelve problemas con **n** variables y **m** restricciones mediante el **Método Simplex** (tableau paso a paso, con aritmética exacta en fracciones) y el **Método Gráfico** (para 2 variables), e incluye análisis de sensibilidad, dualidad y programación entera (Branch & Bound).

Es una calculadora **sin estado en el servidor**: no hay base de datos ni login. Cada resolución es un único request/response; el estado de la UI (problema actual, iteración seleccionada, preferencias) vive solo en el cliente.

## Capacidades

- Maximización y minimización, restricciones `≤`/`≥`/`=`, variables con o sin restricción de no negatividad.
- Conversión automática a forma estándar (holguras, excesos, artificiales).
- Simplex tabular completo: **Método de las Dos Fases** (por defecto) y **Gran M** (alternativo, con el término `M` mostrado de forma simbólica y exacta: `3 - 2M`, no un número gigante aproximado).
- Cada iteración devuelve el tableau completo, variable entrante/saliente, elemento pivote, prueba de la razón mínima y una explicación en español de qué ocurrió.
- Aritmética **exacta con fracciones** en todo el motor, con toggle fracción/decimal en la UI.
- Detección explícita de: solución no acotada, infactible, óptimos alternativos y degeneración — cada una con su propio mensaje pedagógico.
- **Método gráfico** interactivo (Plotly) para 2 variables: región factible, vértices con su Z, barrido animado de la función objetivo, zoom/pan/exportar imagen, con tabla de datos accesible equivalente.
- **Análisis de sensibilidad**: rangos de los coeficientes de la función objetivo y del RHS, precios sombra.
- **Dual**: formulación automática (reglas generales/asimétricas, válidas para cualquier combinación de sentido y tipo de restricción), solución y verificación de holgura complementaria.
- **Programación entera/binaria**: Branch & Bound con árbol de ramificación visual (nodos, cotas, motivo de poda).
- Exportar el resumen + gráfico como imagen (PNG) o PDF.
- Modo claro/oscuro, totalmente responsive (375 / 768 / 1024 / 1440px), accesible (WCAG AA, foco visible, estado nunca solo por color).

## Arquitectura

```
simplex-solver/
├── backend/                 Python 3.12 + FastAPI + Pydantic v2
│   ├── app/
│   │   ├── core/
│   │   │   ├── models.py            Modelos de dominio (LPProblem, etc.)
│   │   │   ├── standard_form.py     Conversión a forma estándar
│   │   │   ├── validation.py        Parseo/validación numérica
│   │   │   ├── graphical.py         Geometría del método gráfico
│   │   │   ├── sensitivity.py       Rangos y precios sombra
│   │   │   ├── duality.py           Dual + holgura complementaria
│   │   │   ├── branch_and_bound.py  Programación entera
│   │   │   └── simplex/
│   │   │       ├── pivot.py         Motor de pivoteo genérico
│   │   │       ├── engine_loop.py   Bucle de iteración compartido
│   │   │       ├── two_phase.py     Método de las Dos Fases
│   │   │       ├── big_m.py         Método de Gran M
│   │   │       └── big_m_number.py  Aritmética simbólica con M
│   │   ├── schemas/                 Pydantic request/response
│   │   ├── api/routes.py            POST /api/solve, GET /api/examples
│   │   └── examples.py              Problemas de ejemplo precargados
│   └── tests/                       pytest (motor + API)
├── frontend/                 Next.js 15 (App Router) + React 19 + TypeScript
│   ├── app/                         Layout raíz, tokens de diseño
│   ├── components/
│   │   ├── problem-form/            Formulario dinámico (variables/restricciones)
│   │   ├── results/                 Tabs de resultados, tableau, gráfico, etc.
│   │   ├── layout/                  AppShell, ThemeToggle
│   │   └── ui/                      Primitivas shadcn/ui
│   ├── lib/                         Cliente API, formato de fracciones/KaTeX
│   └── store/                       Zustand (problema actual, UI)
├── docker-compose.yml
└── .github/workflows/ci.yml
```

### Decisión de stack backend

**Python 3.12 + FastAPI + Pydantic v2**, por cuatro razones concretas:

1. `fractions.Fraction` (stdlib) da aritmética racional exacta sin dependencias extra — necesario para mostrar `7/3` en el tableau en vez de `2.333333`.
2. `scipy.optimize.linprog`/`milp` permite validar cruzadamente cada resultado del motor en los tests (Fraction → float, comparado contra la solución de scipy), algo sin equivalente igual de maduro en Node.
3. Pydantic v2 da validación de esquema y errores de campo claros, con el mismo modelo mental que Zod en el frontend.
4. FastAPI/Uvicorn se containeriza trivialmente y expone documentación OpenAPI gratis (`/docs`).

### Decisiones técnicas destacadas

- **Motor de pivoteo único y genérico** (`pivot.py` + `engine_loop.py`): tanto Dos Fases como Gran M usan el mismo bucle de iteración, operando por duck typing sobre `Fraction` o `BigMNumber`. Regla de Bland como salvaguarda anti-ciclos en casos degenerados.
- **Gran M simbólico**: `BigMNumber(const, coefM)` guarda la parte constante y el coeficiente de `M` por separado, comparando primero por `coefM` — el tableau puede mostrar `3 - 2M` de forma exacta.
- **Protección de artificiales degeneradas**: si una variable artificial queda en la base con valor 0 tras la Fase 1, la prueba de la razón mínima la protege explícitamente (fuerza razón 0 ante cualquier coeficiente no nulo, incluso negativo) para que un pivote posterior no la reactive silenciosamente a un valor positivo — esto evitaba un bug real donde el motor podía reportar como "óptimo" un punto que en realidad violaba una restricción.
- **Sensibilidad y dual siempre vía Dos Fases**: independientemente del método que el usuario elija para ver el tableau, el análisis de sensibilidad y el dual resuelven internamente con Dos Fases, para obtener un tableau final sin términos `M` y evitar la complejidad de rangos con aritmética simbólica.
- **El gráfico nunca decide su propio estado**: `graphical.py` reutiliza el `SolveStatus` que ya calculó el Simplex en vez de re-derivarlo geométricamente, para que la pestaña Resumen y la pestaña Gráfico nunca puedan contradecirse.
- **Branch & Bound** reutiliza el motor Simplex existente para cada nodo (relajación LP + restricciones de cota acumuladas), rama sobre la variable más fraccionaria, y poda por infactibilidad/cota/integralidad. Variables binarias se acotan agregando automáticamente `x ≤ 1`.
- **LaTeX se genera en el frontend**, no en el backend: el backend manda coeficientes/nombres de variable estructurados; `lib/katex-helpers.ts` arma las cadenas KaTeX. Evita duplicar lógica de formato en dos lenguajes.
- **Sin React Query**: cada resolución es una única llamada POST sin necesidad de cache; un hook simple + Zustand alcanza.

## Cómo correr el proyecto

### Con Docker (recomendado)

Requiere Docker y Docker Compose.

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000 (docs interactivas en `/docs`)

Variables opcionales (con valores por defecto ya funcionales): `CORS_ORIGINS` para el backend, `NEXT_PUBLIC_API_URL` para el frontend — ver `docker-compose.yml`.

### Sin Docker

**Backend** (Python 3.12):

```bash
cd backend
python -m venv .venv
./.venv/Scripts/activate      # Windows (PowerShell/Git Bash: .venv/Scripts/activate)
# source .venv/bin/activate   # macOS/Linux
pip install -e ".[dev]"
cp .env.example .env          # ajustar CORS_ORIGINS si el frontend corre en otro puerto
uvicorn app.main:app --reload --port 8000
```

**Frontend** (Node 20+):

```bash
cd frontend
npm install
cp .env.example .env.local    # NEXT_PUBLIC_API_URL debe apuntar al backend
npm run dev
```

Por defecto el frontend corre en el puerto que definas (en este repo se usó `3007` en desarrollo vía `.claude/launch.json`); ajustá `NEXT_PUBLIC_API_URL` y `CORS_ORIGINS` según el puerto real que uses.

## Variables de entorno

| Variable | Dónde | Default | Descripción |
|---|---|---|---|
| `CORS_ORIGINS` | `backend/.env` | `http://localhost:3000` | Orígenes permitidos por CORS, separados por coma |
| `NEXT_PUBLIC_API_URL` | `frontend/.env.local` | `http://localhost:8000` | URL base del backend que consume el cliente |

## Tests y linting

```bash
# Backend
cd backend
pytest -v
ruff check app tests
black --check app tests

# Frontend
cd frontend
npm run test
npm run lint
npx tsc --noEmit
```

CI mínimo en `.github/workflows/ci.yml` corre ambas suites (lint + tests + build del frontend) en cada push/PR.

## Endpoint principal

`POST /api/solve` recibe el problema (sentido, coeficientes de la función objetivo, restricciones, tipo de variable, método) y devuelve: forma estándar, iteraciones completas del tableau, solución y estado, datos del gráfico (si hay 2 variables), sensibilidad, dual y — si hay variables enteras/binarias — el árbol de Branch & Bound. `GET /api/examples` devuelve los problemas de ejemplo precargados que usa el botón "Cargar ejemplo" del formulario.

## Limitaciones conocidas

- El rango de sensibilidad de los coeficientes objetivo no se calcula para variables libres (sin restricción de signo): perturbar su coeficiente afecta simultáneamente a las dos columnas en las que se dividen internamente, y esa perturbación conjunta queda fuera del alcance actual.
- Branch & Bound tiene un tope de seguridad de 500 nodos explorados, pensado para problemas de tamaño de curso (no para instancias combinatorias grandes).
- No hay persistencia ni autenticación: es intencional, la app es una calculadora sin estado en el servidor.
