# API de Gestión de Tareas

API REST para gestionar el ciclo de vida de tareas, construida con **FastAPI** y **SQLAlchemy**. Permite crear, consultar, actualizar parcialmente y eliminar tareas. Cada tarea posee un identificador único, título, descripción opcional, estado (`pending`, `in_progress`, `done`) y fecha de creación asignada automáticamente.

---

## Requisitos previos

| Requisito | Versión mínima |
|-----------|----------------|
| Python    | 3.12+          |
| pip       | 23+            |

### Dependencias de producción

| Paquete    | Versión  |
|------------|----------|
| FastAPI    | 0.136.1  |
| SQLAlchemy | 2.0.49   |
| Pydantic   | 2.13.4   |
| Uvicorn    | 0.46.0   |

### Dependencias de desarrollo y tests

| Paquete | Versión |
|---------|---------|
| pytest  | 9.0.3   |
| httpx   | 0.28.1  |
| anyio   | 4.13.0  |

---

## Instalación

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/rls4git/gestor-tareas-api.git
   cd gestor-tareas-api
   ```

2. **Crear y activar un entorno virtual:**

   ```bash
   python -m venv venv

   # macOS / Linux
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

3. **Instalar las dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

---

## Cómo arrancar la aplicación

```bash
uvicorn aplicacion.principal:app --reload
```

La API quedará disponible en `http://127.0.0.1:8000`.

La documentación interactiva (Swagger UI) se encuentra en `http://127.0.0.1:8000/docs`.

---

## Endpoints

### 1. Listar todas las tareas

| Campo       | Valor                          |
|-------------|--------------------------------|
| **Método**  | `GET`                          |
| **Ruta**    | `/tasks/`                      |
| **Parámetros** | Ninguno                     |

**Ejemplo de request:**

```bash
curl -X GET http://127.0.0.1:8000/tasks/
```

**Ejemplo de response** (`200 OK`):

```json
[
  {
    "id": 1,
    "title": "Revisar documentación",
    "description": "Revisar la documentación del proyecto",
    "status": "pending",
    "created_at": "2025-01-15T10:30:00"
  }
]
```

---

### 2. Contar tareas

| Campo       | Valor                          |
|-------------|--------------------------------|
| **Método**  | `GET`                          |
| **Ruta**    | `/tasks/count`                 |
| **Parámetros** | Ninguno                     |

**Ejemplo de request:**

```bash
curl -X GET http://127.0.0.1:8000/tasks/count
```

**Ejemplo de response** (`200 OK`):

```json
{
  "total": 5
}
```

---

### 3. Obtener una tarea por id

| Campo       | Valor                          |
|-------------|--------------------------------|
| **Método**  | `GET`                          |
| **Ruta**    | `/tasks/{task_id}`             |
| **Parámetros** | `task_id` (int, ruta) — Identificador de la tarea |

**Ejemplo de request:**

```bash
curl -X GET http://127.0.0.1:8000/tasks/1
```

**Ejemplo de response** (`200 OK`):

```json
{
  "id": 1,
  "title": "Revisar documentación",
  "description": "Revisar la documentación del proyecto",
  "status": "pending",
  "created_at": "2025-01-15T10:30:00"
}
```

**Respuesta de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

### 4. Crear una nueva tarea

| Campo       | Valor                          |
|-------------|--------------------------------|
| **Método**  | `POST`                         |
| **Ruta**    | `/tasks/`                      |
| **Parámetros** | Cuerpo JSON (ver abajo)     |

**Campos del cuerpo:**

| Campo         | Tipo   | Obligatorio | Descripción |
|---------------|--------|-------------|-------------|
| `title`       | string | Sí          | Título de la tarea (mínimo 3 caracteres) |
| `description` | string | No          | Descripción de la tarea |
| `status`      | string | No          | Estado inicial: `pending` (por defecto), `in_progress` o `done` |

**Ejemplo de request:**

```bash
curl -X POST http://127.0.0.1:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Implementar login", "description": "Añadir autenticación JWT"}'
```

**Ejemplo de response** (`201 Created`):

```json
{
  "id": 2,
  "title": "Implementar login",
  "description": "Añadir autenticación JWT",
  "status": "pending",
  "created_at": "2025-01-15T11:00:00"
}
```

**Respuesta de error** (`422 Unprocessable Entity`):

```json
{
  "detail": "El título debe tener al menos 3 caracteres"
}
```

---

### 5. Actualizar parcialmente una tarea

| Campo       | Valor                          |
|-------------|--------------------------------|
| **Método**  | `PATCH`                        |
| **Ruta**    | `/tasks/{task_id}`             |
| **Parámetros** | `task_id` (int, ruta) — Identificador de la tarea; cuerpo JSON con los campos a modificar |

**Campos del cuerpo (todos opcionales):**

| Campo         | Tipo   | Descripción |
|---------------|--------|-------------|
| `title`       | string | Nuevo título de la tarea |
| `description` | string | Nueva descripción |
| `status`      | string | Nuevo estado: `pending`, `in_progress` o `done` |

**Ejemplo de request:**

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/2 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

**Ejemplo de response** (`200 OK`):

```json
{
  "id": 2,
  "title": "Implementar login",
  "description": "Añadir autenticación JWT",
  "status": "in_progress",
  "created_at": "2025-01-15T11:00:00"
}
```

**Respuesta de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

### 6. Eliminar una tarea

| Campo       | Valor                          |
|-------------|--------------------------------|
| **Método**  | `DELETE`                       |
| **Ruta**    | `/tasks/{task_id}`             |
| **Parámetros** | `task_id` (int, ruta) — Identificador de la tarea |

**Ejemplo de request:**

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/1
```

**Ejemplo de response** (`204 No Content`):

Sin cuerpo de respuesta.

**Respuesta de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

## Cómo ejecutar los tests

```bash
pytest tests/ -v
```

Los tests utilizan una base de datos SQLite en memoria con `StaticPool` para garantizar el aislamiento entre casos de prueba. No modifican el archivo `tareas.db` de producción.

---

## Estructura del proyecto

```
gestor-tareas-api/
├── aplicacion/                # Paquete principal de la aplicación
│   ├── __init__.py
│   ├── principal.py           # Punto de entrada: instancia FastAPI y registro de routers
│   ├── base_de_datos.py       # Configuración del engine y sesión de SQLAlchemy
│   ├── modelos.py             # Modelos ORM (tabla tasks, enum TaskStatus)
│   ├── esquemas.py            # Esquemas Pydantic de entrada y respuesta
│   └── rutas/                 # Controladores HTTP
│       ├── __init__.py
│       └── tareas.py          # Endpoints REST de tareas
├── tests/                     # Tests de integración
│   ├── __init__.py
│   └── test_tasks.py          # Tests con pytest y SQLite en memoria
├── .devin/                    # Instrucciones para el agente Devin
│   └── AGENTS.md
├── .gitignore
├── requirements.txt           # Dependencias del proyecto
└── README.md
```

| Carpeta / Archivo       | Descripción |
|--------------------------|-------------|
| `aplicacion/`            | Contiene toda la lógica de la aplicación: modelos, esquemas, rutas y configuración de base de datos. |
| `aplicacion/rutas/`      | Define los endpoints REST agrupados por recurso. |
| `tests/`                 | Tests de integración que validan los endpoints utilizando `TestClient` de FastAPI. |
| `.devin/`                | Configuración e instrucciones específicas para el agente de desarrollo Devin. |
| `requirements.txt`       | Lista de dependencias de producción y desarrollo con versiones fijadas. |
