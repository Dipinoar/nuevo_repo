# Template Mobile Pipeline

Repositorio centralizado de **pipelines GitLab CI** para aplicaciones móviles.

---

## 📂 Estructura

```
├── .mobile-superapp-android.yml        # Pipeline SuperApp Android (PF)
├── .mobile-pipeline.yml                # Pipeline Android PJ Modules/Library
├── .mobile-pipeline-app.yml            # Pipeline Android PJ App
├── .mobile-android-itau-bom.yml        # Pipeline Android Itaú BOM
├── .mobile-android-native-bom.yml      # Pipeline Android Native BOM
├── ci/
│   ├── cacerts                         # Certificados CA para conexiones internas
│   ├── cacerts_backup_250326           # Backup de certificados
│   └── template-config.yaml           # Template de ci/config.yaml para proyectos
├── docs/
│   ├── superapp-android.md             # Doc: SuperApp Android (PF)
│   ├── android-pj-app.md              # Doc: Android PJ App
│   ├── android-pj-modules.md          # Doc: Android PJ Modules/Library
│   ├── android-itau-bom.md            # Doc: Android Itaú BOM
│   ├── android-native-bom.md          # Doc: Android Native BOM
│   └── configuracion-local-cl-android-superapp.md
├── files/
│   ├── shared/                         # Anchors compartidos PJ + PF
│   │   ├── calculate_version.yml       # Cálculo de beta y versionado
│   │   ├── check_rebase.yml            # Validación de rebase y conflictos
│   │   ├── comment_summary.yml         # Comment summary (PF)
│   │   ├── package_registry.yml        # Helpers de Package Registry
│   │   ├── reusable_commands.yml       # Helpers: git auth, downloads, pip
│   │   └── rules_components.yml        # Reglas por tipo de MR/branch
│   ├── PF/
│   │   ├── anchors/                    # Anchors específicos SuperApp Android
│   │   ├── scripts/                    # Scripts Gradle/Veracode parametrizados
│   │   └── yamls/                      # Variables, workflow, includes
│   │       ├── .mobile-superapp-android-include.yml
│   │       ├── .mobile-superapp-android-variables.yml
│   │       └── .mobile-superapp-android-workflow.yml
│   ├── PJ/
│   │   ├── anchors/                    # Anchors específicos Android PJ
│   │   ├── scripts/                    # Scripts Python
│   │   └── yamls/                      # Variables, workflow, includes
│   │       ├── .mobile-pipeline-include.yml          # Include para App
│   │       ├── .mobile-pipeline-modules-include.yml  # Include para Modules
│   │       ├── .mobile-pipeline-variables.yml
│   │       └── .mobile-pipeline-workflow.yml
│   └── semantic-versioning/
│       ├── .releaserc.yml              # Releases reales (push a development)
│       ├── .deploytestrc.yml           # Simulación de release (dry-run en MR)
│       └── semantic_release.sh         # Script de configuración semantic-release
└── templates/
    ├── mr_artifacts.md                 # Template de comentario MR (artefactos)
    └── summary.md                      # Template de version promotion summary
```

### Modularización

Cada pipeline se compone de archivos separados:

| Archivo | Propósito |
|---|---|
| `.mobile-superapp-android.yml` / `.mobile-pipeline.yml` | Solo jobs (stages, needs, rules, !reference) |
| `files/<PF\|PJ>/yamls/*-variables.yml` | Variables del pipeline |
| `files/<PF\|PJ>/yamls/*-workflow.yml` | Workflow rules |
| `files/<PF\|PJ>/yamls/*-include.yml` | Includes (shared, anchors, componentes) |
| `files/<PF\|PJ>/anchors/*.yml` | Anchors con lógica de scripts |
| `files/shared/*.yml` | Anchors compartidos entre PJ y PF |

Los scripts se descargan via `curl` individual por job, sin clonar el repositorio completo.

---

## 📖 Documentación por pipeline

| Pipeline | Archivo | Documentación |
|----------|---------|---------------|
| SuperApp Android (PF) | `.mobile-superapp-android.yml` | [docs/superapp-android.md](docs/superapp-android.md) |
| Android PJ App | `.mobile-pipeline-app.yml` | [docs/android-pj-app.md](docs/android-pj-app.md) |
| Android PJ Modules (Library) | `.mobile-pipeline.yml` | [docs/android-pj-modules.md](docs/android-pj-modules.md) |
| Android Itaú BOM | `.mobile-android-itau-bom.yml` | [docs/android-itau-bom.md](docs/android-itau-bom.md) |
| Android Native BOM | `.mobile-android-native-bom.yml` | [docs/android-native-bom.md](docs/android-native-bom.md) |

---

## 🔢 Versionado semántico

Configuración de `semantic-release` en `files/semantic-versioning/`:

- `.releaserc.yml` – Releases reales (push a development).
- `.deploytestrc.yml` – Simulación de release (dry-run en MR).
