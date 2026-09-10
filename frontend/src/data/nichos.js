// ============================================================
// NICHOS — Datos maestros de Nuvora
// ============================================================
// Añadir un nuevo nicho es tan simple como añadir un objeto aquí.
// No se necesita modificar ningún otro archivo.
// ============================================================

export const NICHOS = {
  restaurantes: {
    id: 'restaurantes',
    name: 'Restaurantes',
    icon: '🍽️',
    description: 'Restaurantes, bares y establecimientos de hostelería',
    greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
    quickQuestions: ['Horario', 'Menú', 'Reservas', 'Ubicación', 'Alergenos'],
    categories: [
      { name: 'Horarios', description: 'Horarios de apertura y cierre' },
      { name: 'Menú', description: 'Platos, precios y especialidades' },
      { name: 'Reservas', description: 'Política de reservas y aforo' },
      { name: 'Ubicación', description: 'Dirección, aparcamiento, acceso' },
      { name: 'Información general', description: 'Sobre el negocio y sus servicios' },
    ],
    suggestedMemories: [
      { fact: 'Abrimos de lunes a domingo de 9:00 a 18:00', keyword: 'horario' },
      { fact: 'Aceptamos reservas por teléfono y online', keyword: 'reservas' },
      { fact: 'Tenemos opciones vegetarianas y veganas', keyword: 'menú,vegetariano' },
      { fact: 'Estamos en la calle Principal 123', keyword: 'ubicación,dirección' },
      { fact: 'Aceptamos tarjeta de crédito, Bizum y efectivo', keyword: 'pagos' },
    ],
    sampleQuestions: [
      '¿A qué hora abrís?',
      '¿Tenéis menú infantil?',
      '¿Aceptáis mascotas?',
    ]
  },

  peluquerias: {
    id: 'peluquerias',
    name: 'Peluquerías',
    icon: '💇',
    description: 'Peluquerías, barberías y centros de estética',
    greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
    quickQuestions: ['Horario', 'Servicios', 'Precios', 'Reservas', 'Productos'],
    categories: [
      { name: 'Horarios', description: 'Horarios de apertura y cierre' },
      { name: 'Servicios', description: 'Cortes, tintes, tratamientos' },
      { name: 'Precios', description: 'Tarifas y promociones' },
      { name: 'Reservas', description: 'Cómo pedir cita y cancelar' },
      { name: 'Ubicación', description: 'Dirección y contacto' },
    ],
    suggestedMemories: [
      { fact: 'Abrimos de martes a sábado de 10:00 a 20:00', keyword: 'horario' },
      { fact: 'Trabajamos con cita previa', keyword: 'reservas,cita' },
      { fact: 'Disponemos de productos sin sulfatos y orgánicos', keyword: 'productos' },
      { fact: 'Estamos en la calle Comercio 45', keyword: 'ubicación,dirección' },
    ],
    sampleQuestions: [
      '¿Cuánto cuesta un corte?',
      '¿Trabajáis con cita previa?',
      '¿Tenéis productos sin sulfatos?',
    ]
  },

  hoteles: {
    id: 'hoteles',
    name: 'Hoteles',
    icon: '🏨',
    description: 'Hoteles, hostales y alojamientos turísticos',
    greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
    quickQuestions: ['Horario', 'Habitaciones', 'Precios', 'Servicios', 'Ubicación'],
    categories: [
      { name: 'Horarios', description: 'Check-in/out y recepción' },
      { name: 'Habitaciones', description: 'Tipos de habitación y servicios' },
      { name: 'Precios', description: 'Tarifas y ofertas' },
      { name: 'Servicios', description: 'Wifi, parking, desayuno, spa' },
      { name: 'Ubicación', description: 'Dirección, transporte, entorno' },
    ],
    suggestedMemories: [
      { fact: 'Check-in de 15:00 a 22:00, check-out hasta las 12:00', keyword: 'horario,checkin' },
      { fact: 'Disponemos de habitaciones dobles, suites y familiares', keyword: 'habitaciones' },
      { fact: 'El desayuno está incluido en todas las tarifas', keyword: 'desayuno,precio' },
      { fact: 'Disponemos de wifi gratuito en todas las instalaciones', keyword: 'servicios,wifi' },
      { fact: 'Estamos en la Avenida del Mar 12', keyword: 'ubicación,dirección' },
    ],
    sampleQuestions: [
      '¿A qué hora es el check-in?',
      '¿Tienen habitaciones con vistas?',
      '¿El desayuno está incluido?',
    ]
  },

  gimnasios: {
    id: 'gimnasios',
    name: 'Gimnasios',
    icon: '🏋️',
    description: 'Gimnasios, centros deportivos y fitness',
    greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
    quickQuestions: ['Horario', 'Precios', 'Clases', 'Instalaciones', 'Ubicación'],
    categories: [
      { name: 'Horarios', description: 'Horarios de apertura y cierre' },
      { name: 'Precios', description: 'Cuotas, bonos y promociones' },
      { name: 'Clases', description: 'Tipos de clases y horarios' },
      { name: 'Instalaciones', description: 'Sala de musculación, cardio, piscina' },
      { name: 'Ubicación', description: 'Dirección y acceso' },
    ],
    suggestedMemories: [
      { fact: 'Abrimos de lunes a sábado de 7:00 a 22:00, domingos de 9:00 a 14:00', keyword: 'horario' },
      { fact: 'Ofrecemos clases de yoga, pilates, spinning y zumba', keyword: 'clases' },
      { fact: 'Disponemos de sala de musculación, cardio y piscina cubierta', keyword: 'instalaciones' },
      { fact: 'Estamos en la Calle Deporte 8', keyword: 'ubicación,dirección' },
    ],
    sampleQuestions: [
      '¿Cuál es el horario del gimnasio?',
      '¿Qué tipos de clases ofrecéis?',
      '¿Cuánto cuesta la cuota mensual?',
    ]
  },

  clinicas: {
    id: 'clinicas',
    name: 'Clínicas',
    icon: '🏥',
    description: 'Clínicas, consultas y centros de salud',
    greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
    quickQuestions: ['Horario', 'Servicios', 'Citas', 'Ubicación', 'Contacto'],
    categories: [
      { name: 'Horarios', description: 'Horarios de consulta y atención' },
      { name: 'Servicios', description: 'Especialidades y tratamientos (solo información general)' },
      { name: 'Citas', description: 'Cómo pedir cita y cancelar' },
      { name: 'Ubicación', description: 'Dirección y accesibilidad' },
      { name: 'Contacto', description: 'Teléfono, email y atención al paciente' },
    ],
    suggestedMemories: [
      { fact: 'Atención de lunes a viernes de 9:00 a 20:00', keyword: 'horario' },
      { fact: 'Especialidades: odontología, dermatología, fisioterapia', keyword: 'servicios,especialidades' },
      { fact: 'Para urgencias llame al 900 123 456', keyword: 'urgencias,contacto' },
      { fact: 'Estamos en la Calle Salud 56', keyword: 'ubicación,dirección' },
      { fact: 'Las citas se pueden pedir por teléfono o por nuestra web', keyword: 'citas,reservas' },
    ],
    sampleQuestions: [
      '¿A qué hora abrís?',
      '¿Qué especialidades tenéis?',
      '¿Cómo puedo pedir cita?',
    ]
  },

  tiendas: {
    id: 'tiendas',
    name: 'Tiendas',
    icon: '🛍️',
    description: 'Tiendas, comercios y retail',
    greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
    quickQuestions: ['Horario', 'Productos', 'Precios', 'Envíos', 'Ubicación'],
    categories: [
      { name: 'Horarios', description: 'Horarios de apertura y cierre' },
      { name: 'Productos', description: 'Catálogo y disponibilidad' },
      { name: 'Precios', description: 'Tarifas, ofertas y promociones' },
      { name: 'Envíos', description: 'Política de envíos y devoluciones' },
      { name: 'Ubicación', description: 'Dirección y contacto' },
    ],
    suggestedMemories: [
      { fact: 'Abrimos de lunes a sábado de 10:00 a 21:00', keyword: 'horario' },
      { fact: 'Realizamos envíos a toda España en 24-48h', keyword: 'envíos' },
      { fact: 'Aceptamos tarjeta de crédito, Bizum y efectivo', keyword: 'pagos' },
      { fact: 'Estamos en la Calle Comercio 78', keyword: 'ubicación,dirección' },
      { fact: 'Disponemos de cambio de tallas y devoluciones hasta 30 días', keyword: 'devoluciones' },
    ],
    sampleQuestions: [
      '¿Cuál es el horario de la tienda?',
      '¿Hacéis envíos a domicilio?',
      '¿Aceptáis tarjetas de crédito?',
    ]
  },

  otro: {
    id: 'otro',
    name: 'Otro negocio',
    icon: '🏪',
    description: 'Cualquier otro tipo de negocio sin plantilla específica',
    greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
    quickQuestions: ['Horario', 'Servicios', 'Ubicación', 'Contacto'],
    categories: [
      { name: 'Horarios', description: 'Horarios de apertura y cierre' },
      { name: 'Servicios', description: 'Qué ofrece el negocio' },
      { name: 'Ubicación', description: 'Dirección y cómo llegar' },
      { name: 'Contacto', description: 'Teléfono, email y redes sociales' },
    ],
    suggestedMemories: [
      { fact: 'Abrimos de lunes a sábado de 9:00 a 20:00', keyword: 'horario' },
      { fact: 'Estamos en la Calle Principal 1', keyword: 'ubicación,dirección' },
      { fact: 'Puedes contactarnos por teléfono o email', keyword: 'contacto' },
    ],
    sampleQuestions: [
      '¿Cuál es vuestro horario?',
      '¿Dónde estáis?',
      '¿Cómo puedo contactaros?',
    ]
  }
};

desde_cero: {
  id: 'desde_cero',
  name: 'Desde cero',
  icon: '✨',
  description: 'Crea un bot personalizado sin plantilla',
  greeting: '¡Hola! Soy el asistente de {business_name}. ¿En qué puedo ayudarte?',
  quickQuestions: ['Información', 'Contacto', 'Ayuda'],
  categories: [],
  suggestedMemories: [],
  sampleQuestions: [
    '¿Qué puedes hacer?',
    '¿Cómo funciona?',
    '¿Qué información tienes?',
  ]
},


// ============================================================
// FUNCIONES DE UTILIDAD
// ============================================================

export const getNicho = (id) => {
  return NICHOS[id] || NICHOS.otro;
};

export const getNichosList = () => {
  return Object.values(NICHOS);
};

export const getNichoOptions = () => {
  return getNichosList().map(n => ({
    value: n.id,
    label: `${n.icon} ${n.name}`,
    description: n.description
  }));
};

export const getQuickQuestions = (nichoId) => {
  const nicho = getNicho(nichoId);
  return nicho ? nicho.quickQuestions : NICHOS.otro.quickQuestions;
};

export const getSuggestedGreeting = (nichoId, businessName) => {
  const nicho = getNicho(nichoId);
  const greeting = nicho ? nicho.greeting : NICHOS.otro.greeting;
  return greeting.replace('{business_name}', businessName || 'tu negocio');
};

export const getNichoOptions = () => {
  return getNichosList()
    .filter(n => n.id !== 'desde_cero')
    .map(n => ({
      value: n.id,
      label: `${n.icon} ${n.name}`,
      description: n.description
    }));
};

// Nueva función: obtener nichos "reales" (sin desde_cero)
export const getRealNichosList = () => {
  return getNichosList().filter(n => n.id !== 'desde_cero');
};
