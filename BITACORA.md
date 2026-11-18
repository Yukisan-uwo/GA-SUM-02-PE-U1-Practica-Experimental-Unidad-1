# Bitácora del equipo

**Integrantes:** Joseph [apellido] · Mera Jumbo Allison (`ameraj2-bit`) · Roger [apellido] · Mario [apellido]

## Formato de cada entrada

### AAAA-MM-DD · Nombre de quien registra
- **Integrantes presentes:** quiénes trabajaron en esa sesión.
- **Commit(s):** `hash corto` — mensaje del commit.
- **Qué se hizo:** tarea realizada.
- **Problema encontrado:** dificultad o aspecto pendiente.
- **Solución y comprobación:** qué se cambió y cómo se verificó que funcionó.
- **Tiempo dedicado:** X h Y min.

---

## Registro de trabajo

### 2026-11-17 · [Nombre del compañero]
- **Integrantes presentes:** [Nombre].
- **Commit(s):** `[hash]` — [mensaje].
- **Qué se hizo:** Organicé la estructura inicial del repositorio según la rúbrica: `analysis/`, `data/`, `src/` (con `sockets/`, `grpc/` y `proto/`) y `docs/sections/` para el informe en LaTeX. También repartí el trabajo entre los integrantes.
- **Problema encontrado:** Git no registra carpetas vacías, así que la estructura no se veía en GitHub.
- **Solución y comprobación:** Agregué archivos `.gitkeep` en las carpetas vacías y verifiqué en GitHub que aparecieran.
- **Tiempo dedicado:** 2 h 12 min.

### 2026-11-17 · Mera Jumbo Allison
- **Integrantes presentes:** Mera Jumbo Allison.
- **Commit(s):** `a3d0825` — Configura dependencias del proyecto y agrega gitignore.
- **Qué se hizo:** Cloné el repositorio, creé el entorno virtual con Python 3.14.0 e instalé grpcio, grpcio-tools, protobuf, pandas y matplotlib. Fijé sus versiones exactas en `requirements.txt` y agregué `.gitignore` para no subir `.venv/` ni `__pycache__/`.
- **Problema encontrado:** El `git push` falló con error 403 porque Windows tenía guardada la sesión de otra cuenta de GitHub sin permisos en el repo.
- **Solución y comprobación:** Borré la credencial de GitHub en el Administrador de credenciales de Windows, revisé con `git log` que el commit tuviera mi correo y volví a hacer push iniciando sesión con `ameraj2-bit`. El push terminó con `main -> main`.
- **Tiempo dedicado:** [ajústalo, más o menos 45 min].
