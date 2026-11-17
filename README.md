# Taller 2 – API REST Segura con FastAPI: Autenticación, Autorización y Migraciones – Biblioteca

API REST completa de nivel de producción construida con **FastAPI**, **SQLAlchemy 2.0**, **Alembic**, **PostgreSQL**, **Argon2** y **JWT**. Implementa configuración centralizada por entorno con Pydantic-Settings, migraciones versionadas de base de datos, autenticación con flujo OAuth2 Password (Access Token y Refresh Token con rotación y detección de robo), autorización basada en roles (RBAC) y control de propiedad de recursos, paginación estandarizada, auditoría por request ID, rate limiting con SlowAPI y manejo controlado de excepciones.

---

## 👥 Integrantes
- **Aprendiz:** Julian Remolina
- **Programa:** Análisis y Desarrollo de Software (ADSO) - SENA
- **Repositorio:** `Taller2_API_FastAPI_Segura_Julian_Remolina`

---

## 🏛️ Estructura del Proyecto

```
biblioteca/
├── app/
│   ├── main.py              # Aplicación FastAPI, routers v1, middlewares (CORS, Request ID, logs), rate limit y manejadores de error
│   ├── core/
│   │   ├── config.py        # Configuración tipada leída desde .env con pydantic-settings
│   │   ├── database.py      # Engine, SessionLocal, Base con naming convention
│   │   ├── dependencies.py  # Inyección de dependencias (SessionDep, CurrentUser, requiere_rol, PaginacionDep)
│   │   ├── exceptions.py    # Excepciones propias (NoAutenticado, Prohibido, CuentaBloqueada, NoEncontrado, Conflicto, ReglaNegocio)
│   │   ├── limiter.py       # Instancia de SlowAPI Limiter para rate limiting
│   │   └── security.py      # Hashing Argon2 y creación/verificación de JWT con PyJWT
│   ├── models/              # Modelos ORM SQLAlchemy 2.0
│   │   ├── autor.py
│   │   ├── categoria.py
│   │   ├── libro.py         # Modelo Libro y tabla intermedia libro_categoria
│   │   ├── prestamo.py      # Modelo Prestamo (+ multa_pagada, registrado_por_id)
│   │   ├── socio.py
│   │   ├── usuario.py       # Modelo Usuario (+ rol Enum rolusuario)
│   │   └── refresh_token.py # Modelo RefreshToken con jti
│   ├── schemas/             # Esquemas de validación y serialización Pydantic
│   │   ├── auth.py          # TokenRespuesta, RefreshTokenSolicitud, PasswordCambiar
│   │   ├── autor.py
│   │   ├── categoria.py
│   │   ├── libro.py
│   │   ├── pagina.py        # Esquema genérico Pagina[T] con items, total, skip, limit
│   │   ├── prestamo.py
│   │   ├── reportes.py
│   │   ├── socio.py
│   │   └── usuario.py       # UsuarioRegistro, UsuarioCrear, UsuarioRespuesta, SocioActualizarPropio
│   ├── controllers/         # Lógica de negocio y consultas a la base de datos
│   │   ├── auth.py
│   │   ├── autor.py
│   │   ├── categoria.py
│   │   ├── libro.py
│   │   ├── prestamo.py
│   │   ├── reportes.py
│   │   ├── socio.py
│   │   └── usuario.py
│   ├── routes/              # Routers HTTP bajo el prefijo /api/v1
│   │   ├── auth.py
│   │   ├── autor.py
│   │   ├── categoria.py
│   │   ├── health.py        # Endpoint /api/v1/health
│   │   ├── libro.py
│   │   ├── prestamo.py
│   │   ├── reportes.py
│   │   ├── socio.py
│   │   └── usuario.py
│   └── scripts/
│       └── crear_admin.py   # Creación del primer administrador por consola interactiva
├── alembic/
│   ├── env.py               # Conexión leída desde pydantic-settings y metadatos
│   └── versions/            # Migraciones versionadas
│       ├── 0001_estado_inicial.py
│       ├── 0002_multa_pagada.py
│       ├── 0003_usuarios.py
│       ├── 0004_refresh_tokens.py
│       └── 0005_auditoria_prestamos.py
├── tests/
│   ├── conftest.py          # Fixtures de pytest, base de datos de test y cliente TestClient
│   ├── test_taller.py       # Flujo completo con los 33 casos de prueba del taller
│   └── test_mas_cobertura.py# Pruebas adicionales para cobertura de código superior al 70%
├── .env.example             # Plantilla de variables de entorno
├── alembic.ini              # Archivo de configuración de Alembic
├── Dockerfile               # Definición de contenedor para despliegue
├── docker-compose.yml       # Orquestación de PostgreSQL y API
├── requirements.txt         # Dependencias de producción
├── requirements-dev.txt     # Dependencias de desarrollo y pruebas
├── seed.py                  # Script para cargar datos de prueba iniciales
└── README.md                # Documentación del proyecto
```

---

## 📦 Librerías y Tecnologías Utilizadas

| Librería | Versión | Uso |
|---|---|---|
| `fastapi[standard]` | `>=0.115` | Framework web, servidor Uvicorn, CLI FastAPI, formulación multipart |
| `sqlalchemy` | `>=2.0` | ORM con sintaxis 2.0 (`select`, `Mapped`, convenciones de metadatos) |
| `psycopg[binary]` | `>=3.2` | Driver PostgreSQL para Python |
| `alembic` | `>=1.13` | Control de versiones y migraciones de esquemas en base de datos |
| `pydantic-settings` | `>=2.4` | Lectura tipada de configuración y variables de entorno (`.env`) |
| `pyjwt` | `>=2.9` | Emisión y validación segura de JSON Web Tokens (HS256) |
| `pwdlib[argon2]` | `>=0.2` | Hashing moderno y seguro de contraseñas con Argon2 |
| `slowapi` | `>=0.1.9` | Rate limiting por dirección IP |
| `pytest` y `pytest-cov`| `>=8.0` | Pruebas automatizadas y análisis de cobertura |

---

## ⚙️ Variables de Entorno (`.env`)

Cree un archivo `.env` en la raíz del proyecto tomando como base `.env.example`:

```env
# Conexión a la base de datos principal
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/biblioteca

# Base de datos exclusiva para pruebas unitarias con pytest
TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/biblioteca_test

# Seguridad y Firma de JWT (mínimo 32 caracteres generados con secrets)
SECRET_KEY=su_clave_secreta_de_al_menos_32_caracteres_aleatorios
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Frontends autorizados en CORS (formato JSON)
CORS_ORIGINS=["http://localhost:5173"]

# Entorno de ejecución: dev | test | prod
ENVIRONMENT=dev
```

Para generar una clave secreta segura de 32 bytes:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🚀 Instalación y Puesta en Marcha

### 1. Clonar el Repositorio y Crear Entorno Virtual
```bash
git clone <URL_DEL_REPOSITORIO>
cd Taller2_API_FastAPI_Segura_Julian_Remolina

# Crear entorno virtual
python -m venv .venv

# Activar entorno virtual
# En Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# En Linux/macOS:
source .venv/bin/activate
```

### 2. Instalar Dependencias
```bash
pip install -r requirements-dev.txt
```

### 3. Levantar la Base de Datos PostgreSQL
Con Docker Compose:
```bash
docker compose up -d db
```

O utilizando una instancia local de PostgreSQL asegurando tener creadas las bases de datos `biblioteca` y `biblioteca_test`.

### 4. Aplicar Migraciones con Alembic
```bash
alembic upgrade head
```

Para verificar o revertir migraciones:
```bash
# Revertir la última migración
alembic downgrade -1

# Revertir todas las migraciones
alembic downgrade base

# Volver al estado más reciente
alembic upgrade head

# Ver la versión actual de la base de datos
alembic current
```

### 5. Crear el Primer Administrador
La creación de administradores está protegida y no se permite por la API pública:
```bash
python -m app.scripts.crear_admin
```
Ingrese por consola el correo electrónico, nombre y contraseña del administrador.

### 6. Ejecutar la API en Modo Desarrollo
```bash
fastapi dev app/main.py
# o con uvicorn:
uvicorn app.main:app --reload --port 8000
```
La documentación interactiva estará disponible en:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🛡️ Roles del Sistema y Matriz de Permisos

El sistema implementa tres roles definidos mediante el enum `rolusuario`:

1. **Anónimo:** Usuarios no autenticados (sin token Bearer).
2. **Socio:** Usuario vinculado a un registro de la tabla `socios`.
3. **Bibliotecario:** Empleado responsable de gestionar catálogo, préstamos y devoluciones.
4. **Admin:** Administrador total del sistema.

### Matriz de Permisos

| Endpoint | Método | Anónimo | Socio | Bibliotecario | Admin |
|---|---|:---:|:---:|:---:|:---:|
| `/api/v1/health` | GET | ✅ | ✅ | ✅ | ✅ |
| `/api/v1/auth/registro` | POST | ✅ | ✅ | ✅ | ✅ |
| `/api/v1/auth/login` | POST | ✅ | ✅ | ✅ | ✅ |
| `/api/v1/auth/refresh` | POST | ✅ | ✅ | ✅ | ✅ |
| `/api/v1/auth/logout` | POST | ❌ | ✅ | ✅ | ✅ |
| `/api/v1/auth/me` | GET | ❌ | ✅ | ✅ | ✅ |
| `/api/v1/auth/me/password` | PATCH | ❌ | ✅ | ✅ | ✅ |
| `/api/v1/libros`, `/autores`, `/categorias` | GET | ✅ | ✅ | ✅ | ✅ |
| `/api/v1/libros`, `/autores`, `/categorias` | POST / PATCH | ❌ | ❌ | ✅ | ✅ |
| `/api/v1/libros/{id}`, `/autores/{id}`, `/categorias/{id}` | DELETE | ❌ | ❌ | ❌ | ✅ |
| `/api/v1/socios/me` | GET / PATCH | ❌ | ✅ (Propio) | ❌ | ❌ |
| `/api/v1/socios/me/prestamos` | GET | ❌ | ✅ (Propio) | ❌ | ❌ |
| `/api/v1/socios/me/multas` | GET | ❌ | ✅ (Propio) | ❌ | ❌ |
| `/api/v1/socios` | GET, POST | ❌ | ❌ | ✅ | ✅ |
| `/api/v1/socios/{id}` | GET, PATCH | ❌ | ❌ | ✅ | ✅ |
| `/api/v1/socios/{id}` | DELETE | ❌ | ❌ | ❌ | ✅ |
| `/api/v1/prestamos` | GET | ❌ | ✅ (Filtrado) | ✅ | ✅ |
| `/api/v1/prestamos/{id}` | GET | ❌ | ✅ (Propio o 404) | ✅ | ✅ |
| `/api/v1/prestamos` | POST | ❌ | ❌ | ✅ | ✅ |
| `/api/v1/prestamos/{id}/devolucion` | POST | ❌ | ❌ | ✅ | ✅ |
| `/api/v1/prestamos/{id}/pago-multa` | POST | ❌ | ❌ | ✅ | ✅ |
| `/api/v1/reportes/*` | GET | ❌ | ❌ | ✅ | ✅ |
| `/api/v1/usuarios` (todos) | GET, POST, PATCH | ❌ | ❌ | ❌ | ✅ |

---

## 📜 Reglas Implementadas

### Reglas de Negocio (R1 a R11)
- **R1:** El socio existe al pedir préstamo (HTTP 404).
- **R2:** El libro existe al pedir préstamo (HTTP 404).
- **R3:** El socio debe estar activo (HTTP 422).
- **R4:** El socio no puede tener préstamos vencidos (HTTP 422).
- **R5:** El socio no puede tener más de 3 préstamos activos sin devolver (HTTP 422).
- **R6:** El socio no puede tener en préstamo dos veces el mismo libro simultáneamente (HTTP 409).
- **R7:** El libro debe tener ejemplares disponibles (HTTP 422).
- **R8:** La fecha límite se calcula como `fecha_prestamo + dias`.
- **R9:** La devolución valida existencia, que no haya sido devuelto previamente y que la fecha de devolución no sea anterior a la de préstamo.
- **R10:** Si hay días de retraso, se liquida multa a $0.50 por día de mora.
- **R11:** Un socio con multas pendientes no pagadas no puede solicitar nuevos préstamos (HTTP 422 "El socio tiene multas pendientes").

### Reglas de Autenticación (A1 a A7)
- **A1:** Validación de email y contraseña. El mensaje es idéntico si el email no existe o la clave es incorrecta (`401 "Credenciales inválidas"`).
- **A2:** Validación de usuario activo (`403 "Usuario inactivo"`).
- **A3:** Tras 5 intentos fallidos consecutivos, la cuenta se bloquea por 15 minutos (`423 "Cuenta bloqueada temporalmente"`).
- **A4:** El access token debe existir, tener firma válida y no estar vencido.
- **A5:** Un refresh token no puede ser utilizado como access token ni viceversa (`claim type`).
- **A6:** Rotación de refresh tokens: al usarse, se revoca el token y se emite uno nuevo. Si se reutiliza un token revocado, se revocan todos los refresh tokens del usuario por seguridad contra robo.
- **A7:** `get_current_user` consulta al usuario en base de datos en cada petición; si fue desactivado, su token vigente queda rechazado de inmediato.

### Reglas de Autorización (Z1 a Z7)
- **Z1:** Verificación estricta de roles según la matriz (HTTP 403).
- **Z2:** Un socio que intenta consultar un préstamo ajeno recibe HTTP 404 (evita revelar la existencia de recursos ajenos).
- **Z3:** En `GET /prestamos`, el socio solo recibe sus préstamos incluso si especifica `?socio_id=` de otro socio.
- **Z4:** El socio no puede alterar su email, rol o estado activo mediante `PATCH /socios/me` (`extra="forbid"`, HTTP 422).
- **Z5:** Debe existir al menos un administrador activo; un admin no puede quitarse su rol ni desactivarse a sí mismo (HTTP 422).
- **Z6:** Cambiar el rol o desactivar a un usuario revoca de forma automática todos sus refresh tokens.
- **Z7:** Cada préstamo almacena en `registrado_por_id` el ID del usuario que realizó la operación (Auditoría).

---

## 🧪 Pruebas Automatizadas y Cobertura

Para ejecutar todas las pruebas automatizadas y generar el reporte de cobertura:

```bash
pytest --cov=app --cov-report=term-missing
```

### Resultados de Cobertura
- **Cobertura total obtenida:** **80%** (Superando el requisito mínimo del 70%).
- **Casos probados:** Los 33 casos de prueba del taller implementados y verificados.

---

## 🐳 Despliegue con Docker

Para levantar la arquitectura completa (Base de datos PostgreSQL + API con migraciones automáticas):

```bash
docker compose up --build
```

El servicio estará disponible en `http://localhost:8000`.
