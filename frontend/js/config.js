/**
 * Configuración global de la aplicación de Biblioteca
 * Soporta conexión a FastAPI y servicio de imágenes Cloudinary
 */

const CONFIG = {
  // Configuración de la API FastAPI
  API: {
    BASE_URL: 'http://localhost:8000/api/v1',
    TIMEOUT_MS: 4000,
  },

  // Configuración de Cloudinary
  CLOUDINARY: {
    // Cloud name por defecto (puede modificarse en el panel de ajustes de la UI)
    CLOUD_NAME: 'demo',
    // Preset de subida no firmada (unsigned upload preset)
    UPLOAD_PRESET: 'ml_default',
    // Base URL de entrega de Cloudinary
    CDN_BASE: 'https://res.cloudinary.com',
    // Transformaciones predefinidas optimizadas para biblioteca
    TRANSFORMS: {
      coverStandard: 'c_fill,w_400,h_600,g_auto,q_auto,f_auto',
      coverCard: 'c_fill,w_300,h_450,g_auto,q_auto,f_auto',
      coverThumb: 'c_fill,w_120,h_180,g_auto,q_auto,f_auto',
      vintageSepia: 'e_sepia,c_fill,w_400,h_600,q_auto,f_auto',
      artisticVignette: 'e_vignette:40,c_fill,w_400,h_600,q_auto,f_auto',
      monochrome: 'e_grayscale,c_fill,w_400,h_600,q_auto,f_auto',
      improved: 'e_improve,c_fill,w_400,h_600,q_auto,f_auto',
      avatar: 'c_thumb,g_face,w_200,h_200,q_auto,f_auto,r_max',
    }
  },

  // Portadas iniciales en Cloudinary para el catálogo de la biblioteca
  DEFAULT_COVERS: {
    '9780307474728': {
      // Cien Años De Soledad
      url: 'https://res.cloudinary.com/demo/image/upload/c_fill,w_400,h_600,q_auto,f_auto/sample.jpg',
      publicId: 'cien_anos_soledad_cover',
      fallback: 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=400&h=600&q=80'
    },
    '9780307389732': {
      // El Amor En Los Tiempos Del Cólera
      url: 'https://res.cloudinary.com/demo/image/upload/c_fill,w_400,h_600,q_auto,f_auto/book_love_cholera',
      publicId: 'amor_tiempos_colera_cover',
      fallback: 'https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=400&h=600&q=80'
    },
    '9788401341991': {
      // La Casa De Los Espíritus
      url: 'https://res.cloudinary.com/demo/image/upload/c_fill,w_400,h_600,q_auto,f_auto/house_of_spirits',
      publicId: 'casa_espiritus_cover',
      fallback: 'https://images.unsplash.com/photo-1543002588-bfa74002ed7e?auto=format&fit=crop&w=400&h=600&q=80'
    },
    '9780451524935': {
      // 1984
      url: 'https://res.cloudinary.com/demo/image/upload/c_fill,w_400,h_600,q_auto,f_auto/1984_book',
      publicId: '1984_george_orwell_cover',
      fallback: 'https://images.unsplash.com/photo-1532012164546-f432f2e3777f?auto=format&fit=crop&w=400&h=600&q=80'
    },
    'default': 'https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=400&h=600&q=80'
  },

  // Parámetros de negocio de la biblioteca (alineados con backend)
  RULES: {
    MAX_PRESTAMOS_ACTIVOS: 3,
    TASA_MULTA_DIARIA: 0.50, // $0.50 por día de retraso
    DIAS_PRESTAMO_DEFAULT: 14,
    INTENTOS_LOGIN_MAX: 5
  }
};

window.CONFIG = CONFIG;
