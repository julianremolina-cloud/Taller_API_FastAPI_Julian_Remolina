/**
 * Capa de Comunicación API y Gestión de Estado para Biblioteca Digital
 * Implementa soporte Dual:
 *  1. Conexión Real a FastAPI (http://localhost:8000/api/v1)
 *  2. Simulación Local Interactiva con Reglas de Negocio R1 - R11 (por si el backend está apagado)
 */

class ApiService {
  constructor() {
    this.baseUrl = window.CONFIG?.API?.BASE_URL || 'http://localhost:8000/api/v1';
    this.tokenKey = 'biblioteca_token';
    this.userKey = 'biblioteca_user';
    this.backendAvailable = false;
    this.listeners = [];

    // Inicializar almacén local de simulación
    this.initMockDatabase();
    // Probar conexión con FastAPI
    this.checkHealth();
  }

  onStatusChange(callback) {
    this.listeners.push(callback);
    callback(this.backendAvailable);
  }

  notifyStatus(status) {
    this.backendAvailable = status;
    this.listeners.forEach(cb => cb(status));
  }

  async checkHealth() {
    try {
      const controller = new AbortController();
      const id = setTimeout(() => controller.abort(), 2000);
      const res = await fetch(`${this.baseUrl}/health`, {
        signal: controller.signal,
        headers: { 'Accept': 'application/json' }
      });
      clearTimeout(id);
      if (res.ok) {
        this.notifyStatus(true);
        return true;
      }
    } catch (e) {
      // Backend apagado o inalcanzable
    }
    this.notifyStatus(false);
    return false;
  }

  // ==========================================
  // MANEJO DE TOKENS Y AUTENTICACIÓN
  // ==========================================

  getToken() {
    return localStorage.getItem(this.tokenKey);
  }

  setToken(token) {
    if (token) {
      localStorage.setItem(this.tokenKey, token);
    } else {
      localStorage.removeItem(this.tokenKey);
    }
  }

  getCurrentUser() {
    try {
      const data = localStorage.getItem(this.userKey);
      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  }

  setCurrentUser(user) {
    if (user) {
      localStorage.setItem(this.userKey, JSON.stringify(user));
    } else {
      localStorage.removeItem(this.userKey);
    }
  }

  getHeaders(isJson = true) {
    const headers = {};
    if (isJson) headers['Content-Type'] = 'application/json';
    const token = this.getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    return headers;
  }

  // ==========================================
  // OPERACIONES DE AUTENTICACIÓN
  // ==========================================

  async login(email, password) {
    if (this.backendAvailable) {
      try {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const res = await fetch(`${this.baseUrl}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: formData.toString()
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || 'Credenciales inválidas');
        }

        const data = await res.json();
        this.setToken(data.access_token);

        // Obtener datos del usuario
        const meRes = await fetch(`${this.baseUrl}/auth/me`, {
          headers: this.getHeaders()
        });
        if (meRes.ok) {
          const user = await meRes.json();
          this.setCurrentUser(user);
          return user;
        }
      } catch (err) {
        console.warn('Fallo petición a backend real, probando modo simulación:', err);
      }
    }

    // Modo Simulación
    const users = this.mockDb.usuarios;
    const user = users.find(u => u.email.toLowerCase() === email.toLowerCase());
    if (!user || user.password !== password) {
      throw new Error('Credenciales inválidas (401)');
    }
    if (!user.activo) {
      throw new Error('Usuario inactivo (403)');
    }

    this.setToken('mock-jwt-token-' + user.id);
    const userClean = { id: user.id, nombre: user.nombre, email: user.email, rol: user.rol, socio_id: user.socio_id };
    this.setCurrentUser(userClean);
    return userClean;
  }

  logout() {
    this.setToken(null);
    this.setCurrentUser(null);
  }

  // ==========================================
  // LIBROS
  // ==========================================

  async getLibros(params = {}) {
    if (this.backendAvailable) {
      try {
        const query = new URLSearchParams();
        if (params.buscar) query.append('buscar', params.buscar);
        if (params.autor) query.append('autor', params.autor);
        if (params.categoria_id) query.append('categoria_id', params.categoria_id);
        if (params.desde) query.append('desde', params.desde);
        if (params.hasta) query.append('hasta', params.hasta);
        if (params.orden) query.append('orden', params.orden);
        query.append('skip', params.skip || 0);
        query.append('limit', params.limit || 50);

        const res = await fetch(`${this.baseUrl}/libros?${query.toString()}`, {
          headers: this.getHeaders()
        });
        if (res.ok) {
          return await res.json();
        }
      } catch (e) {
        console.warn('Error conectando a backend para libros:', e);
      }
    }

    // Modo Simulación
    let items = [...this.mockDb.libros];

    // Filtros
    if (params.buscar) {
      const q = params.buscar.toLowerCase();
      items = items.filter(l => l.titulo.toLowerCase().includes(q) || l.isbn.includes(q));
    }
    if (params.autor) {
      const a = params.autor.toLowerCase();
      items = items.filter(l => l.autor.nombre.toLowerCase().includes(a));
    }
    if (params.categoria_id) {
      items = items.filter(l => l.categorias.some(c => c.id === parseInt(params.categoria_id)));
    }
    if (params.desde) {
      items = items.filter(l => l.anio_publicacion >= parseInt(params.desde));
    }
    if (params.hasta) {
      items = items.filter(l => l.anio_publicacion <= parseInt(params.hasta));
    }

    // Ordenamiento
    if (params.orden === 'titulo') {
      items.sort((a, b) => a.titulo.localeCompare(b.titulo));
    } else if (params.orden === 'anio') {
      items.sort((a, b) => a.anio_publicacion - b.anio_publicacion);
    } else if (params.orden === '-anio') {
      items.sort((a, b) => b.anio_publicacion - a.anio_publicacion);
    }

    // Recalcular disponibilidad
    this.recalcularDisponibilidad(items);

    const total = items.length;
    const skip = parseInt(params.skip || 0);
    const limit = parseInt(params.limit || 50);
    const paginados = items.slice(skip, skip + limit);

    return {
      items: paginados,
      total,
      skip,
      limit
    };
  }

  async getLibro(id) {
    if (this.backendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/libros/${id}`, {
          headers: this.getHeaders()
        });
        if (res.ok) return await res.json();
      } catch (e) {
        console.warn('Error al obtener libro:', e);
      }
    }

    const libro = this.mockDb.libros.find(l => l.id === parseInt(id));
    if (!libro) throw new Error('Libro no encontrado (404)');
    this.recalcularDisponibilidad([libro]);
    return libro;
  }

  async crearLibro(libroData) {
    if (this.backendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/libros`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify(libroData)
        });
        if (res.ok) return await res.json();
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Error al crear libro');
      } catch (e) {
        if (!e.message.includes('Failed to fetch')) throw e;
      }
    }

    // Simulación
    if (this.mockDb.libros.some(l => l.isbn === libroData.isbn)) {
      throw new Error('El ISBN ya se encuentra registrado (409)');
    }
    const autor = this.mockDb.autores.find(a => a.id === libroData.autor_id);
    if (!autor) throw new Error('Autor no encontrado (404)');

    const cats = this.mockDb.categorias.filter(c => libroData.categoria_ids.includes(c.id));
    const nuevo = {
      id: this.mockDb.libros.length + 1,
      titulo: libroData.titulo,
      isbn: libroData.isbn,
      anio_publicacion: parseInt(libroData.anio_publicacion),
      ejemplares: parseInt(libroData.ejemplares),
      disponibles: parseInt(libroData.ejemplares),
      autor_id: autor.id,
      autor,
      categorias: cats
    };
    this.mockDb.libros.push(nuevo);
    this.saveMockDb();
    return nuevo;
  }

  async actualizarLibro(id, libroData) {
    if (this.backendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/libros/${id}`, {
          method: 'PATCH',
          headers: this.getHeaders(),
          body: JSON.stringify(libroData)
        });
        if (res.ok) return await res.json();
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Error al actualizar libro');
      } catch (e) {
        if (!e.message.includes('Failed to fetch')) throw e;
      }
    }

    const libro = this.mockDb.libros.find(l => l.id === parseInt(id));
    if (!libro) throw new Error('Libro no encontrado');
    Object.assign(libro, libroData);
    this.saveMockDb();
    return libro;
  }

  async eliminarLibro(id) {
    if (this.backendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/libros/${id}`, {
          method: 'DELETE',
          headers: this.getHeaders()
        });
        if (res.ok) return true;
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Error al eliminar');
      } catch (e) {
        if (!e.message.includes('Failed to fetch')) throw e;
      }
    }

    this.mockDb.libros = this.mockDb.libros.filter(l => l.id !== parseInt(id));
    this.saveMockDb();
    return true;
  }

  // ==========================================
  // AUTORES Y CATEGORÍAS
  // ==========================================

  async getAutores() {
    if (this.backendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/autores`, { headers: this.getHeaders() });
        if (res.ok) {
          const data = await res.json();
          return Array.isArray(data) ? data : data.items || [];
        }
      } catch (e) {}
    }
    return this.mockDb.autores;
  }

  async crearAutor(autorData) {
    if (this.backendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/autores`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify(autorData)
        });
        if (res.ok) return await res.json();
      } catch (e) {}
    }

    const nuevo = {
      id: this.mockDb.autores.length + 1,
      nombre: autorData.nombre,
      nacionalidad: autorData.nacionalidad,
      anio_nacimiento: parseInt(autorData.anio_nacimiento)
    };
    this.mockDb.autores.push(nuevo);
    this.saveMockDb();
    return nuevo;
  }

  async getCategorias() {
    if (this.backendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/categorias`, { headers: this.getHeaders() });
        if (res.ok) {
          const data = await res.json();
          return Array.isArray(data) ? data : data.items || [];
        }
      } catch (e) {}
    }
    return this.mockDb.categorias;
  }

  async crearCategoria(catData) {
    if (this.backendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/categorias`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify(catData)
        });
        if (res.ok) return await res.json();
      } catch (e) {}
    }

    const nuevo = {
      id: this.mockDb.categorias.length + 1,
      nombre: catData.nombre.toLowerCase().trim(),
      descripcion: catData.descripcion
    };
    this.mockDb.categorias.push(nuevo);
    this.saveMockDb();
    return nuevo;
  }

  // ==========================================
  // SOCIOS
  // ==========================================

  async getSocios() {
    if (this.backendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/socios`, { headers: this.getHeaders() });
        if (res.ok) {
          const data = await res.json();
          return Array.isArray(data) ? data : data.items || [];
        }
      } catch (e) {}
    }
    return this.mockDb.socios;
  }

  async crearSocio(socioData) {
    if (this.backendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/socios`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify(socioData)
        });
        if (res.ok) return await res.json();
      } catch (e) {}
    }

    const nuevo = {
      id: this.mockDb.socios.length + 1,
      nombre: socioData.nombre,
      email: socioData.email,
      telefono: socioData.telefono || null,
      activo: true,
      fecha_creacion: new Date().toISOString()
    };
    this.mockDb.socios.push(nuevo);
    this.saveMockDb();
    return nuevo;
  }

  // ==========================================
  // PRÉSTAMOS Y CIRCULACIÓN (REGLAS R1 A R11)
  // ==========================================

  async getPrestamos(socioId = null) {
    if (this.backendAvailable) {
      try {
        const query = socioId ? `?socio_id=${socioId}` : '';
        const res = await fetch(`${this.baseUrl}/prestamos${query}`, { headers: this.getHeaders() });
        if (res.ok) {
          const data = await res.json();
          return Array.isArray(data) ? data : data.items || [];
        }
      } catch (e) {}
    }

    let items = [...this.mockDb.prestamos];
    if (socioId) {
      items = items.filter(p => p.socio_id === parseInt(socioId));
    }
    return items;
  }

  /**
   * Registra un nuevo préstamo validando estrictamente las reglas R1 a R11
   */
  async crearPrestamo(prestamoData) {
    if (this.backendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/prestamos`, {
          method: 'POST',
          headers: this.getHeaders(),
          body: JSON.stringify(prestamoData)
        });
        if (res.ok) return await res.json();
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Error al registrar préstamo');
      } catch (e) {
        if (!e.message.includes('Failed to fetch')) throw e;
      }
    }

    // Validación exhaustiva de Reglas en Simulación:
    const socio = this.mockDb.socios.find(s => s.id === parseInt(prestamoData.socio_id));
    if (!socio) throw new Error('R1: El socio especificado no existe (404)');

    const libro = this.mockDb.libros.find(l => l.id === parseInt(prestamoData.libro_id));
    if (!libro) throw new Error('R2: El libro especificado no existe (404)');

    if (!socio.activo) {
      throw new Error('R3: El socio no se encuentra activo para solicitar préstamos (422)');
    }

    const prestamosSocio = this.mockDb.prestamos.filter(p => p.socio_id === socio.id && !p.fecha_devolucion);

    // R4: Préstamos vencidos
    const hoy = new Date();
    const tieneVencidos = prestamosSocio.some(p => new Date(p.fecha_limite) < hoy);
    if (tieneVencidos) {
      throw new Error('R4: El socio tiene préstamos vencidos sin devolver (422)');
    }

    // R5: Máximo 3 préstamos activos
    if (prestamosSocio.length >= 3) {
      throw new Error('R5: El socio ya alcanzó el límite máximo de 3 préstamos activos (422)');
    }

    // R6: No prestar el mismo libro dos veces simultáneamente
    const yaTieneEseLibro = prestamosSocio.some(p => p.libro_id === libro.id);
    if (yaTieneEseLibro) {
      throw new Error('R6: El socio ya tiene una copia de este libro en préstamo activo (409)');
    }

    // R7: Ejemplares disponibles
    const prestadosLibro = this.mockDb.prestamos.filter(p => p.libro_id === libro.id && !p.fecha_devolucion).length;
    const disponibles = Math.max(0, libro.ejemplares - prestadosLibro);
    if (disponibles <= 0) {
      throw new Error('R7: No hay ejemplares disponibles de este libro en este momento (422)');
    }

    // R11: Multas pendientes
    const multasPendientes = this.mockDb.prestamos.some(p => p.socio_id === socio.id && p.multa > 0 && !p.multa_pagada);
    if (multasPendientes) {
      throw new Error('R11: El socio tiene multas pendientes de pago (422)');
    }

    // R8: Fecha límite
    const dias = parseInt(prestamoData.dias || 14);
    const fechaPrestamo = new Date();
    const fechaLimite = new Date();
    fechaLimite.setDate(fechaPrestamo.getDate() + dias);

    const nuevoPrestamo = {
      id: this.mockDb.prestamos.length + 1,
      socio_id: socio.id,
      socio_nombre: socio.nombre,
      libro_id: libro.id,
      libro_titulo: libro.titulo,
      fecha_prestamo: fechaPrestamo.toISOString().split('T')[0],
      fecha_limite: fechaLimite.toISOString().split('T')[0],
      fecha_devolucion: null,
      dias_retraso: 0,
      multa: 0.0,
      multa_pagada: false
    };

    this.mockDb.prestamos.push(nuevoPrestamo);
    this.saveMockDb();
    return nuevoPrestamo;
  }

  /**
   * Registra la devolución de un libro y calcula mora según R9 y R10
   */
  async devolverPrestamo(prestamoId) {
    if (this.backendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/prestamos/${prestamoId}/devolucion`, {
          method: 'POST',
          headers: this.getHeaders()
        });
        if (res.ok) return await res.json();
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Error al devolver');
      } catch (e) {
        if (!e.message.includes('Failed to fetch')) throw e;
      }
    }

    const prestamo = this.mockDb.prestamos.find(p => p.id === parseInt(prestamoId));
    if (!prestamo) throw new Error('Préstamo no encontrado (404)');
    if (prestamo.fecha_devolucion) throw new Error('El libro ya fue devuelto previamente (422)');

    const hoy = new Date();
    prestamo.fecha_devolucion = hoy.toISOString().split('T')[0];

    // R10: Cálculo de multa si hubo retraso ($0.50 por día)
    const fechaLimite = new Date(prestamo.fecha_limite);
    const diffTime = hoy.getTime() - fechaLimite.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays > 0) {
      prestamo.dias_retraso = diffDays;
      prestamo.multa = Number((diffDays * 0.50).toFixed(2));
      prestamo.multa_pagada = false;
    } else {
      prestamo.dias_retraso = 0;
      prestamo.multa = 0.0;
      prestamo.multa_pagada = true;
    }

    this.saveMockDb();
    return prestamo;
  }

  /**
   * Registra el pago de la multa de un préstamo
   */
  async pagarMulta(prestamoId) {
    if (this.backendAvailable) {
      try {
        const res = await fetch(`${this.baseUrl}/prestamos/${prestamoId}/pago-multa`, {
          method: 'POST',
          headers: this.getHeaders()
        });
        if (res.ok) return await res.json();
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || 'Error al pagar multa');
      } catch (e) {
        if (!e.message.includes('Failed to fetch')) throw e;
      }
    }

    const prestamo = this.mockDb.prestamos.find(p => p.id === parseInt(prestamoId));
    if (!prestamo) throw new Error('Préstamo no encontrado (404)');
    if (prestamo.multa <= 0) throw new Error('Este préstamo no tiene multa registrada (422)');
    if (prestamo.multa_pagada) throw new Error('La multa ya se encuentra pagada (422)');

    prestamo.multa_pagada = true;
    this.saveMockDb();
    return prestamo;
  }

  // ==========================================
  // REPORTES
  // ==========================================

  async getReportes() {
    if (this.backendAvailable) {
      try {
        const [r1, r2] = await Promise.all([
          fetch(`${this.baseUrl}/reportes/libros-mas-prestados`, { headers: this.getHeaders() }),
          fetch(`${this.baseUrl}/reportes/prestamos-activos-por-socio`, { headers: this.getHeaders() })
        ]);
        if (r1.ok && r2.ok) {
          return {
            masPrestados: await r1.json(),
            porSocio: await r2.json()
          };
        }
      } catch (e) {}
    }

    // Simulación de reportes basada en los préstamos
    const masPrestadosMap = {};
    this.mockDb.prestamos.forEach(p => {
      masPrestadosMap[p.libro_titulo] = (masPrestadosMap[p.libro_titulo] || 0) + 1;
    });

    const masPrestados = Object.entries(masPrestadosMap).map(([titulo, total]) => ({
      titulo,
      total_prestamos: total
    })).sort((a, b) => b.total_prestamos - a.total_prestamos);

    return {
      masPrestados,
      totalLibros: this.mockDb.libros.length,
      totalSocios: this.mockDb.socios.length,
      prestamosActivos: this.mockDb.prestamos.filter(p => !p.fecha_devolucion).length,
      multasPendientes: this.mockDb.prestamos.filter(p => p.multa > 0 && !p.multa_pagada).length
    };
  }

  // ==========================================
  // AUXILIARES Y BASE DE DATOS LOCAL
  // ==========================================

  recalcularDisponibilidad(libros) {
    libros.forEach(l => {
      const prestados = this.mockDb.prestamos.filter(p => p.libro_id === l.id && !p.fecha_devolucion).length;
      l.disponibles = Math.max(0, l.ejemplares - prestados);
    });
  }

  initMockDatabase() {
    try {
      const saved = localStorage.getItem('biblioteca_mock_db');
      if (saved) {
        this.mockDb = JSON.parse(saved);
        return;
      }
    } catch (e) {
      console.warn('Error cargando mock db:', e);
    }

    // Datos iniciales idénticos a seed.py del proyecto
    this.mockDb = {
      autores: [
        { id: 1, nombre: 'Gabriel García Márquez', nacionalidad: 'Colombiana', anio_nacimiento: 1927 },
        { id: 2, nombre: 'Isabel Allende', nacionalidad: 'Chilena', anio_nacimiento: 1942 },
        { id: 3, nombre: 'George Orwell', nacionalidad: 'Británica', anio_nacimiento: 1903 }
      ],
      categorias: [
        { id: 1, nombre: 'novela', descripcion: 'Obras narrativas de ficción' },
        { id: 2, nombre: 'realismo mágico', descripcion: 'Elementos mágicos en un entorno realista' },
        { id: 3, nombre: 'distopía', descripcion: 'Sociedades ficticias indeseables' },
        { id: 4, nombre: 'poesía', descripcion: 'Composiciones literarias poéticas' }
      ],
      socios: [
        { id: 1, nombre: 'Ana Torres', email: 'ana@example.com', activo: true, telefono: '+57 300 123 4567' },
        { id: 2, nombre: 'Luis Pérez', email: 'luis@example.com', activo: true, telefono: '+57 311 234 5678' },
        { id: 3, nombre: 'Marta Ruiz', email: 'marta@example.com', activo: true, telefono: '+57 320 345 6789' }
      ],
      usuarios: [
        { id: 1, nombre: 'Administrador General', email: 'admin@biblioteca.com', password: 'admin', rol: 'admin', socio_id: null, activo: true },
        { id: 2, nombre: 'Bibliotecario Turno Mañana', email: 'biblio@biblioteca.com', password: 'biblio', rol: 'bibliotecario', socio_id: null, activo: true },
        { id: 3, nombre: 'Ana Torres', email: 'ana@example.com', password: 'socio', rol: 'socio', socio_id: 1, activo: true }
      ],
      libros: [
        {
          id: 1,
          titulo: 'Cien Años De Soledad',
          isbn: '9780307474728',
          anio_publicacion: 1967,
          ejemplares: 2,
          disponibles: 2,
          autor_id: 1,
          autor: { id: 1, nombre: 'Gabriel García Márquez', nacionalidad: 'Colombiana' },
          categorias: [
            { id: 1, nombre: 'novela' },
            { id: 2, nombre: 'realismo mágico' }
          ]
        },
        {
          id: 2,
          titulo: 'El Amor En Los Tiempos Del Cólera',
          isbn: '9780307389732',
          anio_publicacion: 1985,
          ejemplares: 1,
          disponibles: 1,
          autor_id: 1,
          autor: { id: 1, nombre: 'Gabriel García Márquez', nacionalidad: 'Colombiana' },
          categorias: [
            { id: 1, nombre: 'novela' }
          ]
        },
        {
          id: 3,
          titulo: 'La Casa De Los Espíritus',
          isbn: '9788401341991',
          anio_publicacion: 1982,
          ejemplares: 2,
          disponibles: 2,
          autor_id: 2,
          autor: { id: 2, nombre: 'Isabel Allende', nacionalidad: 'Chilena' },
          categorias: [
            { id: 1, nombre: 'novela' },
            { id: 2, nombre: 'realismo mágico' }
          ]
        },
        {
          id: 4,
          titulo: '1984',
          isbn: '9780451524935',
          anio_publicacion: 1949,
          ejemplares: 3,
          disponibles: 3,
          autor_id: 3,
          autor: { id: 3, nombre: 'George Orwell', nacionalidad: 'Británica' },
          categorias: [
            { id: 1, nombre: 'novela' },
            { id: 3, nombre: 'distopía' }
          ]
        }
      ],
      prestamos: [
        {
          id: 1,
          socio_id: 1,
          socio_nombre: 'Ana Torres',
          libro_id: 1,
          libro_titulo: 'Cien Años De Soledad',
          fecha_prestamo: '2026-11-10',
          fecha_limite: '2026-11-24',
          fecha_devolucion: null,
          dias_retraso: 0,
          multa: 0.0,
          multa_pagada: false
        },
        {
          id: 2,
          socio_id: 2,
          socio_nombre: 'Luis Pérez',
          libro_id: 4,
          libro_titulo: '1984',
          fecha_prestamo: '2026-10-20',
          fecha_limite: '2026-11-03',
          fecha_devolucion: null,
          dias_retraso: 21,
          multa: 10.50,
          multa_pagada: false
        }
      ]
    };
    this.saveMockDb();
  }

  saveMockDb() {
    try {
      localStorage.setItem('biblioteca_mock_db', JSON.stringify(this.mockDb));
    } catch (e) {
      console.error('Error guardando mock db:', e);
    }
  }

  resetMockDb() {
    localStorage.removeItem('biblioteca_mock_db');
    this.initMockDatabase();
  }
}

window.apiService = new ApiService();
