/**
 * Controlador Principal de la Aplicación de Biblioteca Digital
 * Orquesta Catálogo, Préstamos, Carnet de Socio, Estudio Cloudinary y Reportes
 */

document.addEventListener('DOMContentLoaded', () => {
  // Estado local de la aplicación
  const state = {
    currentTab: 'catalogo',
    currentRole: 'admin',
    currentSocioId: 1,
    activeCategory: '',
    searchQuery: '',
    sortOrder: '',
    filterAuthor: '',
    onlyAvailable: false,
    cloudinaryFilter: 'coverCard',
    viewMode: 'cards', // 'cards' o 'shelf'
    currentSelectedBook: null,
    lastUploadedCoverUrl: null,
    books: [],
    authors: [],
    categories: [],
    socios: [],
    loans: []
  };

  // Referencias a elementos del DOM
  const dom = {
    // Pestañas
    navBtns: document.querySelectorAll('.nav-btn'),
    viewPanels: document.querySelectorAll('.view-panel'),
    tabLinks: document.querySelectorAll('[data-tab-link]'),

    // Estado del backend
    backendBadge: document.getElementById('backend-status-badge'),
    btnRecheckHealth: document.getElementById('btn-recheck-health'),
    selectActiveRole: document.getElementById('select-active-role'),

    // Búsqueda y Filtros
    searchInput: document.getElementById('search-input'),
    btnDoSearch: document.getElementById('btn-do-search'),
    btnClearSearch: document.getElementById('btn-clear-search'),
    categoryPills: document.getElementById('category-pills'),
    selectSort: document.getElementById('select-sort'),
    selectFilterAutor: document.getElementById('select-filter-autor'),
    checkSoloDisponibles: document.getElementById('check-solo-disponibles'),
    selectCloudinaryEffect: document.getElementById('select-cloudinary-effect'),
    btnViewCards: document.getElementById('btn-view-cards'),
    btnViewShelf: document.getElementById('btn-view-shelf'),

    // Contenedores
    booksGrid: document.getElementById('books-grid'),
    catalogCountBadge: document.getElementById('catalog-count-badge'),
    tablePrestamosBody: document.getElementById('prestamos-tbody'),

    // Estadísticas Hero
    statTotalLibros: document.getElementById('stat-total-libros'),
    statDisponibles: document.getElementById('stat-disponibles'),
    statPrestamosActivos: document.getElementById('stat-prestamos-activos'),
    statSocios: document.getElementById('stat-socios'),
    badgePrestamosCount: document.getElementById('badge-prestamos-count'),

    // Contadores de filtros de préstamos
    countPrestamosTodos: document.getElementById('count-prestamos-todos'),
    countPrestamosActivos: document.getElementById('count-prestamos-activos'),
    countPrestamosVencidos: document.getElementById('count-prestamos-vencidos'),
    countPrestamosDevueltos: document.getElementById('count-prestamos-devueltos'),

    // Carnet de Socio
    selectSocioCarnet: document.getElementById('select-socio-carnet'),
    carnetNombre: document.getElementById('carnet-nombre'),
    carnetEmail: document.getElementById('carnet-email'),
    carnetId: document.getElementById('carnet-id'),
    carnetEstado: document.getElementById('carnet-estado'),
    carnetPrestamosCount: document.getElementById('carnet-prestamos-count'),
    carnetMultasStatus: document.getElementById('carnet-multas-status'),
    carnetBarcode: document.getElementById('carnet-barcode-code'),
    carnetAvatar: document.getElementById('carnet-avatar'),
    btnCambiarFotoSocio: document.getElementById('btn-cambiar-foto-socio'),
    socioActiveLoansList: document.getElementById('socio-active-loans-list'),

    // Cloudinary Studio
    cloudinaryDropZone: document.getElementById('cloudinary-drop-zone'),
    inputCloudinaryFile: document.getElementById('input-cloudinary-file'),
    btnBrowseFile: document.getElementById('btn-browse-file'),
    btnOpenWidgetDirect: document.getElementById('btn-open-widget-direct'),
    uploadProgressContainer: document.getElementById('upload-progress-container'),
    uploadProgressBar: document.getElementById('upload-progress-bar'),
    uploadPercentage: document.getElementById('upload-percentage'),
    uploadStatusText: document.getElementById('upload-status-text'),
    selectAssignBook: document.getElementById('select-assign-book'),
    btnSaveCoverAssignment: document.getElementById('btn-save-cover-assignment'),
    playgroundPreviewImg: document.getElementById('playground-preview-img'),
    generatedCloudinaryUrl: document.getElementById('generated-cloudinary-url'),
    btnCopyUrl: document.getElementById('btn-copy-url'),

    // Modales
    modalLibroDetalle: document.getElementById('modal-libro-detalle'),
    modalNuevoPrestamo: document.getElementById('modal-nuevo-prestamo'),
    modalCloudinaryConfig: document.getElementById('modal-cloudinary-config'),
    modalAuth: document.getElementById('modal-auth'),

    // Detalle Libro Modal
    detailCoverImg: document.getElementById('detail-cover-img'),
    detailTitulo: document.getElementById('detail-titulo'),
    detailAutor: document.getElementById('detail-autor'),
    detailIsbn: document.getElementById('detail-isbn'),
    detailAnio: document.getElementById('detail-anio'),
    detailEjemplares: document.getElementById('detail-ejemplares'),
    detailDisponibles: document.getElementById('detail-disponibles'),
    detailCategories: document.getElementById('detail-categories'),
    detailSynopsisText: document.getElementById('detail-synopsis-text'),
    btnDetailPrestar: document.getElementById('btn-detail-prestar'),
    btnChangeBookCover: document.getElementById('btn-change-book-cover'),

    // Formularios
    formNuevoLibro: document.getElementById('form-nuevo-libro'),
    formNuevoAutor: document.getElementById('form-nuevo-autor'),
    formNuevaCategoria: document.getElementById('form-nueva-categoria'),
    formCrearPrestamo: document.getElementById('form-crear-prestamo'),
    formCloudinaryConfig: document.getElementById('form-cloudinary-config'),
    formAuthLogin: document.getElementById('form-auth-login'),

    // Botones adicionales
    btnOpenNuevoPrestamo: document.getElementById('btn-open-nuevo-prestamo'),
    btnOpenCloudinarySettings: document.getElementById('btn-open-cloudinary-settings'),
    btnLoginLogout: document.getElementById('btn-login-logout'),
    btnResetDb: document.getElementById('btn-reset-db'),
    btnRefreshReportes: document.getElementById('btn-refresh-reportes'),
    btnUploadCoverForm: document.getElementById('btn-upload-cover-form'),
    toastContainer: document.getElementById('toast-container')
  };

  // ==========================================
  // INICIALIZACIÓN
  // ==========================================
  async function init() {
    setupEventListeners();
    setupStatusWatcher();
    setupRole();
    await loadInitialData();
  }

  // ==========================================
  // VIGILANCIA DE ESTADO DE API (FASTAPI VS SIMULACIÓN)
  // ==========================================
  function setupStatusWatcher() {
    window.apiService.onStatusChange((isOnline) => {
      if (isOnline) {
        dom.backendBadge.className = 'status-indicator-pill online';
        dom.backendBadge.querySelector('.indicator-label').textContent = 'FastAPI v2.0 Conectado';
        dom.backendBadge.title = 'Conexión activa con http://localhost:8000/api/v1';
      } else {
        dom.backendBadge.className = 'status-indicator-pill simulation';
        dom.backendBadge.querySelector('.indicator-label').textContent = 'Modo Interactivo Local';
        dom.backendBadge.title = 'Backend en reposo. Modo de simulación completo con reglas R1-R11 activo.';
      }
    });

    dom.btnRecheckHealth.addEventListener('click', async (e) => {
      e.stopPropagation();
      showToast('Comprobando conexión con FastAPI...', 'info');
      const ok = await window.apiService.checkHealth();
      if (ok) {
        showToast('¡Conectado exitosamente con FastAPI!', 'success');
        await loadInitialData();
      } else {
        showToast('FastAPI no responde en puerto 8000. Continuando en Modo Interactivo.', 'warning');
      }
    });
  }

  // ==========================================
  // CARGA DE DATOS PRINCIPALES
  // ==========================================
  async function loadInitialData() {
    try {
      const [autores, categorias, socios, prestamos] = await Promise.all([
        window.apiService.getAutores(),
        window.apiService.getCategorias(),
        window.apiService.getSocios(),
        window.apiService.getPrestamos()
      ]);

      state.authors = autores || [];
      state.categories = categorias || [];
      state.socios = socios || [];
      state.loans = prestamos || [];

      // Llenar selectores
      populateDropdowns();
      // Cargar libros
      await loadBooks();
      // Renderizar préstamos
      renderPrestamosTable();
      // Renderizar carnet
      renderCarnet();
      // Actualizar estadísticas
      updateStats();
      // Cargar reportes
      loadReportes();
    } catch (err) {
      console.error('Error inicializando datos:', err);
      showToast('Error al cargar datos bibliográficos', 'error');
    }
  }

  // ==========================================
  // GESTIÓN DE ROLES
  // ==========================================
  function setupRole() {
    const savedRole = localStorage.getItem('biblioteca_active_role') || 'admin';
    state.currentRole = savedRole;
    dom.selectActiveRole.value = savedRole;
    updateRoleUI(savedRole);

    dom.selectActiveRole.addEventListener('change', (e) => {
      state.currentRole = e.target.value;
      localStorage.setItem('biblioteca_active_role', state.currentRole);
      updateRoleUI(state.currentRole);
      showToast(`Rol cambiado a: ${state.currentRole.toUpperCase()}`, 'info');
    });
  }

  function updateRoleUI(role) {
    const userRoleLabel = document.getElementById('user-role-label');
    const userName = document.getElementById('user-name');
    const userAvatar = document.getElementById('user-avatar');

    if (role === 'admin') {
      userRoleLabel.textContent = 'ADMIN';
      userRoleLabel.className = 'user-role badge-admin';
      userName.textContent = 'Administrador General';
      userAvatar.src = 'https://res.cloudinary.com/demo/image/upload/c_thumb,g_face,w_80,h_80,r_max/rachel.jpg';
    } else if (role === 'bibliotecario') {
      userRoleLabel.textContent = 'BIBLIOTECARIO';
      userRoleLabel.className = 'user-role badge-biblio';
      userName.textContent = 'Bibliotecario Principal';
      userAvatar.src = 'https://res.cloudinary.com/demo/image/upload/c_thumb,g_face,w_80,h_80,r_max/smiling_man.jpg';
    } else if (role === 'socio') {
      userRoleLabel.textContent = 'SOCIO';
      userRoleLabel.className = 'user-role badge-socio';
      userName.textContent = 'Ana Torres';
      userAvatar.src = 'https://res.cloudinary.com/demo/image/upload/c_thumb,g_face,w_80,h_80,r_max/woman.jpg';
    } else {
      userRoleLabel.textContent = 'VISITANTE';
      userRoleLabel.className = 'user-role';
      userName.textContent = 'Lector Invitado';
      userAvatar.src = 'https://res.cloudinary.com/demo/image/upload/c_thumb,g_face,w_80,h_80,r_max/sample.jpg';
    }
  }

  // ==========================================
  // LLENADO DE SELECTORES EN DOM
  // ==========================================
  function populateDropdowns() {
    // Autores en filtro y formulario
    dom.selectFilterAutor.innerHTML = '<option value="">Todos los autores</option>';
    const libroAutorSelect = document.getElementById('libro-autor');
    libroAutorSelect.innerHTML = '<option value="">Seleccione un autor</option>';

    state.authors.forEach(a => {
      dom.selectFilterAutor.innerHTML += `<option value="${a.nombre}">${a.nombre}</option>`;
      libroAutorSelect.innerHTML += `<option value="${a.id}">${a.nombre} (${a.nacionalidad})</option>`;
    });

    // Categorías en checkboxes
    const catCheckboxes = document.getElementById('categorias-checkboxes');
    catCheckboxes.innerHTML = '';
    state.categories.forEach(c => {
      catCheckboxes.innerHTML += `
        <label class="cat-check-label">
          <input type="checkbox" name="categoria_ids" value="${c.id}">
          <span>${c.nombre}</span>
        </label>
      `;
    });

    // Socios en selectores de préstamo y carnet
    dom.selectSocioCarnet.innerHTML = '';
    const prestamoSocioSelect = document.getElementById('prestamo-socio');
    prestamoSocioSelect.innerHTML = '<option value="">Seleccione un socio</option>';

    state.socios.forEach(s => {
      dom.selectSocioCarnet.innerHTML += `<option value="${s.id}">${s.nombre} (${s.email})</option>`;
      prestamoSocioSelect.innerHTML += `<option value="${s.id}">${s.nombre} - ${s.activo ? 'Activo' : 'Inactivo'}</option>`;
    });

    // Asignar en estudio Cloudinary
    dom.selectAssignBook.innerHTML = '<option value="">-- Seleccionar libro del catálogo --</option>';
  }

  // ==========================================
  // CATÁLOGO DE LIBROS Y RENDERIZADO
  // ==========================================
  async function loadBooks() {
    dom.booksGrid.innerHTML = `
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Cargando catálogo bibliográfico...</p>
      </div>
    `;

    try {
      const params = {
        buscar: state.searchQuery,
        autor: state.filterAuthor,
        categoria_id: state.activeCategory,
        orden: state.sortOrder
      };

      const result = await window.apiService.getLibros(params);
      let books = result.items || [];

      if (state.onlyAvailable) {
        books = books.filter(b => b.disponibles > 0);
      }

      state.books = books;
      renderBooksGrid(books);

      // Actualizar contador
      dom.catalogCountBadge.textContent = `${books.length} ${books.length === 1 ? 'libro' : 'libros'}`;

      // Actualizar selector en Cloudinary
      dom.selectAssignBook.innerHTML = '<option value="">-- Seleccionar libro del catálogo --</option>';
      books.forEach(b => {
        dom.selectAssignBook.innerHTML += `<option value="${b.isbn}">${b.titulo} (${b.isbn})</option>`;
      });

      // Actualizar selector en modal de préstamo
      const prestamoLibroSelect = document.getElementById('prestamo-libro');
      prestamoLibroSelect.innerHTML = '<option value="">Seleccione un libro</option>';
      books.forEach(b => {
        const dispoTxt = b.disponibles > 0 ? `(${b.disponibles} disponibles)` : '(AGOTADO)';
        prestamoLibroSelect.innerHTML += `<option value="${b.id}" ${b.disponibles === 0 ? 'disabled' : ''}>${b.titulo} ${dispoTxt}</option>`;
      });

    } catch (err) {
      console.error('Error cargando libros:', err);
      dom.booksGrid.innerHTML = `
        <div class="alert-info-box" style="grid-column: 1 / -1; justify-content: center;">
          <i class="bi bi-exclamation-triangle"></i>
          <span>No fue posible cargar el catálogo de libros. Compruebe la conexión.</span>
        </div>
      `;
    }
  }

  function renderBooksGrid(books) {
    if (!books || books.length === 0) {
      dom.booksGrid.innerHTML = `
        <div class="no-results-box" style="grid-column: 1 / -1; text-align: center; padding: 3rem;">
          <i class="bi bi-journal-x" style="font-size: 3rem; color: var(--text-muted);"></i>
          <h4 style="margin-top: 1rem;">No se encontraron libros</h4>
          <p class="text-muted-sm">Intente cambiar los filtros o el término de búsqueda.</p>
        </div>
      `;
      return;
    }

    dom.booksGrid.className = state.viewMode === 'shelf' ? 'books-shelf-mode' : 'books-grid';

    dom.booksGrid.innerHTML = books.map(libro => {
      // Obtener portada dinámica de Cloudinary con el filtro activo
      const coverUrl = window.cloudinaryService.getBookCover(libro, state.cloudinaryFilter);
      const isAvailable = libro.disponibles > 0;
      const categoriesHtml = (libro.categorias || []).map(c =>
        `<span class="category-tag">${c.nombre}</span>`
      ).join('');

      return `
        <article class="book-card" data-book-id="${libro.id}">
          <div class="book-cover-container">
            <span class="book-badge-ribbon ${isAvailable ? 'ribbon-available' : 'ribbon-out'}">
              ${isAvailable ? `${libro.disponibles} disp.` : 'Agotado'}
            </span>
            <img src="${coverUrl}" alt="Portada de ${libro.titulo}" class="book-cover-img" loading="lazy">
            <div class="book-spine-shine"></div>
            <span class="book-cloudinary-tag" title="Optimizada por Cloudinary CDN">
              <i class="bi bi-cloud-check-fill"></i> Cloudinary
            </span>
          </div>

          <div class="book-card-body">
            <div class="book-categories">${categoriesHtml}</div>
            <h4 class="book-title" title="${libro.titulo}">${libro.titulo}</h4>
            <p class="book-author">${libro.autor?.nombre || 'Autor desconocido'}</p>

            <div class="book-meta-strip">
              <span>Año: <strong>${libro.anio_publicacion}</strong></span>
              <span class="book-isbn">ISBN: ${libro.isbn}</span>
            </div>

            <div class="book-card-actions">
              <button class="btn-primary btn-sm btn-action-detail" data-book-id="${libro.id}">
                <i class="bi bi-eye"></i> Ver Ficha
              </button>
              <button class="btn-secondary btn-sm btn-action-cover" data-book-isbn="${libro.isbn}" title="Subir o cambiar portada con Cloudinary">
                <i class="bi bi-cloud-arrow-up text-cloudinary"></i>
              </button>
            </div>
          </div>
        </article>
      `;
    }).join('');

    // Asignar eventos a botones de las tarjetas
    dom.booksGrid.querySelectorAll('.btn-action-detail').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = parseInt(btn.dataset.bookId);
        openBookDetailModal(id);
      });
    });

    dom.booksGrid.querySelectorAll('.btn-action-cover').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isbn = btn.dataset.bookIsbn;
        switchTab('cloudinary');
        dom.selectAssignBook.value = isbn;
        dom.btnSaveCoverAssignment.disabled = false;
        showToast('Seleccione un archivo para la portada en Cloudinary', 'info');
      });
    });
  }

  // ==========================================
  // MODAL DE DETALLE DEL LIBRO (FICHA)
  // ==========================================
  async function openBookDetailModal(bookId) {
    try {
      const libro = await window.apiService.getLibro(bookId);
      state.currentSelectedBook = libro;

      dom.detailTitulo.textContent = libro.titulo;
      dom.detailAutor.textContent = libro.autor?.nombre || 'Desconocido';
      dom.detailIsbn.textContent = libro.isbn;
      dom.detailAnio.textContent = libro.anio_publicacion;
      dom.detailEjemplares.textContent = `${libro.ejemplares} ejemplares en colección`;

      if (libro.disponibles > 0) {
        dom.detailDisponibles.textContent = `${libro.disponibles} disponibles para préstamo`;
        dom.detailDisponibles.className = 'meta-value badge-success';
        dom.btnDetailPrestar.disabled = false;
      } else {
        dom.detailDisponibles.textContent = 'Actualmente agotado (Todos en préstamo)';
        dom.detailDisponibles.className = 'meta-value badge-danger';
        dom.btnDetailPrestar.disabled = true;
      }

      dom.detailCategories.innerHTML = (libro.categorias || []).map(c =>
        `<span class="category-tag">${c.nombre}</span>`
      ).join('');

      // Sinopsis temática
      const synopses = {
        'Cien Años De Soledad': 'La saga de la familia Buendía a lo largo de siete generaciones en Macondo. Una joya indiscutible de la literatura mundial y máximo exponente del realismo mágico.',
        'El Amor En Los Tiempos Del Cólera': 'Florentino Ariza y Fermina Daza mantienen un amor juvenil que florece medio siglo después, enmarcado en el Caribe colombiano fluvial de finales del siglo XIX.',
        'La Casa De Los Espíritus': 'La historia familiar de los Trueba a través de cuatro generaciones, combinando pasiones, política y clarividencia en un convulso país latinoamericano.',
        '1984': 'Crónica distópica sobre el Gran Hermano, la vigilancia masiva, el doblepensar y la manipulación de la verdad en una sociedad totalitaria gobernada por Oceanía.'
      };
      dom.detailSynopsisText.textContent = synopses[libro.titulo] || `Edición clásica de ${libro.titulo}. Obra de ${libro.autor?.nombre} incorporada al acervo de la Biblioteca Digital.`;

      // Cargar portada
      updateDetailModalCover('coverStandard');

      // Botón solicitar préstamo
      dom.btnDetailPrestar.onclick = () => {
        closeModal(dom.modalLibroDetalle);
        openNuevoPrestamoModal(libro.id);
      };

      // Botón cambiar portada
      dom.btnChangeBookCover.onclick = () => {
        closeModal(dom.modalLibroDetalle);
        switchTab('cloudinary');
        dom.selectAssignBook.value = libro.isbn;
        dom.btnSaveCoverAssignment.disabled = false;
      };

      openModal(dom.modalLibroDetalle);
    } catch (err) {
      showToast('Error al consultar libro: ' + err.message, 'error');
    }
  }

  function updateDetailModalCover(filterKey) {
    if (!state.currentSelectedBook) return;
    const coverUrl = window.cloudinaryService.getBookCover(state.currentSelectedBook, filterKey);
    dom.detailCoverImg.src = coverUrl;
  }

  // ==========================================
  // GESTIÓN DE PRÉSTAMOS & CIRCULACIÓN
  // ==========================================
  function renderPrestamosTable(filter = 'todos') {
    let loans = [...state.loans];
    const hoy = new Date();

    if (filter === 'activos') {
      loans = loans.filter(l => !l.fecha_devolucion);
    } else if (filter === 'vencidos') {
      loans = loans.filter(l => !l.fecha_devolucion && new Date(l.fecha_limite) < hoy);
    } else if (filter === 'devueltos') {
      loans = loans.filter(l => l.fecha_devolucion);
    }

    // Actualizar contadores
    const countTodos = state.loans.length;
    const countActivos = state.loans.filter(l => !l.fecha_devolucion).length;
    const countVencidos = state.loans.filter(l => !l.fecha_devolucion && new Date(l.fecha_limite) < hoy).length;
    const countDevueltos = state.loans.filter(l => l.fecha_devolucion).length;

    dom.countPrestamosTodos.textContent = countTodos;
    dom.countPrestamosActivos.textContent = countActivos;
    dom.countPrestamosVencidos.textContent = countVencidos;
    dom.countPrestamosDevueltos.textContent = countDevueltos;
    dom.badgePrestamosCount.textContent = countActivos;

    if (loans.length === 0) {
      dom.tablePrestamosBody.innerHTML = `
        <tr>
          <td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-muted);">
            No hay registros de préstamos en esta categoría.
          </td>
        </tr>
      `;
      return;
    }

    dom.tablePrestamosBody.innerHTML = loans.map(p => {
      const fechaLimite = new Date(p.fecha_limite);
      const isReturned = !!p.fecha_devolucion;
      const isOverdue = !isReturned && fechaLimite < hoy;

      let statusBadge = '';
      if (isReturned) {
        statusBadge = '<span class="prestamo-status-badge status-returned"><i class="bi bi-check-all"></i> Devuelto</span>';
      } else if (isOverdue) {
        statusBadge = '<span class="prestamo-status-badge status-overdue"><i class="bi bi-exclamation-octagon"></i> Vencido</span>';
      } else {
        statusBadge = '<span class="prestamo-status-badge status-active"><i class="bi bi-clock"></i> En Plazo</span>';
      }

      // Cálculo de multa visual
      let moraHtml = '-';
      if (p.multa > 0) {
        moraHtml = `
          <strong class="${p.multa_pagada ? 'text-success' : 'text-danger'}">
            $${Number(p.multa).toFixed(2)}
          </strong>
          <span style="font-size: 0.7rem; display: block;">${p.multa_pagada ? '(Pagada)' : `(${p.dias_retraso} d mora)`}</span>
        `;
      } else if (isOverdue) {
        // Cálculo preventivo
        const diffDays = Math.ceil((hoy - fechaLimite) / (1000 * 60 * 60 * 24));
        moraHtml = `<span class="text-danger">Por liquidar (~$${(diffDays * 0.5).toFixed(2)})</span>`;
      }

      // Acciones
      let actionsHtml = '';
      if (!isReturned) {
        actionsHtml += `
          <button class="btn-primary btn-sm btn-devolver-prestamo" data-id="${p.id}" title="Registrar entrega">
            <i class="bi bi-box-arrow-in-left"></i> Devolver
          </button>
        `;
      }
      if (p.multa > 0 && !p.multa_pagada) {
        actionsHtml += `
          <button class="btn-success btn-sm btn-pagar-multa" data-id="${p.id}" title="Pagar multa de mora">
            <i class="bi bi-cash-stack"></i> Pagar Multa
          </button>
        `;
      }

      return `
        <tr>
          <td>#${p.id}</td>
          <td><strong>${p.libro_titulo}</strong></td>
          <td>${p.socio_nombre}</td>
          <td>${p.fecha_prestamo}</td>
          <td>${p.fecha_limite}</td>
          <td>${statusBadge}</td>
          <td>${moraHtml}</td>
          <td>
            <div style="display: flex; gap: 0.35rem;">
              ${actionsHtml || '<span class="text-muted-sm">Completado</span>'}
            </div>
          </td>
        </tr>
      `;
    }).join('');

    // Eventos de botones
    dom.tablePrestamosBody.querySelectorAll('.btn-devolver-prestamo').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        try {
          const resultado = await window.apiService.devolverPrestamo(id);
          showToast(`¡Libro devuelto! ${resultado.multa > 0 ? `Multa generada: $${resultado.multa}` : 'Sin retraso.'}`, 'success');
          await reloadLoans();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    });

    dom.tablePrestamosBody.querySelectorAll('.btn-pagar-multa').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        try {
          await window.apiService.pagarMulta(id);
          showToast('Multa pagada exitosamente', 'success');
          await reloadLoans();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    });
  }

  async function reloadLoans() {
    state.loans = await window.apiService.getPrestamos();
    renderPrestamosTable();
    await loadBooks(); // Recalcular disponibilidad de ejemplares
    renderCarnet();
    updateStats();
    loadReportes();
  }

  function openNuevoPrestamoModal(preselectedBookId = null) {
    if (preselectedBookId) {
      document.getElementById('prestamo-libro').value = preselectedBookId;
    }
    openModal(dom.modalNuevoPrestamo);
  }

  // ==========================================
  // CARNET DIGITAL DE SOCIO
  // ==========================================
  function renderCarnet() {
    const socioId = parseInt(dom.selectSocioCarnet.value || state.currentSocioId);
    const socio = state.socios.find(s => s.id === socioId) || state.socios[0];
    if (!socio) return;

    dom.carnetNombre.textContent = socio.nombre;
    dom.carnetEmail.textContent = socio.email;
    dom.carnetId.textContent = `SOC-000${socio.id}`;
    dom.carnetEstado.textContent = socio.activo ? 'ACTIVO' : 'INACTIVO';
    dom.carnetEstado.className = socio.activo ? 'badge-success' : 'badge-danger';
    dom.carnetBarcode.textContent = `BIB-SOC-00${socio.id}-9780307`;

    // Préstamos del socio
    const prestamosSocio = state.loans.filter(l => l.socio_id === socio.id);
    const activos = prestamosSocio.filter(l => !l.fecha_devolucion);
    dom.carnetPrestamosCount.textContent = `${activos.length} / 3 max`;

    // Multas
    const multasPendientes = prestamosSocio.filter(l => l.multa > 0 && !l.multa_pagada);
    const totalMultas = multasPendientes.reduce((acc, curr) => acc + Number(curr.multa), 0);

    if (totalMultas > 0) {
      dom.carnetMultasStatus.textContent = `$${totalMultas.toFixed(2)} Pendiente`;
      dom.carnetMultasStatus.className = 'badge-danger';
    } else {
      dom.carnetMultasStatus.textContent = '$0.00 (Al día)';
      dom.carnetMultasStatus.className = 'badge-success';
    }

    // Listado en lateral
    if (activos.length === 0) {
      dom.socioActiveLoansList.innerHTML = `
        <p style="color: var(--text-muted); font-size: 0.85rem;">
          Este socio no tiene préstamos activos actualmente. Puede solicitar hasta 3 libros.
        </p>
      `;
    } else {
      dom.socioActiveLoansList.innerHTML = activos.map(p => `
        <div style="background: #f8fafc; border: 1px solid var(--border-light); padding: 0.75rem; border-radius: var(--radius-sm); margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <strong>${p.libro_titulo}</strong>
            <div style="font-size: 0.75rem; color: var(--text-muted);">
              Límite: ${p.fecha_limite}
            </div>
          </div>
          <button class="btn-primary btn-sm btn-devolver-prestamo" data-id="${p.id}">
            Devolver
          </button>
        </div>
      `).join('');

      dom.socioActiveLoansList.querySelectorAll('.btn-devolver-prestamo').forEach(b => {
        b.addEventListener('click', async () => {
          try {
            await window.apiService.devolverPrestamo(b.dataset.id);
            showToast('Libro devuelto con éxito', 'success');
            await reloadLoans();
          } catch (e) {
            showToast(e.message, 'error');
          }
        });
      });
    }
  }

  // ==========================================
  // ESTUDIO Y GESTOR CLOUDINARY
  // ==========================================
  function setupCloudinaryStudio() {
    // Drop zone para subida directa
    const dropZone = dom.cloudinaryDropZone;
    const fileInput = dom.inputCloudinaryFile;

    dom.btnBrowseFile.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        handleCloudinaryUpload(fileInput.files[0]);
      }
    });

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        handleCloudinaryUpload(e.dataTransfer.files[0]);
      }
    });

    // Abrir widget oficial de Cloudinary
    dom.btnOpenWidgetDirect.addEventListener('click', (e) => {
      e.stopPropagation();
      window.cloudinaryService.openWidget(
        {},
        (info) => {
          showToast('¡Imagen subida a Cloudinary con éxito!', 'success');
          onCloudinaryUploadSuccess(info.secure_url);
        },
        (err) => {
          showToast('Error en Cloudinary: ' + err.message, 'error');
        }
      );
    });

    // Guardar asignación al libro
    dom.btnSaveCoverAssignment.addEventListener('click', () => {
      const isbn = dom.selectAssignBook.value;
      if (!isbn) {
        showToast('Seleccione un libro para asociarle esta portada', 'warning');
        return;
      }
      if (!state.lastUploadedCoverUrl) {
        showToast('No hay ninguna imagen cargada en Cloudinary', 'warning');
        return;
      }

      window.cloudinaryService.setBookCover(isbn, {
        url: state.lastUploadedCoverUrl,
        updated_at: new Date().toISOString()
      });

      showToast(`¡Portada de Cloudinary asignada con éxito al ISBN ${isbn}!`, 'success');
      loadBooks();
    });

    // Botones de transformación en el playground
    document.querySelectorAll('.btn-transform-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.btn-transform-chip').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const transformKey = btn.dataset.transform;
        updatePlaygroundPreview(transformKey);
      });
    });

    // Copiar URL
    dom.btnCopyUrl.addEventListener('click', () => {
      navigator.clipboard.writeText(dom.generatedCloudinaryUrl.textContent);
      showToast('URL copiada al portapapeles', 'info');
    });

    // Cambiar foto del socio en carnet
    dom.btnCambiarFotoSocio.addEventListener('click', () => {
      window.cloudinaryService.openWidget(
        { cropping: true, croppingAspectRatio: 1 },
        (info) => {
          dom.carnetAvatar.src = info.secure_url;
          showToast('Foto de socio actualizada en Cloudinary', 'success');
        },
        (err) => {
          showToast('Error: ' + err.message, 'error');
        }
      );
    });
  }

  async function handleCloudinaryUpload(file) {
    if (!file.type.startsWith('image/')) {
      showToast('Por favor seleccione un archivo de imagen válido', 'warning');
      return;
    }

    dom.uploadProgressContainer.style.display = 'block';
    dom.uploadProgressBar.style.width = '0%';
    dom.uploadPercentage.textContent = '0%';
    dom.uploadStatusText.textContent = 'Enviando imagen a Cloudinary CDN...';

    try {
      const result = await window.cloudinaryService.uploadImage(file, (percent) => {
        dom.uploadProgressBar.style.width = `${percent}%`;
        dom.uploadPercentage.textContent = `${percent}%`;
      });

      dom.uploadStatusText.textContent = '¡Subida completada!';
      showToast('¡Imagen subida a Cloudinary exitosamente!', 'success');
      onCloudinaryUploadSuccess(result.url);
    } catch (err) {
      console.warn('Error subiendo directo a Cloudinary:', err);
      // Fallback amigable: cargar localmente y transformar con Cloudinary Fetch
      const reader = new FileReader();
      reader.onload = (e) => {
        const localDataUrl = e.target.result;
        onCloudinaryUploadSuccess(localDataUrl);
        showToast('Imagen cargada en el estudio para optimización', 'info');
      };
      reader.readAsDataURL(file);
    }
  }

  function onCloudinaryUploadSuccess(url) {
    state.lastUploadedCoverUrl = url;
    dom.playgroundPreviewImg.src = url;
    dom.generatedCloudinaryUrl.textContent = url;
    dom.btnSaveCoverAssignment.disabled = false;
    updatePlaygroundPreview('coverStandard');
  }

  function updatePlaygroundPreview(transformKey) {
    const rawUrl = state.lastUploadedCoverUrl || 'https://res.cloudinary.com/demo/image/upload/sample.jpg';
    const transformedUrl = window.cloudinaryService.applyTransform(rawUrl, transformKey);
    dom.playgroundPreviewImg.src = transformedUrl;
    dom.generatedCloudinaryUrl.textContent = transformedUrl;
  }

  // ==========================================
  // CONFIGURACIÓN DE CLOUDINARY MODAL
  // ==========================================
  function setupCloudinarySettingsModal() {
    dom.btnOpenCloudinarySettings.addEventListener('click', () => {
      const cfg = window.cloudinaryService.settings;
      document.getElementById('cfg-cloud-name').value = cfg.cloudName;
      document.getElementById('cfg-upload-preset').value = cfg.uploadPreset;
      document.getElementById('cfg-default-filter').value = cfg.defaultFilter;
      openModal(dom.modalCloudinaryConfig);
    });

    dom.formCloudinaryConfig.addEventListener('submit', (e) => {
      e.preventDefault();
      const name = document.getElementById('cfg-cloud-name').value;
      const preset = document.getElementById('cfg-upload-preset').value;
      const filter = document.getElementById('cfg-default-filter').value;

      window.cloudinaryService.saveSettings(name, preset, filter);
      closeModal(dom.modalCloudinaryConfig);
      showToast('Configuración de Cloudinary guardada', 'success');
      loadBooks();
    });

    document.getElementById('btn-test-cloudinary').addEventListener('click', async () => {
      showToast('Probando conectividad con Cloudinary...', 'info');
      try {
        const testImg = new Image();
        testImg.src = `https://res.cloudinary.com/${document.getElementById('cfg-cloud-name').value}/image/upload/sample.jpg`;
        testImg.onload = () => showToast('¡Conexión con Cloudinary exitosa!', 'success');
        testImg.onerror = () => showToast('El cloud name no existe o es privado, pero puede usarse en modo demo.', 'warning');
      } catch {
        showToast('Error de red al comprobar Cloudinary', 'error');
      }
    });
  }

  // ==========================================
  // ESTADÍSTICAS Y REPORTES
  // ==========================================
  function updateStats() {
    const totalLibros = state.books.length;
    const totalDisponibles = state.books.reduce((acc, b) => acc + (b.disponibles || 0), 0);
    const activos = state.loans.filter(l => !l.fecha_devolucion).length;
    const totalSocios = state.socios.length;

    dom.statTotalLibros.textContent = totalLibros;
    dom.statDisponibles.textContent = totalDisponibles;
    dom.statPrestamosActivos.textContent = activos;
    dom.statSocios.textContent = totalSocios;
  }

  async function loadReportes() {
    const container = document.getElementById('reporte-mas-prestados');
    if (!container) return;

    try {
      const rep = await window.apiService.getReportes();
      const items = rep.masPrestados || [];

      if (items.length === 0) {
        container.innerHTML = '<p class="text-muted-sm">Aún no hay suficiente historial de préstamos.</p>';
        return;
      }

      container.innerHTML = items.map((item, index) => `
        <div class="reporte-item">
          <span class="reporte-rank">#${index + 1}</span>
          <span class="reporte-title">${item.titulo}</span>
          <span class="reporte-count">${item.total_prestamos} préstamos</span>
        </div>
      `).join('');
    } catch (e) {
      console.warn('Error al cargar reportes:', e);
    }
  }

  // ==========================================
  // CONFIGURACIÓN DE EVENT LISTENERS
  // ==========================================
  function setupEventListeners() {
    // Cambio de pestañas
    dom.navBtns.forEach(btn => {
      btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    dom.tabLinks.forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        switchTab(link.dataset.tabLink);
      });
    });

    // Búsqueda en catálogo
    dom.btnDoSearch.addEventListener('click', () => {
      state.searchQuery = dom.searchInput.value.trim();
      dom.btnClearSearch.style.display = state.searchQuery ? 'inline-block' : 'none';
      loadBooks();
    });

    dom.searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        state.searchQuery = dom.searchInput.value.trim();
        dom.btnClearSearch.style.display = state.searchQuery ? 'inline-block' : 'none';
        loadBooks();
      }
    });

    dom.btnClearSearch.addEventListener('click', () => {
      dom.searchInput.value = '';
      state.searchQuery = '';
      dom.btnClearSearch.style.display = 'none';
      loadBooks();
    });

    // Filtros de categoría en Hero
    dom.categoryPills.querySelectorAll('.cat-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        dom.categoryPills.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        state.activeCategory = pill.dataset.cat;
        loadBooks();
      });
    });

    // Orden y autor
    dom.selectSort.addEventListener('change', (e) => {
      state.sortOrder = e.target.value;
      loadBooks();
    });

    dom.selectFilterAutor.addEventListener('change', (e) => {
      state.filterAuthor = e.target.value;
      loadBooks();
    });

    dom.checkSoloDisponibles.addEventListener('change', (e) => {
      state.onlyAvailable = e.target.checked;
      loadBooks();
    });

    // Filtro global de efecto Cloudinary
    dom.selectCloudinaryEffect.addEventListener('change', (e) => {
      state.cloudinaryFilter = e.target.value;
      renderBooksGrid(state.books);
      showToast(`Efecto Cloudinary aplicado: ${e.target.options[e.target.selectedIndex].text}`, 'info');
    });

    // Alternar vistas (Tarjetas vs Estantería)
    dom.btnViewCards.addEventListener('click', () => {
      state.viewMode = 'cards';
      dom.btnViewCards.classList.add('active');
      dom.btnViewShelf.classList.remove('active');
      renderBooksGrid(state.books);
    });

    dom.btnViewShelf.addEventListener('click', () => {
      state.viewMode = 'shelf';
      dom.btnViewShelf.classList.add('active');
      dom.btnViewCards.classList.remove('active');
      renderBooksGrid(state.books);
    });

    // Filtros de préstamos
    document.querySelectorAll('.prestamo-filter-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.prestamo-filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderPrestamosTable(btn.dataset.filter);
      });
    });

    // Cambio de socio en carnet
    dom.selectSocioCarnet.addEventListener('change', () => {
      renderCarnet();
    });

    // Modal nuevo préstamo
    dom.btnOpenNuevoPrestamo.addEventListener('click', () => openNuevoPrestamoModal());

    dom.formCrearPrestamo.addEventListener('submit', async (e) => {
      e.preventDefault();
      const libroId = document.getElementById('prestamo-libro').value;
      const socioId = document.getElementById('prestamo-socio').value;
      const dias = document.getElementById('prestamo-dias').value;

      try {
        await window.apiService.crearPrestamo({
          libro_id: parseInt(libroId),
          socio_id: parseInt(socioId),
          dias: parseInt(dias)
        });
        showToast('¡Préstamo registrado exitosamente!', 'success');
        closeModal(dom.modalNuevoPrestamo);
        await reloadLoans();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    // Formulario Nuevo Libro
    dom.formNuevoLibro.addEventListener('submit', async (e) => {
      e.preventDefault();
      const catCheckboxes = document.querySelectorAll('input[name="categoria_ids"]:checked');
      const catIds = Array.from(catCheckboxes).map(c => parseInt(c.value));

      if (catIds.length === 0 || catIds.length > 5) {
        showToast('Debe asignar entre 1 y 5 categorías', 'warning');
        return;
      }

      const libroData = {
        titulo: document.getElementById('libro-titulo').value.trim(),
        isbn: document.getElementById('libro-isbn').value.trim(),
        anio_publicacion: parseInt(document.getElementById('libro-anio').value),
        ejemplares: parseInt(document.getElementById('libro-ejemplares').value),
        autor_id: parseInt(document.getElementById('libro-autor').value),
        categoria_ids: catIds
      };

      const portadaUrl = document.getElementById('libro-portada-url').value.trim();

      try {
        const nuevo = await window.apiService.crearLibro(libroData);
        if (portadaUrl) {
          window.cloudinaryService.setBookCover(nuevo.isbn, { url: portadaUrl });
        }
        showToast('¡Libro agregado al catálogo con éxito!', 'success');
        dom.formNuevoLibro.reset();
        await loadBooks();
        switchTab('catalogo');
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    // Formulario Nuevo Autor
    dom.formNuevoAutor.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await window.apiService.crearAutor({
          nombre: document.getElementById('autor-nombre').value.trim(),
          nacionalidad: document.getElementById('autor-nacionalidad').value.trim(),
          anio_nacimiento: parseInt(document.getElementById('autor-nacimiento').value)
        });
        showToast('Autor registrado con éxito', 'success');
        dom.formNuevoAutor.reset();
        state.authors = await window.apiService.getAutores();
        populateDropdowns();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    // Formulario Nueva Categoría
    dom.formNuevaCategoria.addEventListener('submit', async (e) => {
      e.preventDefault();
      try {
        await window.apiService.crearCategoria({
          nombre: document.getElementById('cat-nombre').value.trim(),
          descripcion: document.getElementById('cat-desc').value.trim()
        });
        showToast('Categoría registrada con éxito', 'success');
        dom.formNuevaCategoria.reset();
        state.categories = await window.apiService.getCategorias();
        populateDropdowns();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    // Restaurar semilla
    dom.btnResetDb.addEventListener('click', () => {
      if (confirm('¿Desea restaurar la base de datos a los datos iniciales de prueba?')) {
        window.apiService.resetMockDb();
        showToast('Datos de prueba restaurados exitosamente', 'success');
        loadInitialData();
      }
    });

    // Refrescar reportes
    dom.btnRefreshReportes.addEventListener('click', () => {
      loadReportes();
      showToast('Reportes actualizados', 'info');
    });

    // Botón login/logout
    dom.btnLoginLogout.addEventListener('click', () => {
      openModal(dom.modalAuth);
    });

    // Cuentas rápidas de login
    document.querySelectorAll('.btn-quick-cred').forEach(btn => {
      btn.addEventListener('click', () => {
        document.getElementById('auth-email').value = btn.dataset.email;
        document.getElementById('auth-password').value = btn.dataset.pass;
      });
    });

    dom.formAuthLogin.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('auth-email').value;
      const pass = document.getElementById('auth-password').value;

      try {
        const user = await window.apiService.login(email, pass);
        showToast(`Bienvenido, ${user.nombre}`, 'success');
        state.currentRole = user.rol;
        dom.selectActiveRole.value = user.rol;
        updateRoleUI(user.rol);
        closeModal(dom.modalAuth);
      } catch (err) {
        showToast(err.message, 'error');
      }
    });

    // Cerrar modales
    document.querySelectorAll('[data-close-modal]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.modal-backdrop').forEach(m => closeModal(m));
      });
    });

    // Filtros rápidos de portada en modal de detalle
    document.querySelectorAll('[data-cover-style]').forEach(pill => {
      pill.addEventListener('click', () => {
        document.querySelectorAll('[data-cover-style]').forEach(p => p.classList.remove('active'));
        pill.classList.add('active');
        updateDetailModalCover(pill.dataset.coverStyle);
      });
    });

    // Inicializar submódulos
    setupCloudinaryStudio();
    setupCloudinarySettingsModal();
  }

  // ==========================================
  // FUNCIONES AUXILIARES DE NAVEGACIÓN Y MODALES
  // ==========================================
  function switchTab(tabId) {
    state.currentTab = tabId;

    dom.navBtns.forEach(btn => {
      btn.classList.toggle('active', btn.dataset.tab === tabId);
    });

    dom.viewPanels.forEach(panel => {
      panel.classList.toggle('active', panel.id === `view-${tabId}`);
    });

    if (tabId === 'prestamos') renderPrestamosTable();
    if (tabId === 'carnet') renderCarnet();
    if (tabId === 'reportes') loadReportes();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function openModal(modalEl) {
    if (modalEl) modalEl.classList.add('show');
  }

  function closeModal(modalEl) {
    if (modalEl) modalEl.classList.remove('show');
  }

  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    let icon = 'bi-info-circle-fill';
    if (type === 'success') icon = 'bi-check-circle-fill text-success';
    if (type === 'error') icon = 'bi-exclamation-triangle-fill text-danger';
    if (type === 'warning') icon = 'bi-exclamation-circle-fill text-warning';

    toast.innerHTML = `
      <i class="bi ${icon}"></i>
      <span>${message}</span>
    `;

    dom.toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 3800);
  }

  // Arranque inicial
  init();
});
