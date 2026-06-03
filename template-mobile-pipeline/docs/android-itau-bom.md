# Pipeline Android – Itaú BOM (GitLab CI)

Pipeline GitLab CI para el proyecto `cl-android-itau-bom` (BOM de dependencias internas Itaú SDK). Gestiona compilación Gradle de módulos BOM por entorno (development, quality, production), versionado semántico, y publicación a Package Registry.

Archivo de entrada: `.mobile-android-itau-bom.yml`

---

## Flujo de ramas

```mermaid
flowchart LR
  F[feature/*<br>bugfix/*<br>subfeature/*] -->|MR| D[development]
  D -->|MR| Q[quality]
  Q -->|MR| P[production]

  style F fill:#4a9eff,color:#fff
  style D fill:#f5a623,color:#fff
  style Q fill:#7b61ff,color:#fff
  style P fill:#e74c3c,color:#fff
```

- Tags no disparan el pipeline.
- Push/merge en `development` también dispara el pipeline (sin contexto MR) para ejecutar Semantic Release real y publicar a Package Registry DEV.
- MR fuera de este flujo no matchean ninguna regla del workflow y el pipeline no se ejecuta.

Las reglas de ejecución por job se definen como anchors locales en el propio YAML y se complementan con `files/shared/rules_components.yml` vía `!reference`.

---

## Stages

```mermaid
flowchart LR
  S1[🛡️ compliance] --> S2[🧭 prepare_pipeline]
  S2 --> S3[🔢 calculate_version]
  S3 --> S4[🏗️ build]
  S4 --> S5[⬆️ upload]
  S5 --> S6[📝 summary]

  style S1 fill:#e74c3c,color:#fff
  style S2 fill:#f39c12,color:#fff
  style S3 fill:#3498db,color:#fff
  style S4 fill:#9b59b6,color:#fff
  style S5 fill:#1abc9c,color:#fff
  style S6 fill:#95a5a6,color:#fff
```

Los jobs usan `needs:` para formar un DAG y maximizar paralelismo.

---

## Includes

### Archivos locales (shared)

| Archivo | Propósito |
|---|---|
| `files/shared/calculate_version.yml` | Cálculo de versión y semantic release |
| `files/shared/check_rebase.yml` | Validación de rebase y conflictos |
| `files/shared/comment_summary.yml` | Comentario resumen en MR |
| `files/shared/package_registry.yml` | Helpers para verificar paquetes existentes |
| `files/shared/reusable_commands.yml` | Helpers: git auth, downloads, comentarios MR |
| `files/shared/rules_components.yml` | Anchors de reglas por tipo de MR/branch |

### Componente externo

`componente-package-registry/uploadv2@main` para uploads a Package Registry (3 instancias: DEV, QA, PROD).

---

## Stage: compliance

Gate obligatorio que valida políticas organizacionales antes de continuar.

### 1.1 Setting Compliance Variables
Genera `compliance.env` (dotenv) con:
- `COMPLIANCE_TECNOLOGY=mobile`
- `COMPLIANCE_LANGUAGES=$CI_PROJECT_REPOSITORY_LANGUAGES`
- `COMPLIANCE_PROJECT=$CI_PROJECT_PATH`

### 1.2 Validate Compliance
Dispara un pipeline downstream en `arq-devops-team/pipelines-gitlab/rule-validation` (rama `main`) con `strategy: depend`. El pipeline padre espera el resultado.

Variables enviadas al downstream:
- Las 3 de compliance (vía `forward: yaml_variables` + `pipeline_variables`).
- `REPO_ID=$CI_PROJECT_ID`

---

## Stage: prepare_pipeline

### 2.1 Check Rebase Status
Valida el estado del MR: cierra MR no válidos, verifica conflictos y si la rama source está desfasada respecto al target. Solo se ejecuta en MR feature/bugfix/subfeature → development.

### 2.2 Prepare Remote
Descarga e instala Python y PyYAML, lee `ci/config.yaml` del proyecto y genera `build.env` (dotenv) con variables de configuración:

- `GRADLE_VERSION` (default: `8.8`)
- `TEMURIN_VERSION` (default: `21`)
- `PIPELINE_ID`

Si `ci/config.yaml` no existe, el job falla con error explícito. Todos los jobs posteriores consumen `build.env` vía dotenv artifacts.

---

## Stage: calculate_version

```mermaid
flowchart TD
  subgraph "MR feature/bugfix/subfeature → development"
    A1[3.1 Simulate Semantic Release] --> A2[dry-run preview]
  end

  subgraph "Push/merge en development"
    B1[3.2 Semantic Release] --> B2[Crea tag real<br>o fallback a último tag]
  end

  subgraph "MR development → quality / quality → production"
    C1[3.3 Get Version from Tag] --> C2[Lee tag del commit]
  end

  A2 & B2 & C2 --> E[.app_version_env]

  style E fill:#3498db,color:#fff
```

| Job | Descripción | Cuándo |
|---|---|---|
| 3.1 Simulate Semantic Release | `semantic-release --dry-run` para previsualizar versión. Publica `APP_VERSION`, `VERSION_NAME` en `.app_version_env` | MR feature/bugfix/subfeature → development |
| 3.2 Semantic Release | Ejecuta semantic-release real (crea tag). Si no produce versión, hace fallback al último Git tag. Publica `.app_version_env` | Push/merge en development |
| 3.3 Get Version from Tag | Obtiene versión desde tag del commit actual. Publica `APP_VERSION` en `.app_version_env` | MR development → quality, quality → production |

---

## Stage: build

Cada entorno tiene su propio job de build que ejecuta un módulo Gradle específico del proyecto BOM. Los tres jobs comparten la misma estructura:

1. Cargan `build.env` y `.app_version_env`
2. Configuran Java Temurin y Gradle según versiones de `ci/config.yaml`
3. Ejecutan `./gradlew :bom-{entorno}:publishToMavenLocal`
4. Localizan el POM y Module Metadata generados en `~/.m2/repository/`
5. Copian los artefactos a `bom-output/` para el stage de upload

### 4.1 Gradle Build BOM DEV
- Módulo Gradle: `:bom-development:publishToMavenLocal`
- BOM version: `${APP_VERSION}` (sin sufijo en el POM, el sufijo lo agrega el upload)
- Reglas: MR feature/bugfix/subfeature → development, push en development

### 4.2 Gradle Build BOM QA
- Módulo Gradle: `:bom-quality:publishToMavenLocal`
- BOM version: `${APP_VERSION}-quality`
- Reglas: MR development → quality

### 4.3 Gradle Build BOM PROD
- Módulo Gradle: `:bom-production:publishToMavenLocal`
- BOM version: `${APP_VERSION}` (sin sufijo)
- Reglas: MR quality → production

### Artefactos de build

Cada job publica:
- `build.env` (dotenv)
- `.app_version_env`
- `bom-output/` (POM + Module Metadata)

Retención: 1 día.

---

## Stage: upload — Publicación a Package Registry

```mermaid
flowchart LR
  subgraph DEV
    BD[Gradle Build BOM DEV] --> CEP[Check Existing Package]
    CEP --> PR_D[📦 Package Registry<br>APP_VERSION-development]
  end

  subgraph QA
    BQ[Gradle Build BOM QA] --> CEP2[Check Existing Package]
    CEP2 --> PR_Q[📦 Package Registry<br>APP_VERSION-quality]
  end

  subgraph PROD
    BP[Gradle Build BOM PROD] --> CEP3[Check Existing Package]
    CEP3 --> PR_P[📦 Package Registry<br>APP_VERSION]
  end

  style PR_D fill:#1abc9c,color:#fff
  style PR_Q fill:#1abc9c,color:#fff
  style PR_P fill:#1abc9c,color:#fff
```

### 5.1 Check Existing Package
Verifica si el paquete ya existe en Package Registry antes de intentar el upload. Se ejecuta en los flujos DEV (post-merge), QA y PROD.

### 5.2 Upload BOM to Package Registry DEV

| Propiedad | Valor |
|---|---|
| Patrón de archivos | `*` (todo en `bom-output/`) |
| Nombre del paquete | `${BOM_ARTIFACT_ID}` (`core-itau-bom`) |
| Versión | `${APP_VERSION}${DEV_PREFIX}` → `X.Y.Z-development` |
| Reglas | Push/merge en development |

### 5.3 Upload BOM to Package Registry QA

| Propiedad | Valor |
|---|---|
| Patrón de archivos | `*` (todo en `bom-output/`) |
| Nombre del paquete | `${BOM_ARTIFACT_ID}` (`core-itau-bom`) |
| Versión | `${APP_VERSION}${QA_PREFIX}` → `X.Y.Z-quality` |
| Reglas | MR development → quality |

### 5.4 Upload BOM to Package Registry PROD

| Propiedad | Valor |
|---|---|
| Patrón de archivos | `*` (todo en `bom-output/`) |
| Nombre del paquete | `${BOM_ARTIFACT_ID}` (`core-itau-bom`) |
| Versión | `${APP_VERSION}` → `X.Y.Z` (sin sufijo) |
| Reglas | MR quality → production |

Todos usan `componente-package-registry/uploadv2@main` con `auth_method: custom_token` y `retry_max: 2`.

---

## Stage: summary

### 6.1 Comment Summary
Genera un comentario en el MR con:
- Pipeline ID y URL
- Tag de versión
- Lista de artefactos del Package Registry con URLs de descarga

Se ejecuta en todos los flujos (post-merge development, MR dev→quality, MR quality→prod).

---

## Variables y flags

### Variables BOM
| Variable | Valor | Descripción |
|---|---|---|
| `BOM_GROUP_ID` | `cl.itau` | Group ID Maven del BOM |
| `BOM_ARTIFACT_ID` | `core-itau-bom` | Artifact ID Maven del BOM |

### Prefijos de versión
| Variable | Valor |
|---|---|
| `DEV_PREFIX` | `-development` |
| `QA_PREFIX` | `-quality` |

La versión PROD no lleva sufijo.

### Imágenes
| Variable | Imagen |
|---|---|
| default | `runner-android:image-v3` |
| `$RUNNER_DEFAULT_IMAGE` | `runner-default-image:2.5.2-secure` |
| `$NODE_SECURE_IMAGE` | `runner-node:24.11.0-secure` |

Tags: `devsecops-common`.

---

## Artefactos

| Tipo | Archivo | Retención |
|---|---|---|
| Versionado | `.app_version_env` (dotenv) | 1 día |
| Build config | `build.env` (dotenv) | 1 día |
| BOM output | `bom-output/*.pom`, `bom-output/*.module` | 1 día |
| Compliance | `compliance.env` (dotenv) | — |

---

## Retry policy

Los jobs de build comparten una política de retry:

```yaml
retry:
  max: 2
  when:
    - script_failure
    - runner_system_failure
```

Los jobs de upload vía componente (`componente-package-registry/uploadv2`) usan `retry_max: 2` como input del componente.

Jobs con retry: 4.1 Gradle Build BOM DEV, 4.2 Gradle Build BOM QA, 4.3 Gradle Build BOM PROD, 5.2/5.3/5.4 uploads a Package Registry.

---

## Dependencias externas

### `ci/config.yaml` (proyecto consumidor)

El job 2.2 Prepare Remote espera que el repositorio `cl-android-itau-bom` contenga un archivo `ci/config.yaml` en su raíz. Este archivo se parsea con PyYAML y genera `build.env` con:

- `GRADLE_VERSION` — versión de Gradle a usar (default: `8.8`)
- `TEMURIN_VERSION` — versión de Java Temurin (default: `21`)
- `PIPELINE_ID` — ID del pipeline actual

Si `ci/config.yaml` no existe, el job falla con error explícito. Todos los jobs posteriores consumen `build.env` vía dotenv artifacts.

### Módulos Gradle del proyecto BOM

El proyecto `cl-android-itau-bom` contiene tres módulos Gradle, uno por entorno:

| Módulo | Entorno | Usado en |
|---|---|---|
| `bom-development` | DEV | 4.1 Gradle Build BOM DEV |
| `bom-quality` | QA | 4.2 Gradle Build BOM QA |
| `bom-production` | PROD | 4.3 Gradle Build BOM PROD |

Cada módulo define las dependencias internas Itaú SDK correspondientes a su entorno y genera un POM (Maven BOM) + Gradle Module Metadata al ejecutar `publishToMavenLocal`.

---

## Workflow rules (resumen)

El `workflow` del pipeline evalúa el evento y la combinación de ramas:

| Condición | Variables seteadas | Pipeline |
|---|---|---|
| MR feature/bugfix/subfeature → development | `ENVIRONMENT=development`, `PACKAGES_MAVEN_NAME_SUFFIX=${DEV_PREFIX}` | ✅ |
| Push/merge en development | `ENVIRONMENT=development`, `PACKAGES_MAVEN_NAME_SUFFIX=${DEV_PREFIX}` | ✅ |
| MR development → quality | `ENVIRONMENT=quality`, `PACKAGES_MAVEN_NAME_SUFFIX=${QA_PREFIX}` | ✅ |
| MR quality → production | `ENVIRONMENT=production`, `PACKAGES_MAVEN_NAME_SUFFIX=""` | ✅ |
| Cualquier otro caso | — | ❌ never |

---

## Reglas locales (anchors)

El pipeline define sus propios anchors de reglas además de los compartidos:

| Anchor | Condición |
|---|---|
| `.rules_mr_feature_bugfix_subfeature_to_development` | MR de feature/bugfix/subfeature → development |
| `.rules_commit_development` | Push directo en development |
| `.rules_mr_development_to_quality` | MR de development → quality |
| `.rules_mr_quality_to_production` | MR de quality → production |
| `.rules_commit_production` | Push directo en production (definido pero no usado actualmente) |

---

## Matriz de jobs por flujo

| Job | feature→dev | push dev | dev→quality | quality→prod |
|---|:---:|:---:|:---:|:---:|
| 1.1 Setting Compliance Variables | ✅ | ✅ | ✅ | ✅ |
| 1.2 Validate Compliance | ✅ | ✅ | ✅ | ✅ |
| 2.1 Check Rebase Status | ✅ | — | — | — |
| 2.2 Prepare Remote | ✅ | ✅ | ✅ | ✅ |
| 3.1 Simulate Semantic Release | ✅ | — | — | — |
| 3.2 Semantic Release | — | ✅ | — | — |
| 3.3 Get Version from Tag | — | — | ✅ | ✅ |
| 4.1 Gradle Build BOM DEV | ✅ | ✅ | — | — |
| 4.2 Gradle Build BOM QA | — | — | ✅ | — |
| 4.3 Gradle Build BOM PROD | — | — | — | ✅ |
| 5.1 Check Existing Package | — | ✅ | ✅ | ✅ |
| 5.2 Upload BOM to Package Registry DEV | — | ✅ | — | — |
| 5.3 Upload BOM to Package Registry QA | — | — | ✅ | — |
| 5.4 Upload BOM to Package Registry PROD | — | — | — | ✅ |
| 6.1 Comment Summary | — | ✅ | ✅ | ✅ |

> 3.2 Semantic Release solo corre en push/merge directo a `development` (no en MR). Check Rebase Status solo corre en MR feature/bugfix/subfeature → development.

---

## DAG (simplificado)

```mermaid
flowchart LR
  A[1.1 Setting Compliance Vars] --> B[1.2 Validate Compliance]
  B --> C[2.1 Check Rebase Status]
  B --> D[2.2 Prepare Remote]

  D --> E[3.1 Simulate Semantic Release]
  D --> F[3.2 Semantic Release]
  D --> G[3.3 Get Version from Tag]

  D & E & F --> H[4.1 Gradle Build BOM DEV]
  D & G --> I[4.2 Gradle Build BOM QA]
  D & G --> J[4.3 Gradle Build BOM PROD]

  H & F --> K[5.1 Check Existing Package]
  I --> K
  J --> K

  K & H & F --> L[5.2 Upload BOM PR DEV]
  K & I & G --> M[5.3 Upload BOM PR QA]
  K & J & G --> N[5.4 Upload BOM PR PROD]

  F & G & H & I & J & L & M & N --> O[6.1 Comment Summary]
```

---

## Diferencias clave con el pipeline SuperApp Android

| Aspecto | SuperApp Android | Itaú BOM |
|---|---|---|
| Tipo de artefacto | APKs (GMS/HMS) | Maven BOM (POM + Module Metadata) |
| Providers | Google (GMS) + Huawei (HMS) | N/A (no aplica) |
| Stage test | Detekt (análisis estático) | No tiene stage de test |
| Veracode | Sí (scan de seguridad pre-PROD) | No |
| Firebase | Upload a App Distribution (DEV/QA) | No |
| Google Play | Deploy a track interno (PROD) | No |
| Flujo unofficial | Sí (`unofficial/*` → production) | No |
| Módulos Gradle | Build parametrizado por scripts | Módulos por entorno (`bom-development`, `bom-quality`, `bom-production`) |
| Subfeature branches | No | Sí (`subfeature/*` → development) |
| Secrets (AWS) | Firebase token via STS assume-role | No |
