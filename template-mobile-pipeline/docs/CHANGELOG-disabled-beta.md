# Changelog: Beta deshabilitada temporalmente en .mobile-pipeline.yml

**Fecha:** 2026-06-02  
**Motivo:** La comunidad requiere volver al flujo anterior (versionado semántico en pre-merge, sin beta).

---

## Cambios realizados (para revertir luego)

### 1. Job `3.1 Calculate Beta Version` — COMENTADO
- **Qué hacía:** Calculaba versión beta incremental (`XbN`) en pre-merge feature→dev.
- **Efecto al comentar:** La versión en pre-merge vuelve a ser la semántica de Simulate Semantic Release (ej: `1.7.0-development`).
- **Para reactivar:** Descomentar el bloque completo del job `3.1` y restaurar los `needs` en los jobs que lo referencian.

### 2. Job `3.2 Simulate Semantic Release` — MODIFICADO
- **Qué cambió:** Antes exportaba `SEMANTIC_VERSION` a `.semantic_version_env` (para no pisar la beta). Ahora vuelve a exportar `APP_VERSION` a `.app_version_env`.
- **Qué se removió:** `needs: 3.1 Calculate Beta Version` (ya no existe como job activo).
- **Para revertir:**
  - Restaurar `needs: - job: 3.1 Calculate Beta Version optional: true`
  - Cambiar el script para exportar `SEMANTIC_VERSION` a `.semantic_version_env` en vez de `APP_VERSION` a `.app_version_env`
  - Cambiar artifacts a `dotenv: .semantic_version_env`

### 3. Job `5.1 Build and Upload` — rules MODIFICADAS
- **Qué se comentó:** `- !reference [.rules_commit_development, rules]`
- **Efecto:** El build ya no corre en push a development (post-merge). Solo corre en pre-merge (MRs).
- **Para reactivar:** Descomentar la línea de rules_commit_development.
- **También se comentó en needs:** `- job: 3.1 Calculate Beta Version optional: true`

### 4. Job `7.1 Verify Package Registry` — rules MODIFICADAS
- **Qué se comentó:** `rules_commit_development`, `rules_commit_quality`, `rules_commit_production`
- **Efecto:** El verify solo corre en MRs, no en push a ramas protegidas.
- **Para reactivar:** Descomentar las 3 líneas de rules_commit_*.
- **También se comentó en needs:** `- job: 3.1 Calculate Beta Version optional: true`

### 5. Job `8.1 Comment Summary` — needs MODIFICADO
- **Qué se comentó:** `- job: 3.1 Calculate Beta Version optional: true`
- **Para reactivar:** Descomentar.

---

## Archivos afectados
- `template-mobile-pipeline/.mobile-pipeline.yml`

## Búsqueda rápida
Buscar `[DISABLED-BETA]` en el archivo para encontrar todos los puntos comentados.

---

## Para reactivar el flujo beta completo:
1. Descomentar `3.1 Calculate Beta Version` completo
2. En `3.2 Simulate Semantic Release`: restaurar needs de 3.1, cambiar export a `SEMANTIC_VERSION`/`.semantic_version_env`
3. Descomentar `rules_commit_development` en `5.1 Build and Upload`
4. Descomentar `rules_commit_*` en `7.1 Verify Package Registry`
5. Descomentar needs de `3.1` en jobs 5.1, 7.1, 8.1

### 6. Anchor `.build_and_publish_sequential` — no-overwrite COMENTADO
- **Archivo:** `files/PJ/anchors/build_and_publish_sequential.yml`
- **Qué se comentó:** La lógica de `exit 1` cuando el artefacto ya existe.
- **Efecto:** Vuelve al comportamiento anterior de sobreescribir si ya existe.
- **Para reactivar:** Descomentar el bloque `if [[ "$HTTP" == "200" ]]; then exit 1; fi` y eliminar el bloque de "overwriting" que lo reemplaza.
- **Marcador:** `[DISABLED-BETA]`
