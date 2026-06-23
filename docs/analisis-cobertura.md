# Análisis de cobertura de tests — gestor-tareas-api

## Resumen de ejecución

```
pytest tests/ --cov=aplicacion --cov-report=term-missing
```

- **9 passed, 1 failed**
- **Cobertura global: 90%**
- Test fallido: `test_update_done_task_returns_409` (espera 409, recibe 200)

## Reporte de cobertura por módulo

| Módulo | Stmts | Miss | Cover | Líneas sin cubrir |
|---|---|---|---|---|
| `aplicacion/__init__.py` | 0 | 0 | 100% | — |
| `aplicacion/base_de_datos.py` | 12 | 4 | **67%** | 17-21 |
| `aplicacion/esquemas.py` | 22 | 0 | 100% | — |
| `aplicacion/modelos.py` | 20 | 0 | 100% | — |
| `aplicacion/principal.py` | 10 | 2 | **80%** | 14-15 |
| `aplicacion/rutas/__init__.py` | 0 | 0 | 100% | — |
| `aplicacion/rutas/tareas.py` | 51 | 6 | **88%** | 31, 34, 117, 120, 170-171 |

---

## Los 3 módulos con menor cobertura

### 1. `aplicacion/base_de_datos.py` — 67% (líneas 17-21)

**Qué no está cubierto:**
La función generadora `get_db()` completa: creación de sesión (`db = SessionLocal()`), `yield db`, y `db.close()` en el bloque `finally`. Los tests sobreescriben esta dependencia con `override_get_db`, por lo que la versión de producción nunca se ejecuta.

**Casos faltantes:**
- Test que invoque `get_db()` directamente y verifique que produce una sesión válida de SQLAlchemy.
- Test que verifique que la sesión se cierra correctamente tras el yield (rama `finally`).

**Esfuerzo estimado: Bajo**
Un solo test unitario que consuma el generador cubre las 4 líneas. Alternativa: eliminar el override y configurar los tests para usar la función original contra una BD de test dedicada.

---

### 2. `aplicacion/principal.py` — 80% (líneas 14-15)

**Qué no está cubierto:**
El cuerpo del `lifespan` async context manager:

```python
Base.metadata.create_all(bind=engine)  # línea 14
yield                                   # línea 15
```

Los tests crean las tablas directamente en `setup_module()` con `Base.metadata.create_all(bind=engine)`, por lo que el lifespan nunca se dispara durante la ejecución de tests.

**Casos faltantes:**
- Test de integración que arranque la app usando su lifecycle completo (e.g. con `async with lifespan(app)`).
- Verificar que las tablas se crean correctamente al iniciar la aplicación a través del lifespan.

**Esfuerzo estimado: Bajo**
Un test `async` que invoque el context manager directamente, o usar `TestClient` como context manager (`with TestClient(app) as c:`) para disparar el lifespan.

---

### 3. `aplicacion/rutas/tareas.py` — 88% (líneas 31, 34, 117, 120, 170-171)

**Qué no está cubierto:**

| Línea | Código | Caso faltante |
|---|---|---|
| 31 | `raise HTTPException(400)` en `get_task_or_404` | Ningún test envía `task_id <= 0` a `GET` o `DELETE /tasks/{id}` |
| 34 | `raise HTTPException(404)` en `get_task_or_404` | Ningún test consulta o elimina un id inexistente vía `GET /tasks/{id}` o `DELETE /tasks/{id}` |
| 117 | `raise HTTPException(404)` en `update_task` | Ningún test hace `PATCH` a un id inexistente |
| 120 | `raise HTTPException(422)` en `update_task` (título < 3 chars) | Ningún test envía un título corto en `PATCH` |
| 170-171 | `db.delete(task)` + `db.commit()` en `delete_task` | Ningún test ejecuta `DELETE /tasks/{id}` con un id válido existente |

**Tests sugeridos para cubrir todas las líneas:**

1. `GET /tasks/0` -> 400 (cubre línea 31)
2. `GET /tasks/999` -> 404 (cubre línea 34)
3. `PATCH /tasks/999` -> 404 (cubre línea 117)
4. `PATCH /tasks/{id}` con título `"ab"` -> 422 (cubre línea 120)
5. `DELETE /tasks/{id}` con id existente -> 204 (cubre líneas 170-171)
6. `DELETE /tasks/0` -> 400 (cubre línea 31 desde otro endpoint)
7. `DELETE /tasks/999` -> 404 (cubre línea 34 desde otro endpoint)

**Esfuerzo estimado: Bajo**
Son tests de error estándar, análogos a los que ya existen para otros endpoints. Cada test son ~3-5 líneas.

---

## Nota sobre el test fallido: `test_update_done_task_returns_409`

Este test falla porque:

1. Intenta poner la tarea en estado `done` con `PATCH`, pero el endpoint lo bloquea con **400** (línea 125-128 de `tareas.py`).
2. Al recibir 400, la tarea permanece en estado `pending`.
3. El segundo `PATCH` (cambiar título) se ejecuta exitosamente con **200**.
4. El test espera **409** pero recibe **200**.

**Causa raíz:** No existe una vía en la API para marcar una tarea como `done`, por lo que el escenario de conflicto que el test pretende verificar es inalcanzable con la implementación actual. Se necesita decidir si:

- (a) Se añade un endpoint dedicado para completar tareas (e.g. `POST /tasks/{id}/complete`).
- (b) Se permite la transición a `done` bajo ciertas condiciones en el PATCH existente.
- (c) Se corrige el test para reflejar el comportamiento actual (400 en vez de 409).
