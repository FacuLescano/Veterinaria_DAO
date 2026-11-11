# Patitas & Co. - Frontend (vet_front)

Interfaz web para el Sistema de Gestión Veterinaria y Trazabilidad de Derivación de Muestras a Laboratorio Central.

Desarrollada con **React 18**, **TypeScript**, **Vite** y **Tailwind CSS v4**.

---

## 🚀 Requisitos previos

- **Node.js**: versión 18 o superior (recomendada v20+ o v22+).
- **npm**: versión 9 o superior.

---

## 🛠️ Instalación y configuración

1. Abrir una terminal y posicionarse en la carpeta del frontend:

```powershell
cd vet_front
```

2. Instalar las dependencias del proyecto:

```powershell
npm install
```

---

## 💻 Ejecución en modo desarrollo

Para iniciar el servidor de desarrollo local con recarga rápida (HMR):

```powershell
npm run dev
```

El servidor quedará disponible por defecto en:
👉 `http://localhost:3000` (o el puerto indicado por Vite en consola).

Vite reenvía las rutas `/api/*` y `/health` al backend en `http://127.0.0.1:8000`. Para cambiar el destino, configurar `VITE_API_PROXY_TARGET` en `vet_front/.env.local` y reiniciar el servidor. El encabezado muestra el estado de `/health`; las operaciones de los módulos aún usan datos demo en `localStorage` y no escriben en la API.

---

## 📦 Compilación para producción

Para validar tipos TypeScript y compilar el paquete optimizado para producción:

```powershell
npm run build
```

Los archivos compilados listos para servir se generarán en la carpeta `dist/`.

Para previsualizar localmente el build de producción:

```powershell
npm run preview
```

---

## 🧩 Módulos implementados en la interfaz

- **Módulo 1 (Pacientes & Atención)**: Fichas de responsables y mascotas, agenda de turnos con validación de superposición horaria, consultas médicas e historia clínica consolidada.
- **Módulo 2 (Órdenes & Muestras)**: Solicitud de análisis clínicos, rotulado de tubos y asignación de muestras con trazabilidad de estados.
- **Módulo 3 (Despacho & Trazabilidad)**: Preparación de conservadoras isotérmicas, colocación de precintos sanitarios y emisión del Remito Biológico oficial para transporte.
- **Módulo 4 (Recepción & Resultados)**: Recepción en laboratorio central con verificación de precinto sanitario (rechazo automático si está roto o violado), registro de incidencias y carga de informes de análisis.
- **Exportación & Visualizador Python**: Visualización de modelos orientados a objetos y scripts de cátedra.

