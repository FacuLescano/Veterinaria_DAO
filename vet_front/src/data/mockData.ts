import { 
  Responsable, 
  Mascota, 
  Turno, 
  ConsultaMedica, 
  OrdenAnalisis, 
  MuestraBiologica, 
  Conservadora, 
  RemitoBiologico, 
  PrecintoSanitario, 
  Incidencia, 
  ResultadoAnalisis 
} from '../types/veterinaria';

export const INITIAL_RESPONSABLES: Responsable[] = [
  {
    id: 'RESP-001',
    nombreCompleto: 'María Cecilia González',
    documento: '32.489.102',
    telefono: '+54 9 351 512-3489',
    email: 'cecilia.gonzalez@gmail.com',
    domicilio: 'Av. Colón 1420, Barrio Alberdi, Córdoba',
    fechaAlta: '2026-01-15'
  },
  {
    id: 'RESP-002',
    nombreCompleto: 'Carlos Eduardo Benítez',
    documento: '28.910.450',
    telefono: '+54 9 351 689-1122',
    email: 'carlos.benitez@yahoo.com.ar',
    domicilio: 'Chacabuco 830, Nueva Córdoba',
    fechaAlta: '2026-02-01'
  },
  {
    id: 'RESP-003',
    nombreCompleto: 'Dra. Ana Lucía Rossi',
    documento: '35.612.890',
    telefono: '+54 9 351 445-9011',
    email: 'anarossi.vet@outlook.com',
    domicilio: 'Duarte Quirós 2250, Alto Alberdi',
    fechaAlta: '2026-02-20'
  }
];

export const INITIAL_MASCOTAS: Mascota[] = [
  {
    id: 'MASC-001',
    responsableId: 'RESP-001',
    nombre: 'Luna',
    especie: 'Canino',
    raza: 'Golden Retriever',
    sexo: 'Hembra',
    fechaNacimientoAprox: '2021-04-10',
    pesoKg: 28.5,
    microchip: '981098102341902',
    alergias: 'Sensible a picadura de pulga',
    fotoUrl: '/assets/pets/luna.jpg',
  },
  {
    id: 'MASC-002',
    responsableId: 'RESP-002',
    nombre: 'Milo',
    especie: 'Felino',
    raza: 'Mestizo',
    sexo: 'Macho',
    fechaNacimientoAprox: '2023-08-14',
    pesoKg: 4.2,
    alergias: 'Ninguna conocida',
    fotoUrl: '/assets/pets/milo.jpg',
  },
  {
    id: 'MASC-003',
    responsableId: 'RESP-003',
    nombre: 'Thor',
    especie: 'Canino',
    raza: 'Bulldog Francés',
    sexo: 'Macho',
    fechaNacimientoAprox: '2022-11-03',
    pesoKg: 12.8,
    microchip: '981098109988112',
    alergias: 'Dermatitis atópica estacional',
    fotoUrl: '/assets/pets/thor.jpg',
  }
];

export const INITIAL_TURNOS: Turno[] = [
  {
    id: 'TUR-101',
    mascotaId: 'MASC-001',
    responsableId: 'RESP-001',
    veterinario: 'Dr. Alejandro Morales (M.P. 4812)',
    fecha: '2026-11-09',
    hora: '09:30',
    motivo: 'Decaimiento y control post-tratamiento',
    estado: 'Atendido'
  },
  {
    id: 'TUR-102',
    mascotaId: 'MASC-002',
    responsableId: 'RESP-002',
    veterinario: 'Dra. Sofía Carrizo (M.P. 5190)',
    fecha: '2026-11-09',
    hora: '11:00',
    motivo: 'Vómitos esporádicos y pérdida de apetito',
    estado: 'Confirmado'
  },
  {
    id: 'TUR-103',
    mascotaId: 'MASC-003',
    responsableId: 'RESP-003',
    veterinario: 'Dr. Alejandro Morales (M.P. 4812)',
    fecha: '2026-11-10',
    hora: '10:00',
    motivo: 'Control dermatológico y vacuna antirrábica',
    estado: 'Pendiente'
  }
];

export const INITIAL_CONSULTAS: ConsultaMedica[] = [
  {
    id: 'CON-001',
    mascotaId: 'MASC-001',
    veterinario: 'Dr. Alejandro Morales',
    fecha: '2026-11-09',
    hora: '09:45',
    motivo: 'Luna presenta letargo de 48hs y leve dolor abdominal.',
    evaluacionClinica: 'Mucosas pálidas, T° 39.1°C, linfonódulos reactivos, abdomen blando doloroso en hipocondrio.',
    diagnosticoPresuntivo: 'Posible proceso infeccioso o hepático a descartar.',
    tratamiento: 'Fluidoterapia de sostén con Ringer Lactato y analgésico oral.',
    vacunaAplicada: 'Antirrábica anual al día',
    requiereAnalisis: true,
    turnoId: 'TUR-101'
  }
];

export const INITIAL_ORDENES: OrdenAnalisis[] = [
  {
    id: 'ORD-2026-001',
    consultaId: 'CON-001',
    mascotaId: 'MASC-001',
    veterinarioSolicitante: 'Dr. Alejandro Morales',
    fechaSolicitud: '2026-11-09 10:15',
    prioridad: 'Urgente',
    estado: 'Enviada',
    detalles: [
      {
        id: 'DET-01',
        tipoAnalisis: 'Hemograma Completo',
        indicaciones: 'Evaluar hematocrito, leucocitos y plaquetas por palidez de mucosas.',
        muestraAsociadaId: 'MUE-9101',
        estado: 'En proceso'
      },
      {
        id: 'DET-02',
        tipoAnalisis: 'Perfil Bioquímico Hepático',
        indicaciones: 'Determinación de ALT, AST, Fosfatasa Alcalina y Bilirrubinas.',
        muestraAsociadaId: 'MUE-9102',
        estado: 'En proceso'
      }
    ]
  }
];

export const INITIAL_MUESTRAS: MuestraBiologica[] = [
  {
    id: 'MUE-9101',
    ordenId: 'ORD-2026-001',
    identificacionFisica: 'TUB-LILA-9101',
    tipoMaterial: 'Sangre con EDTA (Tubo lila)',
    fechaHoraExtraccion: '2026-11-09 10:30',
    responsableExtraccion: 'Dra. Sofía Carrizo',
    condicionConservacion: 'Refrigerada (2° a 8°C)',
    estadoActual: 'En tránsito',
    conservadoraId: 'CON-01',
    remitoId: 'REM-2026-012',
    historialTrazabilidad: [
      {
        id: 'TRAZ-01',
        fechaHora: '2026-11-09 10:30',
        estadoNuevo: 'Extraída',
        responsable: 'Dra. Sofía Carrizo',
        ubicacion: 'Consultorio 2 - Clínica Central',
        observaciones: 'Punción venosa cefálica sin incidentes.'
      },
      {
        id: 'TRAZ-02',
        fechaHora: '2026-11-09 11:00',
        estadoAnterior: 'Extraída',
        estadoNuevo: 'Empaquetada',
        responsable: 'Enf. Juan Méndez',
        ubicacion: 'Área de Embalaje y Despacho',
        observaciones: 'Ubicada en conservadora CON-01 con gel refrigerante.'
      },
      {
        id: 'TRAZ-03',
        fechaHora: '2026-11-09 11:45',
        estadoAnterior: 'Empaquetada',
        estadoNuevo: 'En tránsito',
        responsable: 'Chofer Roberto Gómez (Transportes BioLog)',
        ubicacion: 'En ruta hacia Laboratorio Central BioVet',
        observaciones: 'Despacho verificado con remito REM-2026-012.'
      }
    ]
  },
  {
    id: 'MUE-9102',
    ordenId: 'ORD-2026-001',
    identificacionFisica: 'TUB-ROJO-9102',
    tipoMaterial: 'Suero sanguíneo (Tubo rojo)',
    fechaHoraExtraccion: '2026-11-09 10:35',
    responsableExtraccion: 'Dra. Sofía Carrizo',
    condicionConservacion: 'Refrigerada (2° a 8°C)',
    estadoActual: 'En tránsito',
    conservadoraId: 'CON-01',
    remitoId: 'REM-2026-012',
    historialTrazabilidad: [
      {
        id: 'TRAZ-04',
        fechaHora: '2026-11-09 10:35',
        estadoNuevo: 'Extraída',
        responsable: 'Dra. Sofía Carrizo',
        ubicacion: 'Consultorio 2 - Clínica Central',
        observaciones: 'Muestra centrifugada a 3000 RPM por 10 min.'
      },
      {
        id: 'TRAZ-05',
        fechaHora: '2026-11-09 11:00',
        estadoAnterior: 'Extraída',
        estadoNuevo: 'Empaquetada',
        responsable: 'Enf. Juan Méndez',
        ubicacion: 'Área de Embalaje',
        observaciones: 'Empaquetada junto a MUE-9101.'
      },
      {
        id: 'TRAZ-06',
        fechaHora: '2026-11-09 11:45',
        estadoAnterior: 'Empaquetada',
        estadoNuevo: 'En tránsito',
        responsable: 'Chofer Roberto Gómez',
        ubicacion: 'Móvil de derivaciones',
        observaciones: 'En camino.'
      }
    ]
  }
];

export const INITIAL_CONSERVADORAS: Conservadora[] = [
  {
    id: 'CON-01',
    nombre: 'Conservadora Isotérmica Azul A1',
    capacidadMuestras: 12,
    temperaturaRequerida: '2°C a 8°C (Refrigerado)',
    disponible: false
  },
  {
    id: 'CON-02',
    nombre: 'Conservadora Isotérmica Roja B2',
    capacidadMuestras: 8,
    temperaturaRequerida: '-20°C (Congelado con hielo seco)',
    disponible: true
  },
  {
    id: 'CON-03',
    nombre: 'Conservadora Portátil C3',
    capacidadMuestras: 6,
    temperaturaRequerida: 'Ambiente controlado (15°C a 25°C)',
    disponible: true
  }
];

export const INITIAL_PRECINTOS: PrecintoSanitario[] = [
  {
    id: 'PREC-ID-01',
    codigoUnico: 'PREC-48921',
    conservadoraId: 'CON-01',
    colocadoPor: 'Enf. Juan Méndez',
    fechaHoraColocacion: '2026-11-09 11:15'
  }
];

export const INITIAL_REMITOS: RemitoBiologico[] = [
  {
    id: 'REM-2026-012',
    fechaEmision: '2026-11-09 11:30',
    clinicaOrigen: 'Clínica Veterinaria Patitas & Co. - Sede Central',
    laboratorioDestino: 'Laboratorio Central de Derivación BioVet',
    responsableDespacho: 'Enf. Juan Méndez',
    transportista: 'Transportes BioLog (Roberto Gómez)',
    conservadoraId: 'CON-01',
    precintoCodigo: 'PREC-48921',
    muestrasIds: ['MUE-9101', 'MUE-9102'],
    estado: 'Despachado',
    temperaturaDespachoC: 4.8,
    observaciones: 'Muestras biológicas refrigeradas en cadena de frío estricta.'
  }
];

export const INITIAL_INCIDENCIAS: Incidencia[] = [];

export const INITIAL_RESULTADOS: ResultadoAnalisis[] = [
  {
    id: 'RES-001',
    ordenId: 'ORD-PREV-90',
    detalleAnalisisId: 'DET-PREV-01',
    muestraId: 'MUE-8801',
    fechaRecepcionResultado: '2026-11-08 17:00',
    laboratorioNombre: 'Laboratorio Central BioVet',
    valores: [
      { parametro: 'Glóbulos Rojos (RBC)', valor: '6.8', unidad: 'M/uL', rangoReferencia: '5.5 - 8.5', alerta: 'Normal' },
      { parametro: 'Hemoglobina', valor: '15.2', unidad: 'g/dL', rangoReferencia: '12.0 - 18.0', alerta: 'Normal' },
      { parametro: 'Hematocrito', valor: '44', unidad: '%', rangoReferencia: '37 - 55', alerta: 'Normal' },
      { parametro: 'Glóbulos Blancos (WBC)', valor: '9.2', unidad: 'K/uL', rangoReferencia: '6.0 - 17.0', alerta: 'Normal' }
    ],
    conclusionDiagnostica: 'Hemograma completo dentro de los parámetros de referencia de la especie canina.',
    nombreArchivoAdjunto: 'Informe_Hemograma_MUE-8801.pdf',
    estado: 'Validado por Veterinario',
    validadoPor: 'Dr. Alejandro Morales'
  }
];
