# Guía de Configuración Local - cl-android-superapp

## Requisitos previos

- macOS con Homebrew
- Java 21 (Temurin)
- Android Studio
- Acceso al GitLab corporativo (gitlab.itauchile.cl)

## Tokens necesarios

Los siguientes tokens son de solo lectura (descarga de dependencias y wrapper):

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `ANDROID_MAVEN_PULL_USER` | `GITLAB_MAVEN_PULL_TOKEN` | Username del Deploy Token para Maven |
| `ANDROID_MAVEN_PULL_USER_TOKEN` | `gldt-Qxhy4zn_GHimVMvMfQsP` | Password del Deploy Token para Maven |
| `ANDROID_ARTIFACT_PULL_USER` | `GITLAB_ANDROID_PULL_TOKEN` | Username del Deploy Token para Artifacts/Wrapper |
| `ANDROID_ARTIFACT_PULL_USER_TOKEN` | `gldt-tyNiKNvBucEioxLsN6Nc` | Password del Deploy Token para Artifacts/Wrapper |
| `TOKEN_GITLAB` | `GITLAB_TOKEN o 57mjxTWZHup2ikzuAsrb` | Token para repositorio Maven del grupo latam |

## Paso 1: Configurar variables de entorno

Agregar al final de `~/.zshrc` (o `~/.bash_profile` si usas bash):

```bash
# ====== JAVA ======
export JAVA_HOME=/Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home

# ====== GITLAB - Maven (dependencias del proyecto) ======
export ANDROID_MAVEN_PULL_USER="GITLAB_MAVEN_PULL_TOKEN"
export ANDROID_MAVEN_PULL_USER_TOKEN="gldt-Qxhy4zn_GHimVMvMfQsP"

# ====== GITLAB - Artifacts/Wrapper (descarga de Gradle) ======
export ANDROID_ARTIFACT_PULL_USER="GITLAB_ANDROID_PULL_TOKEN"
export ANDROID_ARTIFACT_PULL_USER_TOKEN="gldt-tyNiKNvBucEioxLsN6Nc"

# ====== GITLAB - Grupo latam (repositorio Maven del grupo) ======
export GITLAB_TOKEN="57mjxTWZHup2ikzuAsrb"
export TOKEN_GITLAB=$GITLAB_TOKEN

# ====== GRADLE WRAPPER AUTH ======
# Esto permite que ./gradlew descargue Gradle desde GitLab
export JAVA_TOOL_OPTIONS="-Dgradle.wrapperUser=$ANDROID_ARTIFACT_PULL_USER -Dgradle.wrapperPassword=$ANDROID_ARTIFACT_PULL_USER_TOKEN"

# ====== ANDROID SDK ======
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/tools

# ====== BUILD CONFIG ======
export VERSION_NAME="7.0.0"
export VERSION_CODE="700"
export PIPELINE_ID="000000"
export EXEMPT_RUT_STORE="99000001"

# ====== FACETEC ======
export FACETEC_PUBLIC_ENC="LS0tLS1CRUdJTiBQVUJMSUMgS0VZLS0tLS0KTUlJQklqQU5CZ2txaGtpRzl3MEJBUUVGQUFPQ0FROEFNSUlCQ2dLQ0FRRUE1UHhaM0RMait6UDZUNkhGZ3p6awpNNzdMZHpQM2ZvakJvTGFzdzdFZnp2TE1uSk5VbHlSYjVtOGU1UXl5SnhJK3dSanNBTEh2RmdMekd3eE04ZWh6CkRxcUJaZWQrZjR3MzNHZ1FYRlpPUzRBT3Z5UGJBTGdDWW9MZWhpZ0xBYmJDTlRrZVk1UkRjbW1TSS9zYnArczYKbUFpQUtLdkNkSXFlMTdibHRaL3JmRW9MM2dQS0VmTFhlTjU0OUxUajNYQnAwaHZHNGxvUTZlQzFFMXRSelNrZgpHSkQ0R0lWdlIrajEyZ1hBYWZ0ajNhaGZZeGlvQkg3RjdIUXh6bVdrd0R5bjNicVU1NGVhaUI3ZjBmdHNQcFdNCmNlVWFxa0wyRFpVdmdOMGVmRUpqbld5NXkxL0drcTVHR1dDUk9JOVhHL1N3WEozMEJiVlVlaFRiVmNENzArWkYKOFFJREFRQUIKLS0tLS1FTkQgUFVCTElDIEtFWS0tLS0t"

# ====== DEXGUARD ======
export DEXGUARD_LICENSE="$HOME/ItauSuperApp/dexguard/dexguard-license.txt"

# ====== SIGNING - Debug/Development ======
# La keystore de debug está dentro del proyecto en tools/debug-keystore/
# Ajustar la ruta al directorio donde clonaste cl-android-superapp
export KEY_ALIAS="itau_debug"
export KEY_PASSWORD="debugSuperApp"
export KEY_STORE_PASSWORD="debugSuperApp"
export KEY_STORE_PATH="$HOME/<ruta-al-proyecto>/cl-android-superapp/tools/debug-keystore/itau_debug.keystore"
```

Luego recargar el terminal:

```bash
source ~/.zshrc
```

## Paso 2: Limpiar cache del wrapper (si ya falló antes)

```bash
rm -rf ~/.gradle/wrapper/dists/gradle-8.8-all
```

## Paso 3: Verificar la configuración

```bash
# Verificar variables de entorno
echo "ANDROID_MAVEN_PULL_USER: $ANDROID_MAVEN_PULL_USER"
echo "ANDROID_ARTIFACT_PULL_USER: $ANDROID_ARTIFACT_PULL_USER"
echo "JAVA_TOOL_OPTIONS: $JAVA_TOOL_OPTIONS"
echo "JAVA_HOME: $JAVA_HOME"

# Verificar Java
java -version
```

## Paso 4: Compilar el proyecto

Desde la raíz del proyecto `cl-android-superapp`:

```bash
# Detener daemons previos
./gradlew --stop

# Verificar que descarga el wrapper y resuelve dependencias
./gradlew --no-daemon tasks

# Listar proyectos
./gradlew projects

# Verificar dependencias de app
./gradlew :app:dependencies

# Build completo (primera vez tarda ~10-15 min)
./gradlew build --refresh-dependencies
```

## Troubleshooting

### Error 401 al descargar Gradle wrapper

1. Verificar que `JAVA_TOOL_OPTIONS` está seteado:
   ```bash
   echo $JAVA_TOOL_OPTIONS
   ```
   Debe mostrar: `-Dgradle.wrapperUser=... -Dgradle.wrapperPassword=...`

2. Limpiar cache y reintentar:
   ```bash
   rm -rf ~/.gradle/wrapper/dists/gradle-8.8-all
   ./gradlew --version
   ```

3. Probar descarga manual para validar el token:
   ```bash
   curl -u "GITLAB_ANDROID_PULL_TOKEN:gldt-tyNiKNvBucEioxLsN6Nc" \
     "http://gitlab.itauchile.cl/api/v4/projects/12754/packages/generic/gradle/8.8/gradle-8.8-all.zip" \
     -o /dev/null -w "%{http_code}\n"
   ```
   Si da `200`, el token es correcto. Si da `401`, el token expiró o es incorrecto.

### Error "Could not resolve dependencies"

Verificar que `ANDROID_MAVEN_PULL_USER` y `ANDROID_MAVEN_PULL_USER_TOKEN` están seteados:
```bash
echo $ANDROID_MAVEN_PULL_USER
echo $ANDROID_MAVEN_PULL_USER_TOKEN
```

## Resumen de archivos de configuración

| Archivo | Qué configura |
|---------|---------------|
| `~/.zshrc` | Variables de entorno (tokens, JAVA_HOME, JAVA_TOOL_OPTIONS) |
| `<proyecto>/gradle.properties` | Config del proyecto (no modificar) |
| `<proyecto>/gradle/wrapper/gradle-wrapper.properties` | URL del wrapper (no modificar) |
