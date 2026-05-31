# IDP - APIConnect

Pipeline GitLab para orquestar componentes IBM API Connect del grupo IDP, alineado con el flujo git de referencia y separado entre automatizacion por ramas y jobs utilitarios disparados por variables.

## Flujo vigente

Automatizado:
- Merge request hacia `development`: ejecuta `compliance`, `HU Validation`, `validate_api` y `create_api` sobre `development`.
- Push hacia `quality`: ejecuta `create_api`, `veracode-devenv`, `HU Sync` y `leanix` sobre `quality`.
- Merge request hacia `production`: ejecuta `HU Validation` y `veracode-prd`.
- Push hacia `production`: ejecuta `create_api`, `HU Sync`, `leanix` y deja disponibles `rollback` y `redeploy` en `options`.

Automatizado por flag de commit o variable:
- `[consumer_flow]` o `AUTO_CREATE_CONSUMER_ORG=true` para crear consumer org.
- `[consumer_flow]` o `AUTO_CREATE_APP=true` para crear aplicacion.
- `[create_subscription]`, `[subscription_sync]` o `FORCE_CREATE_SUBSCRIPTION=true` para forzar la stage separada de suscripcion.

Manual por `Run pipeline` o `trigger`:
- `create_api`
- `create_consumer_org`
- `create_app`
- `create_subscription`
- `rollback`
- `redeploy`

Para las ejecuciones manuales se debe informar `ID_STAGE`.

## Flujo recomendado

1. Declarar la metadata de consumo en el `product-*.yaml` bajo `x-idp.consumer.<ambiente>`.
2. En un merge request hacia `development`, ejecutar `validate_api` y `create_api` con la suscripcion declarativa embebida.
3. Si el bootstrap requiere consumer org o app nuevas, agregar `[consumer_flow]` al commit para correr esas stages antes de `create_api`.
4. Promover hacia `quality` para repetir `create_api` en el ambiente promovido con el mismo descriptor versionado.
5. Promover hacia `production` para ejecutar el mismo `create_api` ya con regla de push a `production`.
6. Usar `create_subscription` solo como stage operativa o de resincronizacion puntual, y `rollback` o `redeploy` para contingencia.

`create_app` ya contempla la creacion de la consumer org si no existe, por lo que `create_consumer_org` queda como utilidad operativa o como bootstrap explicito por flag.

## Variables CI/CD

Variables tecnicas:
- `GITLAB_TOKEN`: token con permisos de lectura al proyecto de componentes para descargar scripts y archivos de configuracion.
- `COMPONENTS_REF`: opcional. Por defecto el pipeline usa `main`.
- `AUTO_CREATE_CONSUMER_ORG`: opcional. `true` para automatizar la stage sin depender del commit message.
- `AUTO_CREATE_APP`: opcional. `true` para automatizar la stage sin depender del commit message.
- `FORCE_CREATE_SUBSCRIPTION`: opcional. `true` para ejecutar la stage separada de suscripcion.

Variables de entrada para jobs manuales o para override explicito:
- `ID_STAGE`: `create_api`, `create_consumer_org`, `create_app`, `create_subscription`, `rollback` o `redeploy`.
- `envi`: `development`, `quality` o `production`. Por defecto `development`.
- `ORGANIZACION`
- `CATALOGO`
- `APPLICATION`
- `CONSUMER_ORG`
- `PRODUCT_NAME`
- `PRODUCT_VERSION`
- `PLAN`

Mapeo usado por los scripts actuales:
- `APPLICATION` se expone tambien como `Nombre`.
- `CONSUMER_ORG` se expone tambien como `Consumer_org`.
- `create_consumer_org` reutiliza `CONSUMER_ORG` como nombre de la consumer org.
- Si no se informan variables manuales, `create_consumer_org`, `create_app` y `create_subscription` intentan inferir `ORGANIZACION`, `CATALOGO`, `APPLICATION`, `CONSUMER_ORG`, `PRODUCT_NAME`, `PRODUCT_VERSION` y `PLAN` desde `CI_PROJECT_NAMESPACE` y el `product-*.yaml`.

## Descriptor repo-driven

El modelo de suscripcion queda versionado en el mismo `product-*.yaml` del repo API:

```yaml
x-idp:
  consumer:
    development:
      subscriptions:
        - consumerorg: benefits-clients
          application: benefits-clients
          plan: default-plan
    quality:
      subscriptions:
        - consumerorg: benefits-clients
          application: benefits-clients
          plan: default-plan
```

`validate_api` revisa ese bloque, valida que el plan exista en el producto y ahora tambien hace la validacion funcional previa contra APIC de la misma forma que el pipeline base, siempre que el ambiente tenga configuracion APIC disponible. `create_api` lo mezcla con las suscripciones heredadas de versiones anteriores.

## Validez de las stages

- `create_api` ya quedo alineada para `development`, `quality` y `production` a nivel de reglas del pipeline.
- `create_consumer_org` y `create_app` ya pueden automatizarse desde commit flags o variables de pipeline, y toman defaults desde el `product-*.yaml`.
- `create_subscription` ya toma el ambiente desde el pipeline, respeta el plan solicitado y puede reconstruir sus defaults desde el repositorio.
- `rollback` y `redeploy` ya existen como componentes equivalentes dentro de la stage `options`.
- `quality` ya tiene configuracion completa para `app`, `consumer_org` y `subscription`.

## Brechas abiertas

- `production` ya quedo considerado en la validacion comun y en la regla de despliegue, pero el despliegue real sigue pendiente hasta completar configuracion productiva en los componentes.
- La validacion funcional previa contra APIC depende de permisos AWS para asumir el rol que entrega `usr_apiconnectv10pipeline`.
- Si el nombre real de `consumerorg` o `application` no coincide con el ejemplo del `product-*.yaml`, debe ajustarse en ese mismo descriptor antes de ejecutar el bootstrap.
