# Sistema de Gestión de Biblioteca - API REST

API REST completa construida desde cero con **Python**, **FastAPI**, **SQLAlchemy** y **PostgreSQL**, aplicando el patrón arquitectónico **MVC (Modelo - Vista / Esquema - Controlador)**, validaciones estrictas con **Pydantic**, relaciones complejas de base de datos (1:N y N:M), consultas optimizadas con joins y agregaciones, y reglas de negocio del sistema de préstamos.

---

## 👥 Integrantes
- **Aprendiz:** Camilo Aguirre
- **Programa:** Análisis y Desarrollo de Software (ADSO) - SENA
- **Repositorio:** `Taller_API_FastAPI_camilo_aguirre`

---

## 🏛️ Arquitectura del Proyecto (Patrón MVC)

El proyecto sigue una estricta separación de responsabilidades:

```
biblioteca/
├── app/
│   ├── main.py              # Creación de la aplicación FastAPI, registro de routers y manejador global de excepciones
│   ├── core/
│   │   ├── database.py      # Conexión a PostgreSQL (engine, SessionLocal, Base)
│   │   ├── dependencies.py  # Inyección de dependencias (get_db / SessionDep, paginación reutilizable)
│   │   └── exceptions.py    # Jerarquía de excepciones propias (ErrorAplicacion, NoEncontrado, Conflicto, ReglaNegocio)
│   ├── models/              # Modelos ORM SQLAlchemy (definen tablas y relaciones)
│   │   ├── autor.py
│   │   ├── categoria.py
│   │   ├── libro.py         # Modelo Libro y tabla asociativa libro_categoria
│   │   ├── socio.py
│   │   └── prestamo.py
│   ├── schemas/             # Esquemas Pydantic (validación de entrada y serialización de salida)
│   │   ├── autor.py
│   │   ├── categoria.py
│   │   ├── libro.py
│   │   ├── socio.py
│   │   ├── prestamo.py
│   │   └── reportes.py
│   ├── controllers/         # Lógica de negocio, consultas SQL y lanzamiento de excepciones propias
│   │   ├── autor.py
│   │   ├── categoria.py
│   │   ├── libro.py
│   │   ├── socio.py
│   │   ├── prestamo.py
│   │   └── reportes.py
│   └── routes/              # Endpoints HTTP (validación y llamado a controladores)
│       ├── autor.py
│       ├── categoria.py
│       ├── libro.py
│       ├── socio.py
│       ├── prestamo.py
│       └── reportes.py
├── tests/
│   └── test_taller.py       # Suite de pruebas automatizadas con pytest (24 casos de prueba)
├── seed.py                  # Script para poblar la base de datos con los datos oficiales de prueba
├── .env.example             # Plantilla de variables de entorno
├── .env                     # Variables de entorno locales (ignorado en git)
├── .gitignore               # Exclusión de archivos sensibles y temporales
├── requirements.txt         # Dependencias del proyecto
└── README.md                # Documentación del proyecto
```

### Separación de Responsabilidades:
- **`models`**: Define únicamente las tablas y sus relaciones. No valida datos de entrada.
- **`schemas`**: Valida lo que entra y define la forma de lo que sale con Pydantic. No consulta la base de datos.
- **`controllers`**: Ejecuta las consultas, aplica las reglas de negocio y lanza excepciones propias. **No utiliza HTTPException ni códigos HTTP**.
- **`routes`**: Recibe la petición, delega la ejecución al controlador y define el `response_model` y códigos de estado HTTP. **No escribe consultas SQL**.

---

## ⚙️ Requisitos e Instalación

### 1. Prerrequisitos
- Python 3.10 o superior (probado en Python 3.13)
- PostgreSQL 14 o superior en ejecución
- Base de datos vacía creada en PostgreSQL (por ejemplo, `biblioteca`)

### 2. Clonación o Preparación del Proyecto
```bash
cd "fast api biblioteca"
```

### 3. Crear y Activar el Entorno Virtual
En Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Instalar Dependencias
```bash
pip install -r requirements.txt
```

---

## 🔐 Configuración de Variables de Entorno

Crear el archivo `.env` a partir de `.env.example`:

```bash
cp .env.example .env
```

Configurar la URL de conexión en `.env`:
```env
DATABASE_URL=postgresql+psycopg://usuario:contrasena@localhost:5432/biblioteca
```

> **Ejemplo local:**
> `DATABASE_URL=postgresql+psycopg://postgres:1234@localhost:5432/biblioteca`

---

## 🚀 Ejecución de la API

Para iniciar el servidor en modo desarrollo con recarga automática:

```bash
uvicorn app.main:app --reload
```

La API quedará disponible en:
- **API Base:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Documentación Interactiva (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Documentación Alternativa (ReDoc):** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Poblado de Datos y Pruebas

### Poblar Base de Datos con Datos de Prueba
Para cargar automáticamente los autores, categorías, libros y socios especificados en el taller:
```bash
python seed.py
```

### Ejecutar las Pruebas Automatizadas (24 Casos del Taller)
Para ejecutar la suite completa de pruebas con `pytest`:
```bash
pytest -v -s tests/test_taller.py
```

---

## 📋 Tabla de Endpoints

### 1. Autores (`/autores`)
| Método | Ruta | Parámetros | Descripción | Códigos HTTP |
|---|---|---|---|---|
| `GET` | `/autores` | `skip` (int), `limit` (int), `nacionalidad` (str, opcional) | Lista paginada con filtro opcional | `200` |
| `GET` | `/autores/{id}` | `id` (int) | Consulta un autor | `200`, `404` |
| `GET` | `/autores/{id}/libros` | `id` (int) | Lista los libros del autor | `200`, `404` |
| `POST` | `/autores` | Body JSON (`AutorCreate`) | Crea un autor | `201`, `409`, `422` |
| `PATCH` | `/autores/{id}` | `id` (int), Body JSON (`AutorUpdate`) | Actualiza campos del autor | `200`, `404`, `409`, `422` |
| `DELETE` | `/autores/{id}` | `id` (int) | Elimina un autor (409 si tiene libros) | `204`, `404`, `409` |

### 2. Categorías (`/categorias`)
| Método | Ruta | Parámetros | Descripción | Códigos HTTP |
|---|---|---|---|---|
| `GET` | `/categorias` | `skip` (int), `limit` (int) | Lista paginada de categorías | `200` |
| `GET` | `/categorias/{id}` | `id` (int) | Consulta una categoría | `200`, `404` |
| `POST` | `/categorias` | Body JSON (`CategoriaCreate`) | Crea una categoría (nombre en minúsculas) | `201`, `409`, `422` |
| `PATCH` | `/categorias/{id}` | `id` (int), Body JSON (`CategoriaUpdate`) | Actualiza una categoría | `200`, `404`, `409`, `422` |
| `DELETE` | `/categorias/{id}` | `id` (int) | Elimina categoría y desvincula de libros | `204`, `404` |

### 3. Libros (`/libros`)
| Método | Ruta | Parámetros | Descripción | Códigos HTTP |
|---|---|---|---|---|
| `GET` | `/libros` | `skip`, `limit`, `buscar`, `autor`, `categoria_id`, `desde`, `hasta`, `orden` | Lista paginada con filtros combinables | `200` |
| `GET` | `/libros/{id}` | `id` (int) | Consulta libro con autor, categorías y `disponibles` | `200`, `404` |
| `POST` | `/libros` | Body JSON (`LibroCreate`) | Crea libro (404 si autor/cat no existen, 409 si ISBN existe) | `201`, `404`, `409`, `422` |
| `PATCH` | `/libros/{id}` | `id` (int), Body JSON (`LibroUpdate`) | Actualiza libro (422 si ejemplares < préstamos activos) | `200`, `404`, `409`, `422` |
| `DELETE` | `/libros/{id}` | `id` (int) | Elimina libro (409 si tiene préstamos sin devolver) | `204`, `404`, `409` |

### 4. Socios (`/socios`)
| Método | Ruta | Parámetros | Descripción | Códigos HTTP |
|---|---|---|---|---|
| `GET` | `/socios` | `skip` (int), `limit` (int), `activo` (bool, opcional) | Lista paginada con filtro por activo | `200` |
| `GET` | `/socios/{id}` | `id` (int) | Consulta un socio | `200`, `404` |
| `GET` | `/socios/{id}/prestamos` | `id` (int), `estado` (activo/vencido/devuelto) | Historial de préstamos del socio | `200`, `404` |
| `POST` | `/socios` | Body JSON (`SocioCreate`) | Crea un socio (email único) | `201`, `409`, `422` |
| `PATCH` | `/socios/{id}` | `id` (int), Body JSON (`SocioUpdate`) | Actualiza un socio | `200`, `404`, `409`, `422` |
| `DELETE` | `/socios/{id}` | `id` (int) | 409 si préstamos activos; inactiva si devueltos; borra si ninguno | `204`, `404`, `409` |

### 5. Préstamos (`/prestamos`)
| Método | Ruta | Parámetros | Descripción | Códigos HTTP |
|---|---|---|---|---|
| `GET` | `/prestamos` | `skip`, `limit`, `estado`, `socio_id`, `libro_id` | Lista préstamos con filtros | `200` |
| `GET` | `/prestamos/{id}` | `id` (int) | Consulta préstamo con libro y socio anidados | `200`, `404` |
| `POST` | `/prestamos` | Body JSON (`PrestamoCreate`) | Registra un préstamo aplicando reglas R1 a R8 | `201`, `404`, `409`, `422` |
| `POST` | `/prestamos/{id}/devolucion` | `id` (int), Body JSON (`DevolucionCreate`) | Registra devolución aplicando reglas R9 y R10 | `200`, `404`, `409`, `422` |

### 6. Reportes Administrativos (`/reportes`)
| Método | Ruta | Parámetros | Descripción | Técnica SQL |
|---|---|---|---|---|
| `GET` | `/reportes/libros-mas-prestados` | `limite` (int, default 5) | Top libros más prestados ordenados descendentemente | `join + group_by + count + order_by` |
| `GET` | `/reportes/categorias` | Ninguno | Total de libros por categoría (incluyendo 0) | `outerjoin + group_by` |
| `GET` | `/reportes/prestamos-vencidos` | Ninguno | Préstamos vencidos con cálculo de días de retraso | `join (3 tablas) + where` |
| `GET` | `/reportes/socios-con-multas` | Ninguno | Socios con multas acumuladas | `group_by + sum + having` |
| `GET` | `/reportes/autores` | Ninguno | Libros, ejemplares y préstamos por cada autor | `outerjoin + CTE / subconsultas` |
| `GET` | `/reportes/resumen` | Ninguno | Totales globales del sistema | `select(func.count()) y func.sum` |

---

## ⚖️ Reglas de Negocio Implementadas

El sistema valida las reglas de negocio estrictamente en el controlador:

- **R1:** El socio debe existir (HTTP 404).
- **R2:** El libro debe existir (HTTP 404).
- **R3:** El socio debe estar activo (`activo == True`) (HTTP 422: *"El socio no está activo"*).
- **R4:** El socio no debe tener préstamos vencidos (HTTP 422: *"El socio tiene préstamos vencidos"*).
- **R5:** El socio debe tener menos de 3 préstamos sin devolver (HTTP 422: *"Máximo de 3 préstamos"*).
- **R6:** El socio no puede tener ya ese mismo libro sin devolver (HTTP 409: *"El socio ya tiene este libro en préstamo"*).
- **R7:** El libro debe tener ejemplares disponibles (`ejemplares - prestamos_activos > 0`) (HTTP 422: *"No hay ejemplares disponibles"*).
- **R8:** La fecha límite se calcula como `fecha_prestamo + dias` (por defecto 14 días).
- **R9:** Al devolver: el préstamo debe existir (404), no haber sido devuelto antes (409) y la fecha de devolución no puede ser anterior a la del préstamo (422).
- **R10:** Si se devuelve tarde (`fecha_devolucion > fecha_limite`), se cobra una multa de `$0.50` por cada día de retraso.
