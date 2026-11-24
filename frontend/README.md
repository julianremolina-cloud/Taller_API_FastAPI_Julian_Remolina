# 🏛️ Biblioteca Digital & Catálogo con Cloudinary CDN

Frontend interactivo y moderno para la gestión de biblioteca, catálogo bibliográfico, circulación de préstamos y carnet digital de afiliación, integrado con **Cloudinary** para optimización y transformación dinámica de portadas de libros y multimedia.

Desarrollado como complemento para el proyecto de API REST Segura con **FastAPI**.

---

## ☁️ Integración con Cloudinary

El sistema utiliza la infraestructura de **Cloudinary** para:

1. **Transformaciones en tiempo real (CDN):**
   - Redimensionamiento y recorte inteligente de portadas con `c_fill,g_auto,w_400,h_600`.
   - Optimización automática de formato y compresión con `f_auto,q_auto` (entrega en WebP/AVIF según el navegador).
   - Filtros artísticos y temáticos de biblioteca:
     - **Estándar HD:** `c_fill,w_400,h_600,g_auto,q_auto,f_auto`
     - **Sepia Siglo XIX (Vintage):** `e_sepia,c_fill,w_400,h_600`
     - **Viñeta Biblioteca:** `e_vignette:40,c_fill,w_400,h_600`
     - **Blanco y Negro Clásico:** `e_grayscale,c_fill,w_400,h_600`
     - **AI Auto-Enhance:** `e_improve,c_fill,w_400,h_600`
2. **Subida de Nuevas Portadas:**
   - **Subida directa sin firmar (Unsigned REST API):** Mediante `https://api.cloudinary.com/v1_1/<cloud_name>/image/upload` con barra de progreso interactiva y zona de arrastre (drag & drop).
   - **Cloudinary Upload Widget Oficial:** Soporte integrado con ventana emergente oficial de Cloudinary.
   - **Asignación en Vivo:** Permite vincular la portada subida a cualquier libro del catálogo (por ISBN o ID).
3. **Fotos de Socios / Carnet:**
   - Carga de fotografía de carnet de socio recortada circularmente con `c_thumb,g_face,r_max`.

---

## 📚 Características del Sistema de Biblioteca

- **Catálogo de Libros:**
  - Vista en **Cuadrícula** y vista en **Estantería 3D** con efecto de lomo encuadernado y perspectiva física.
  - Búsqueda en tiempo real por título, autor, tema o ISBN.
  - Filtro por categorías temáticas (Novela, Realismo Mágico, Distopía, Poesía, etc.).
  - Filtro por autor, disponibilidad ("Solo disponibles") y ordenamiento (A-Z, año publicación).
  - Ficha bibliográfica con vista previa de portada en alta definición y conmutador de filtros Cloudinary.
- **Préstamos y Circulación:**
  - Control de préstamos activos, fechas de préstamo y fecha límite.
  - Detección automática de préstamos vencidos.
  - **Liquidación de mora automática ($0.50/día de retraso)** según la Regla R10.
  - Registro de devoluciones y pago de multas con un solo clic.
  - Formulario de nuevo préstamo con validación de las 11 reglas de negocio (R1 a R11).
- **Carnet Digital de Afiliación (Mi Carnet):**
  - Tarjeta física virtual con sello de la biblioteca, código de barras interactivo, código QR y foto de socio.
  - Resumen de préstamos vigentes del socio y estado de solvencia de multas.
  - Conmutador para alternar entre diferentes socios registrados.
- **Estudio Cloudinary:**
  - Zona de arrastre para subir imágenes directamente a Cloudinary.
  - Playground interactivo para probar transformaciones y copiar las URLs resultantes del CDN.
  - Panel de ajustes para ingresar su propio **Cloud Name** y **Upload Preset**.
- **Panel Administrativo y de Gestión:**
  - Formulario para registrar nuevos libros asociando autor, categorías y portada de Cloudinary.
  - Formularios para agregar autores y nuevas categorías.
  - Botón para restaurar la semilla inicial de datos de prueba (Seed).
- **Arquitectura de Conexión Dual:**
  - **FastAPI Online:** Se comunica automáticamente con los endpoints de la API (`http://localhost:8000/api/v1`).
  - **Modo Interactivo Local:** Si la base de datos o el backend están apagados, el frontend activa un motor de simulación completo en el navegador que valida estrictamente las reglas R1 a R11, permitiendo probar toda la experiencia sin errores de red.

---

## 🚀 Cómo Ejecutar el Frontend

### Opción 1: Con Vite (Recomendada)

Abra una terminal en la carpeta `frontend` y ejecute:

```bash
cd frontend
npm install
npm run dev
```

La aplicación se abrirá en `http://localhost:5173`. Este origen ya está autorizado por defecto en la configuración CORS de la API de FastAPI.

### Opción 2: Con el Script Directo en Windows

Haga doble clic en el archivo:
`start_frontend.bat`

### Opción 3: Abrir directamente el archivo HTML

Puede abrir directamente `frontend/index.html` en Google Chrome, Microsoft Edge o cualquier navegador moderno con soporte para JavaScript ES6.

---

## 👥 Cuentas de Acceso Rápido para Pruebas

En la barra superior o en el modal de inicio de sesión dispone de accesos preconfigurados:

| Rol | Correo | Clave | Capacidades |
|---|---|---|---|
| **Administrador** | `admin@biblioteca.com` | `admin` | Acceso total a catálogo, préstamos, creación de libros, autores y restauración |
| **Bibliotecario** | `biblio@biblioteca.com` | `biblio` | Gestión de catálogo, registro de préstamos, devoluciones y multas |
| **Socio** | `ana@example.com` | `socio` | Consulta de carnet digital y préstamos propios |
| **Visitante** | *Público* | *N/A* | Exploración y consulta del catálogo y fichas bibliográficas |
