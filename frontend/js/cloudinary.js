/**
 * Módulo de Integración con Cloudinary para Biblioteca Digital
 * Administra:
 *  - Subida directa (Unsigned REST API)
 *  - Cloudinary Upload Widget oficial
 *  - Generación dinámica de URLs transformadas (c_fill, e_sepia, f_auto, q_auto, etc.)
 *  - Almacenamiento y persistencia de portadas de libros y avatares
 */

class CloudinaryService {
  constructor() {
    this.storageKey = 'biblioteca_cloudinary_settings';
    this.coversStorageKey = 'biblioteca_book_covers';
    this.settings = this.loadSettings();
    this.customCovers = this.loadCustomCovers();
  }

  /**
   * Carga la configuración guardada o usa valores predeterminados
   */
  loadSettings() {
    try {
      const saved = localStorage.getItem(this.storageKey);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {
      console.warn('No se pudo leer configuración local de Cloudinary', e);
    }
    return {
      cloudName: window.CONFIG?.CLOUDINARY?.CLOUD_NAME || 'demo',
      uploadPreset: window.CONFIG?.CLOUDINARY?.UPLOAD_PRESET || 'ml_default',
      defaultFilter: 'coverStandard'
    };
  }

  /**
   * Guarda ajustes personalizados de Cloudinary (Cloud Name y Preset del usuario)
   */
  saveSettings(cloudName, uploadPreset, defaultFilter = 'coverStandard') {
    this.settings = {
      cloudName: (cloudName || 'demo').trim(),
      uploadPreset: (uploadPreset || 'ml_default').trim(),
      defaultFilter
    };
    try {
      localStorage.setItem(this.storageKey, JSON.stringify(this.settings));
    } catch (e) {
      console.error('Error al guardar configuración de Cloudinary:', e);
    }
    return this.settings;
  }

  /**
   * Carga el mapa de portadas personalizadas asociadas por ISBN o ID
   */
  loadCustomCovers() {
    try {
      const saved = localStorage.getItem(this.coversStorageKey);
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {
      console.warn('Error al cargar portadas locales', e);
    }
    return {};
  }

  /**
   * Guarda una portada para un libro específico
   */
  setBookCover(isbn, coverData) {
    this.customCovers[isbn] = coverData;
    try {
      localStorage.setItem(this.coversStorageKey, JSON.stringify(this.customCovers));
    } catch (e) {
      console.error('Error al guardar portada de libro:', e);
    }
  }

  /**
   * Obtiene la portada para un libro según su ISBN o datos
   */
  getBookCover(libro, filterKey = null) {
    if (!libro) return window.CONFIG.DEFAULT_COVERS.default;

    // 1. Revisar si hay portada personalizada subida por el usuario
    const custom = this.customCovers[libro.isbn] || this.customCovers[libro.id];
    if (custom && custom.url) {
      return this.applyTransform(custom.url, filterKey || this.settings.defaultFilter);
    }

    // 2. Revisar portadas predeterminadas de alta calidad
    const defaultCover = window.CONFIG.DEFAULT_COVERS[libro.isbn];
    if (defaultCover) {
      if (defaultCover.url.includes('res.cloudinary.com')) {
        return this.applyTransform(defaultCover.url, filterKey || this.settings.defaultFilter);
      }
      return defaultCover.url;
    }

    // 3. Fallback inteligente: portada generada o temática basada en categoría
    return this.generateSmartCover(libro, filterKey);
  }

  /**
   * Aplica transformaciones Cloudinary a una URL existente
   */
  applyTransform(url, transformKey = 'coverCard') {
    if (!url) return '';
    const transformStr = window.CONFIG?.CLOUDINARY?.TRANSFORMS[transformKey] || transformKey || 'c_fill,w_300,h_450,g_auto,q_auto,f_auto';

    // Si ya es una URL de Cloudinary
    if (url.includes('res.cloudinary.com')) {
      // Reemplazar o inyectar transformaciones después de '/upload/'
      if (url.includes('/image/upload/')) {
        const parts = url.split('/image/upload/');
        return `${parts[0]}/image/upload/${transformStr}/${parts[1].replace(/^c_[^/]+\//, '')}`;
      }
      return url;
    }

    // Si es una URL externa, podemos usar Cloudinary Fetch API para optimizarla al vuelo
    const cloudName = this.settings.cloudName || 'demo';
    return `https://res.cloudinary.com/${cloudName}/image/fetch/${transformStr}/${encodeURIComponent(url)}`;
  }

  /**
   * Genera una portada temática optimizada con Cloudinary para libros que no tengan imagen
   */
  generateSmartCover(libro, filterKey = 'coverCard') {
    const titles = {
      'Cien Años De Soledad': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=600&q=80',
      'El Amor En Los Tiempos Del Cólera': 'https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=600&q=80',
      'La Casa De Los Espíritus': 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?auto=format&fit=crop&w=600&q=80',
      '1984': 'https://images.unsplash.com/photo-1532012164546-f432f2e3777f?auto=format&fit=crop&w=600&q=80',
    };

    const fallbackUrl = titles[libro.titulo] || 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=600&q=80';
    return this.applyTransform(fallbackUrl, filterKey);
  }

  /**
   * Sube una imagen directamente a Cloudinary mediante REST API (unsigned preset)
   * @param {File|Blob|string} fileSource - Archivo local o URL para subir
   * @param {Function} onProgress - Callback para mostrar porcentaje de carga
   * @returns {Promise<Object>} Resultado con secure_url, public_id, etc.
   */
  async uploadImage(fileSource, onProgress = null) {
    const cloudName = this.settings.cloudName;
    const uploadPreset = this.settings.uploadPreset;

    if (!cloudName) {
      throw new Error('Debe configurar su Cloud Name de Cloudinary en los ajustes.');
    }

    const endpoint = `https://api.cloudinary.com/v1_1/${cloudName}/image/upload`;
    const formData = new FormData();

    formData.append('file', fileSource);
    formData.append('upload_preset', uploadPreset);
    formData.append('folder', 'biblioteca_libros');

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', endpoint, true);

      if (onProgress && xhr.upload) {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            onProgress(percent);
          }
        };
      }

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve({
              url: response.secure_url,
              publicId: response.public_id,
              format: response.format,
              width: response.width,
              height: response.height,
              bytes: response.bytes,
              created_at: response.created_at
            });
          } catch (err) {
            reject(new Error('Respuesta inválida de Cloudinary'));
          }
        } else {
          try {
            const errResp = JSON.parse(xhr.responseText);
            reject(new Error(errResp.error?.message || `Error ${xhr.status} al subir a Cloudinary`));
          } catch {
            reject(new Error(`Error ${xhr.status} al contactar Cloudinary`));
          }
        }
      };

      xhr.onerror = () => {
        reject(new Error('Error de red al conectar con los servidores de Cloudinary. Verifique su conexión y su Cloud Name.'));
      };

      xhr.send(formData);
    });
  }

  /**
   * Abre el Cloudinary Upload Widget oficial si está disponible en la página
   */
  openWidget(options = {}, onSuccess, onError) {
    if (!window.cloudinary) {
      if (onError) onError(new Error('El script del widget de Cloudinary no está cargado.'));
      return;
    }

    const widget = window.cloudinary.createUploadWidget(
      {
        cloudName: this.settings.cloudName,
        uploadPreset: this.settings.uploadPreset,
        folder: 'biblioteca_libros',
        sources: ['local', 'url', 'camera', 'unsplash'],
        multiple: false,
        theme: 'minimal',
        styles: {
          palette: {
            window: '#1e293b',
            windowBorder: '#475569',
            tabIcon: '#38bdf8',
            menuIcons: '#cbd5e1',
            textDark: '#0f172a',
            textLight: '#f8fafc',
            link: '#38bdf8',
            action: '#0284c7',
            inactiveTabIcon: '#94a3b8',
            error: '#f43f5e',
            inProgress: '#38bdf8',
            complete: '#10b981',
            sourceBg: '#0f172a'
          }
        },
        ...options
      },
      (error, result) => {
        if (!error && result && result.event === 'success') {
          if (onSuccess) onSuccess(result.info);
        } else if (error && onError) {
          onError(error);
        }
      }
    );

    widget.open();
    return widget;
  }
}

// Exportar instancia global
window.cloudinaryService = new CloudinaryService();
