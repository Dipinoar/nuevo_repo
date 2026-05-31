import os
import sys

import yaml

from common.RepoMetadata import build_all_subscription_payloads
from common.RepoMetadata import build_subscription_payload
from common.RepoMetadata import get_product_identity
from common.RepoMetadata import resolve_catalog_context
from common.Validation import check_environment
from common.Validation import validate_required_fields
from vars.Apicrest import Apicrequest
from vars.Awsrest import Awsrequest
from vars.Functions import Processfunc


def environment_is_configured(vars_envi, environment):
    env_config = vars_envi.get("environment", {}).get(environment, {})
    return bool(env_config.get("urlmanager")) and bool(env_config.get("realm"))


def main():
    environment = os.environ.get("TARGET_BRANCH") or os.environ.get("envi") or "development"
    check_environment(environment)

    process = Processfunc()
    product_file = process.findProductYaml(".")
    product_name, _, _, plans = process.validateProductYaml(product_file)
    valid_plans = set(plans.get("plans", []))
    all_declared_subscriptions = build_all_subscription_payloads(product_file)

    process.checkvisibility(".")
    process.checkDp(".")

    subscriptions = build_subscription_payload(environment, product_file)
    if subscriptions is None:
        print(f"[INFO] No se encontro configuracion x-idp para {environment} en el product yaml")
        return

    print(f"[INFO] Validando suscripciones declarativas para {product_name} en {environment}")
    for subscription in subscriptions["subscription"]["environment"][environment]:
        if not subscription.get("consumerorg"):
            raise ValueError("El bloque x-idp.consumer requiere consumerorg")
        if not subscription.get("application"):
            raise ValueError("El bloque x-idp.consumer requiere application")
        if valid_plans and subscription["plan"] not in valid_plans:
            raise ValueError(
                f"El plan '{subscription['plan']}' no existe en el product yaml para {environment}"
            )

    print(f"[OK] Se validaron {len(subscriptions['subscription']['environment'][environment])} suscripciones declarativas")

    # Validacion funcional previa (AWS/APIC) queda deshabilitada temporalmente.
    # Motivo: requiere permisos de AWS (AssumeRole) no disponibles en el entorno actual.
    # Se mantiene la logica comentada para reactivarla cuando esten listos los permisos.
    print("[INFO] Validacion funcional previa deshabilitada temporalmente por permisos AWS pendientes")
    return

    # if all_declared_subscriptions is None:
    #     return
    #
    # with open("config_files/api/varenvironment.yml", "r") as varyaml:
    #     vars_envi = yaml.safe_load(varyaml)
    #
    # organizacion, catalogo = resolve_catalog_context()
    # validate_required_fields(
    #     {"organizacion": organizacion, "catalogo": catalogo},
    #     ["organizacion", "catalogo"],
    # )
    #
    # if not environment_is_configured(vars_envi, environment):
    #     print(f"[INFO] El ambiente {environment} no tiene configuracion APIC completa para validacion remota previa")
    #     return
    #
    # product_identity = get_product_identity(product_file)
    # vars_deploy = {
    #     "organizacion": organizacion,
    #     "catalogo": catalogo,
    #     "nameProduct": product_identity["nameProduct"],
    #     "versionProduct": product_identity["versionProduct"],
    # }
    # secrets = Awsrequest()
    # login_api = secrets.getSecret(
    #     vars_envi["environment"]["production"]["aws_da"],
    #     vars_envi["environment"]["production"]["aws_dr"],
    #     "usr_apiconnectv10pipeline",
    # )
    #
    # validation_errors = 0
    # for declared_environment, declared_subscriptions in all_declared_subscriptions["subscription"]["environment"].items():
    #     if not environment_is_configured(vars_envi, declared_environment):
    #         print(
    #             f"[INFO] Se omite validacion funcional previa de {declared_environment} porque la configuracion APIC aun no esta completa"
    #         )
    #         continue
    #
    #     remote_payload = {"subscription": {"environment": {declared_environment: declared_subscriptions}}}
    #     validation_errors += process.get_subscriptions_and_print_results(
    #         login_api,
    #         dict(vars_deploy),
    #         declared_environment,
    #         remote_payload,
    #         vars_envi,
    #     )
    #
    # if validation_errors > 0:
    #     print("SE ENCONTRARON PROBLEMAS PARA VALIDAR LA SUSCRIPCION")
    #     sys.exit(1)


if __name__ == "__main__":
    main()