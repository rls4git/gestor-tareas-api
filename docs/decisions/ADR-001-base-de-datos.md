# ADR-001: Elección de SQLite como base de datos

## Estado

**Aceptado**

## Contexto

La API de Gestión de Tareas necesita una base de datos para persistir el ciclo de vida de las tareas (creación, consulta, actualización parcial y eliminación). Los requisitos del sistema son:

- Proyecto de alcance reducido con un modelo de datos sencillo (una tabla principal `tasks`).
- Despliegue simple, sin necesidad de infraestructura externa ni administración de servidores de base de datos.
- Desarrollo local ágil: los desarrolladores deben poder clonar el repositorio y ejecutar la API sin configurar servicios adicionales.
- Entorno de tests aislado con base de datos en memoria para garantizar rapidez y reproducibilidad.
- Compatibilidad nativa con Python y SQLAlchemy sin drivers adicionales.

## Decisión

Se ha elegido **SQLite** como motor de base de datos, almacenando los datos en el archivo local `tareas.db`. La configuración utiliza `check_same_thread=False` para permitir el acceso concurrente desde los hilos del servidor ASGI (Uvicorn/FastAPI).

### Razones principales

1. **Cero configuración**: SQLite es una biblioteca embebida que no requiere instalar, configurar ni mantener un servidor de base de datos independiente.
2. **Incluido en Python**: El módulo `sqlite3` forma parte de la biblioteca estándar de Python; no se necesitan drivers adicionales en `requirements.txt`.
3. **Simplicidad operativa**: Un único archivo (`tareas.db`) contiene toda la base de datos, lo que facilita backups, migración y desarrollo local.
4. **Tests en memoria**: SQLAlchemy permite crear una instancia SQLite en memoria con `StaticPool`, proporcionando tests rápidos y completamente aislados sin tocar datos reales.
5. **Coherencia con el alcance del proyecto**: Para una API de gestión de tareas con un único modelo y volumen de datos moderado, SQLite ofrece rendimiento más que suficiente.
6. **Portabilidad**: El archivo de base de datos es multiplataforma y puede copiarse entre sistemas sin conversión.

## Alternativas consideradas

### PostgreSQL

| Aspecto | Detalle |
|---------|---------|
| **Ventajas** | Soporte completo de concurrencia (MVCC), tipos de datos avanzados (JSONB, arrays), extensiones (PostGIS, pg_trgm), excelente rendimiento en cargas de trabajo concurrentes, replicación nativa y ecosistema maduro para producción a gran escala. |
| **Inconvenientes** | Requiere instalar y administrar un servidor independiente (o un contenedor Docker), configurar credenciales, puertos y conexiones. Añade complejidad al onboarding de desarrolladores y a la pipeline de CI. Necesita un driver Python adicional (`psycopg2` o `asyncpg`). Sobredimensionado para el volumen y modelo de datos actual del proyecto. |

### MySQL

| Aspecto | Detalle |
|---------|---------|
| **Ventajas** | Ampliamente adoptado en la industria, buena documentación, soporte de replicación maestro-esclavo, rendimiento sólido en operaciones de lectura intensiva, herramientas de administración gráfica disponibles (MySQL Workbench, phpMyAdmin). |
| **Inconvenientes** | Igual que PostgreSQL, requiere un servidor independiente y configuración adicional. Necesita un driver Python (`mysqlclient` o `PyMySQL`). Históricamente menos estricto en validación de datos que PostgreSQL. El modelo de licenciamiento dual (GPL/comercial) puede ser relevante en algunos contextos corporativos. No aporta beneficios significativos sobre PostgreSQL para este caso de uso. |

## Consecuencias

### A corto plazo

- El proyecto se mantiene ligero y fácil de configurar: `pip install -r requirements.txt` es suficiente para empezar.
- Los tests se ejecutan rápidamente gracias a SQLite en memoria.
- No hay dependencias de infraestructura externa para desarrollo ni CI.

### A largo plazo

- **Concurrencia limitada**: SQLite usa bloqueos a nivel de archivo. Si el proyecto escala a múltiples usuarios concurrentes con escrituras frecuentes, se producirán cuellos de botella. En ese escenario será necesario migrar a PostgreSQL.
- **Funcionalidades SQL reducidas**: SQLite no soporta `ALTER TABLE` completo, tipos avanzados ni procedimientos almacenados. Migraciones de esquema complejas requerirán recrear tablas.
- **No apta para despliegues distribuidos**: En entornos con múltiples instancias de la aplicación (contenedores, serverless), SQLite no es viable porque el archivo no se comparte fácilmente entre procesos en diferentes máquinas.
- **Ruta de migración clara**: Gracias al uso de SQLAlchemy como ORM, la migración a PostgreSQL o MySQL implica cambiar únicamente la URL de conexión y el driver, sin reescribir las consultas ni los modelos.
- **Monitorización limitada**: No dispone de herramientas de monitorización, query planner avanzado ni métricas de rendimiento como las que ofrecen PostgreSQL o MySQL.

### Criterios para reconsiderar esta decisión

- El proyecto requiere más de ~100 escrituras concurrentes por segundo.
- Se despliega en un entorno multi-instancia (Kubernetes, serverless).
- Se necesitan tipos de datos avanzados (JSONB, arrays, geoespaciales).
- Se requiere replicación o alta disponibilidad.
