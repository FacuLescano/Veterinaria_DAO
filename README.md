# Sistema de Gestión Veterinaria

## 1. Descripción del proyecto

El Sistema de Gestión Veterinaria es un proyecto académico de Ingeniería en Sistemas destinado a gestionar las operaciones de una red de clínicas veterinarias y su laboratorio central de análisis.

El sistema busca centralizar la información de clientes, mascotas, consultas médicas, derivaciones de muestras biológicas y resultados de laboratorio, permitiendo mantener la trazabilidad de las muestras durante todo su ciclo de vida.

Uno de los aspectos principales del proyecto es garantizar la integridad de la información y la correcta gestión del transporte de muestras, desde su extracción en una clínica hasta su recepción, procesamiento y diagnóstico en el laboratorio central.

### Objetivos principales

- Administrar clientes y sus mascotas.
- Mantener las historias clínicas de las mascotas.
- Registrar consultas médicas y órdenes de derivación al laboratorio.
- Gestionar el empaquetado, los remitos biológicos y los precintos sanitarios.
- Registrar y consultar la trazabilidad de las muestras biológicas.
- Controlar la recepción de muestras y rechazar aquellas que presenten un precinto sanitario roto.
- Registrar los análisis realizados y sus resultados.
- Emitir comprobantes de atención y generar reportes de gestión.

## 2. Tecnologías utilizadas

### Backend

- **Python:** lenguaje de programación principal.
- **FastAPI:** framework para desarrollar la API REST.
- **Uvicorn:** servidor ASGI utilizado para ejecutar la aplicación.
- **SQLAlchemy:** ORM para interactuar con la base de datos mediante objetos Python.
- **SQLite:** sistema de gestión de bases de datos relacional.
- **Pydantic Settings:** administración de configuraciones mediante variables de entorno.
- **Pytest:** ejecución de pruebas automatizadas.
- **HTTPX:** cliente HTTP utilizado para probar los endpoints de la API.

### Frontend

- **React 18:** librería para la construcción de interfaces de usuario interactivas basadas en componentes.
- **TypeScript:** tipado estático, interfaces de dominio y verificación en tiempo de desarrollo.
- **Vite:** entorno de desarrollo de última generación con recarga ultrarrápida (HMR) y empaquetador para producción.
- **Tailwind CSS v4:** estilos utilitarios modernos y diseño responsivo adaptado a dispositivos de escritorio y móviles.
- **Lucide React:** iconografía especializada para interfaces médicas, veterinarias y de laboratorio.

## 3. Estructura del repositorio

```text
veterinaria/
├── README.md
├── .gitignore
├── .env.example
├── docs/
├── vet_back/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── dao/
│   │   └── db/
│   ├── test/
│   ├── requirements.txt
│   └── .env.example
└── vet_front/
    ├── README.md
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    ├── public/
    └── src/
        ├── components/
        ├── context/
        ├── data/
        └── types/
```

### Responsabilidad de las carpetas

| Carpeta o archivo | Responsabilidad |
|---|---|
| `vet_back/app/main.py` | Punto de entrada de la aplicación FastAPI. |
| `vet_back/app/api/` | Definición y organización de los endpoints de la API. |
| `vet_back/app/core/` | Configuraciones generales y componentes transversales. |
| `vet_back/app/models/` | Definición de las entidades del modelo de datos con SQLAlchemy. |
| `vet_back/app/schemas/` | Esquemas de validación de solicitudes y respuestas con Pydantic. |
| `vet_back/app/services/` | Reglas de negocio y lógica de aplicación. |
| `vet_back/app/dao/` | Acceso a datos y persistencia. |
| `vet_back/app/db/` | Configuración del motor y la sesión de base de datos. |
| `vet_back/test/` | Pruebas automatizadas unitarias y de integración. |
| `vet_front/src/components/` | Componentes visuales organizados por módulo (pacientes, órdenes, despacho, recepción). |
| `vet_front/src/context/` | Estado global de la aplicación (VeterinaryContext) con persistencia en localStorage. |
| `vet_front/src/types/` | Definiciones TypeScript del dominio veterinario y trazabilidad. |
| `backend/app/models/` | Modelos de dominio y entidades mapeadas con SQLAlchemy. |
| `backend/app/schemas/` | Esquemas de validación y estructuras de entrada y salida de la API. |
| `backend/app/services/` | Reglas de negocio y coordinación de operaciones. |
| `backend/app/dao/` | Acceso a datos y consultas de persistencia. |
| `backend/app/db/` | Configuración de la base de datos y administración de sesiones. |
| `backend/tests/` | Pruebas automatizadas del backend. |
| `docs/` | Documentación funcional, técnica y de diseño del sistema. |
| `frontend/` | Aplicación de interfaz de usuario. |

Los archivos `__init__.py` permiten organizar los módulos como paquetes de Python. En esta etapa pueden permanecer vacíos.

## 4. Requisitos previos

Antes de ejecutar el proyecto, es necesario contar con las siguientes herramientas:

- **Git:** para clonar el repositorio y administrar los cambios.
- **Python 3.11 o una versión compatible:** para ejecutar el backend. Se recomienda utilizar la misma versión de Python entre los integrantes del equipo.
- **pip:** administrador de paquetes de Python, incluido normalmente con su instalación.
- **PowerShell o una terminal equivalente:** para ejecutar los comandos de configuración.

Para verificar que Python está instalado, ejecutar:

```powershell
py --version
```

También se puede comprobar con:

```powershell
python --version
```

Para verificar Git:

```powershell
git --version
```

Si alguno de estos comandos no funciona, verificar la instalación y que la herramienta esté disponible en la variable de entorno `PATH`.

## 5. Instalación y configuración del backend

### Paso 1. Obtener el repositorio

Si todavía no tenés el proyecto en tu computadora, cloná el repositorio:

```powershell
git clone URL_DEL_REPOSITORIO
```

Reemplazá `URL_DEL_REPOSITORIO` por la URL real del repositorio de GitHub.

Después, ingresá en la carpeta del proyecto:

```powershell
cd veterinaria
```

Si ya tenés el repositorio clonado, simplemente abrí una terminal en su carpeta raíz.

### Paso 2. Ingresar al backend

```powershell
cd backend
```

Los siguientes comandos de instalación y ejecución del backend deben realizarse desde esta carpeta, salvo que se indique lo contrario.

### Paso 3. Crear el entorno virtual

Se recomienda utilizar un entorno virtual para aislar las dependencias del proyecto de las demás instalaciones de Python de la computadora.

En Windows, ejecutar:

```powershell
py -m venv .venv
```

Esto crea la carpeta `.venv/`, que contendrá el intérprete y las dependencias instaladas para este proyecto.

El entorno virtual no debe subirse a GitHub.

### Paso 4. Activar el entorno virtual

En PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Si la activación fue exitosa, la terminal mostrará normalmente `(.venv)` al comienzo de la línea.

Por ejemplo:

```text
(.venv) PS C:\proyectos\veterinaria\backend>
```

Esto indica que los comandos de Python y `pip` se ejecutarán utilizando el entorno virtual activado.

**Si PowerShell bloquea la ejecución del script de activación**, se puede abrir CMD y ejecutar:

```bat
.venv\Scripts\activate.bat
```

Como alternativa, es posible ejecutar directamente el intérprete del entorno virtual sin activarlo:

```powershell
.\.venv\Scripts\python.exe --version
```

### Paso 5. Instalar las dependencias

Con el entorno virtual activado, actualizar `pip`:

```powershell
python -m pip install --upgrade pip
```

Instalar las dependencias declaradas por el proyecto:

```powershell
pip install -r requirements.txt
```

El archivo `requirements.txt` contiene las librerías necesarias para ejecutar y desarrollar el backend. Cada integrante debe instalarlas en su propio entorno virtual.

Si todavía no existe un `requirements.txt` con las dependencias del proyecto, primero hay que generarlo o completarlo a partir de la configuración de desarrollo acordada por el equipo.

### Paso 6. Configurar las variables de entorno

Si el proyecto necesita variables de entorno, revisar el archivo `.env.example` y utilizarlo como referencia para crear un archivo `.env` local.

Por ejemplo, si existe un archivo de ejemplo en la carpeta `backend/`:

```powershell
Copy-Item .env.example .env
```

Completar las variables requeridas según la configuración del proyecto.

El archivo `.env` puede contener configuraciones locales o credenciales y **no debe subirse al repositorio**. El archivo `.env.example` debe incluir solamente nombres de variables y valores de ejemplo que no sean secretos.

Si el backend todavía no utiliza variables de entorno, este paso puede omitirse.

## 6. Ejecutar el backend

Una vez instaladas las dependencias y activado el entorno virtual, verificar que la terminal se encuentre dentro de la carpeta `backend/`.

Ejecutar:

```powershell
uvicorn app.main:app --reload
```

### ¿Qué significa este comando?

- `uvicorn`: inicia el servidor que ejecuta la aplicación ASGI.
- `app.main`: indica que debe buscar el módulo `main.py` dentro del paquete `app`.
- `:app`: indica que debe utilizar el objeto llamado `app` definido en `main.py`.
- `--reload`: reinicia el servidor automáticamente cuando detecta cambios en los archivos de código. Esta opción se utiliza durante el desarrollo, no como configuración de producción.

Si todo funciona correctamente, Uvicorn mostrará un mensaje indicando que el servidor está ejecutándose, normalmente en:

```text
http://127.0.0.1:8000
```

**Importante:** no cierres la terminal mientras quieras mantener el servidor funcionando. Para detenerlo, presioná `Ctrl + C`.

### Verificar que la API funciona

Con el servidor iniciado, abrí el navegador y visitá las siguientes direcciones:

| Dirección | Descripción |
|---|---|
| `http://127.0.0.1:8000/health` | Comprueba el estado de la API, si el endpoint `/health` está implementado. |
| `http://127.0.0.1:8000/docs` | Abre la documentación interactiva de Swagger UI. |
| `http://127.0.0.1:8000/redoc` | Abre la documentación alternativa de la API. |

Swagger UI permite visualizar los endpoints disponibles, consultar sus parámetros y probar las solicitudes HTTP desde el navegador.

La documentación se genera automáticamente a partir de los endpoints y esquemas definidos en FastAPI.

## 7. Configuración y ejecución del frontend (`vet_front`)

La aplicación web frontend de **Patitas & Co.** está desarrollada en **React 18** con **TypeScript**, **Vite** y **Tailwind CSS v4**. Permite operar los 4 módulos funcionales del sistema con interfaz gráfica moderna y responsiva.

### Requisitos previos

- **Node.js**: versión 18 o superior instalada (verificar con `node -v`).
- **npm**: versión 9 o superior (verificar con `npm -v`).

### Paso a paso para ejecutar el frontend

1. Abrir una nueva terminal y navegar a la carpeta `vet_front/`:

```powershell
cd vet_front
```

2. Instalar las dependencias del proyecto:

```powershell
npm install
```

3. Iniciar el servidor de desarrollo local:

```powershell
npm run dev
```

4. Abrir el navegador en la dirección indicada por Vite:
👉 `http://localhost:3000`

### Compilación y verificación para producción

Para validar los tipos TypeScript y generar el paquete estático optimizado para producción:

```powershell
npm run build
```

Los artefactos listos para desplegar se generarán en `vet_front/dist/`.

### Módulos funcionales disponibles en la interfaz

| Módulo | Funcionalidades principales |
|---|---|
| **1. Pacientes & Atención** | Alta y edición de responsables y mascotas, agenda de turnos con validación de superposición horaria, registro de consultas e historia clínica. |
| **2. Órdenes & Muestras** | Emisión de solicitudes de análisis clínicos vinculadas a consultas, extracción y rotulado de tubos/muestras biológicas y trazabilidad de estados. |
| **3. Despacho & Trazabilidad** | Preparación de conservadoras isotérmicas, asignación y validación de precintos sanitarios y generación/impresión del Remito Biológico oficial. |
| **4. Recepción & Resultados** | Recepción de envíos en laboratorio central, verificación de precinto (rechazo automático si está violado), registro de incidencias y carga de informes de análisis. |

## 8. Base de datos

El proyecto utilizará SQLite como sistema de gestión de base de datos y SQLAlchemy como ORM.

La configuración de conexión se centralizará en el módulo correspondiente dentro de `backend/app/db/`.

La aplicación utilizará un `engine` compartido y una fábrica de sesiones para administrar las operaciones contra la base de datos.

El acceso a los datos se organizará mediante el patrón DAO (*Data Access Object*), separando las consultas y operaciones de persistencia de las reglas de negocio.

La base de datos local tendrá un archivo con extensión `.db`, cuya ubicación dependerá de la configuración definida en el backend. Estos archivos locales no deben subirse al repositorio.

**Nota:** instalar SQLAlchemy no crea automáticamente las tablas. Para disponer del esquema completo será necesario implementar los modelos y el mecanismo de creación o migración correspondiente. Hasta que esto se configure, la API puede ejecutarse sin tener todas las tablas creadas.

## 9. Ejecutar las pruebas

Las pruebas automatizadas se almacenarán en `backend/tests/`.

Con el entorno virtual activado y desde la carpeta `backend/`, ejecutar:

```powershell
pytest
```

Para obtener una salida más detallada:

```powershell
pytest -v
```

Las pruebas se irán incorporando a medida que se implementen los servicios, DAO y endpoints.

## 10. Flujo de trabajo con Git

Se utilizará Git para versionar el código y GitHub para alojar el repositorio y facilitar la colaboración.

Antes de comenzar una tarea:

```powershell
git pull
```

Después de realizar cambios, revisar su estado:

```powershell
git status
```

Agregar los archivos que se desean incluir en el próximo commit:

```powershell
git add .
```

Crear un commit descriptivo:

```powershell
git commit -m "feat: agregar gestion de clientes"
```

Enviar los cambios a la rama remota correspondiente:

```powershell
git push
```

Los nombres de ramas y el proceso de integración deberán respetar las convenciones acordadas por el equipo.

No deben versionarse la carpeta `.venv/`, los archivos `.env`, las bases de datos locales ni otros archivos generados que estén excluidos en `.gitignore`.

## 11. Convenciones de desarrollo

Para mantener una estructura consistente, se recomienda:

- Utilizar nombres de variables, clases y funciones descriptivos.
- Mantener separadas las responsabilidades de API, servicios, DAO, modelos y configuración de base de datos.
- Implementar las reglas de negocio en la capa de servicios, evitando concentrarlas en los endpoints.
- Utilizar los DAO para encapsular las consultas y operaciones de persistencia.
- Validar los datos recibidos por la API mediante esquemas.
- Incorporar pruebas automatizadas para las reglas críticas del dominio.
- Documentar las decisiones de diseño y las reglas de negocio relevantes.
- No guardar credenciales ni datos sensibles directamente en el código fuente.

## 12. Alcance funcional

El sistema se desarrollará de forma incremental, priorizando los procesos principales del dominio veterinario:

1. Administración de clientes y mascotas.
2. Gestión de historias clínicas y consultas.
3. Emisión de órdenes de derivación.
4. Empaquetado de muestras, generación de remitos y control de precintos.
5. Registro de envíos y trazabilidad de las muestras.
6. Recepción en el laboratorio y validación de condiciones sanitarias.
7. Registro de análisis, resultados y comprobantes de atención.
8. Generación de reportes de gestión.

Se deberá preservar el historial de estados de las muestras para permitir su seguimiento desde la extracción hasta el análisis o rechazo.

## 13. Estado del proyecto

El proyecto se encuentra en etapa de preparación de la estructura del repositorio y configuración inicial del backend. Los módulos funcionales, el esquema definitivo de base de datos, los endpoints y la interfaz de usuario se implementarán progresivamente.

Este README se actualizará conforme se incorporen nuevas funcionalidades, configuraciones y procedimientos de instalación.