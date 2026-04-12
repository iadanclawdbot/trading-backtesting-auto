---
name: update
description: Actualiza TASK.md, CHANGELOG.md y CLAUDE.md del proyecto para reflejar el estado actual de la sesion
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(git *)
---

# /update — Actualizacion de Proyecto

Actualiza los archivos del sistema del proyecto para reflejar el estado actual.

## Archivos que actualiza

| Archivo | Que se actualiza | Prioridad |
|---------|-----------------|-----------|
| TASK.md | Estado de tareas, nuevas tareas, completadas, bloqueos | SIEMPRE |
| CHANGELOG.md | Entry de sesion con formato estandar | SIEMPRE |
| CLAUDE.md | Notas activas, estado del proyecto, version si aplica | SIEMPRE |
| Otros archivos del proyecto | Segun lo que haya cambiado | SI HUBO CAMBIOS |

## Protocolo de ejecucion

### Paso 1: Leer estado actual
- Leer TASK.md, CHANGELOG.md, CLAUDE.md
- Identificar que cambio en esta sesion

### Paso 2: Proponer cambios

Antes de escribir, mostrar resumen:

```
Voy a actualizar:
- TASK.md: [que cambia]
- CHANGELOG.md: [que se agrega]
- CLAUDE.md: [que cambia]
- [otros archivos si aplica]

Excluyo: [archivos que no cambian]

Ok para ejecutar? Excluyo algun archivo?
```

### Paso 3: Esperar confirmacion
- "ok", "dale", "si", "adelante" → ejecutar todo
- "excluye X" → ejecutar sin ese archivo
- "solo X" → ejecutar solo ese archivo
- Instrucciones especificas → seguirlas

### Paso 4: Ejecutar
- Actualizar todos los archivos confirmados
- Respetar formatos existentes
- Mantener sincronizacion entre archivos

### Paso 5: Commit + Push
- `git add` de los archivos modificados (NUNCA `git add -A`)
- Commit: "update: [resumen breve]"
- Push a origin

### Paso 6: Confirmar
Resumen breve: "Actualizado: TASK.md, CHANGELOG.md, CLAUDE.md. Push OK."

## Excepciones — sin confirmacion
- Usuario dice "actualiza todo" o "actualiza directo"
- Marcar una tarea como completada (cambio menor)
- Instruccion especifica clara ("agrega esta tarea a TASK.md")

## Excepciones — SIEMPRE confirmar
- Eliminar tareas o contenido existente
- Cambiar estado o etapa del proyecto
- Modificar la instruccion principal de CLAUDE.md
- Modificar archivos de contexto del negocio

## Formato CHANGELOG entry

```markdown
## [YYYY-MM-DD] — Sesion N | Titulo descriptivo

### Completado
### Decisiones tomadas
### Proximos pasos
```

## Notas
- No inventar informacion — solo registrar lo que realmente paso
- Nombres de archivo: kebab-case, sin acentos, fechas ISO
