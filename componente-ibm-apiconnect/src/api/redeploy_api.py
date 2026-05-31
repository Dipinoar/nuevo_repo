import os
import sys

import yaml

from common.RepoMetadata import build_subscription_payload
from common.RepoMetadata import get_product_identity
from common.RepoMetadata import resolve_catalog_context
from common.Validation import check_environment
from common.Validation import validate_required_fields
from vars.Apicrest import Apicrequest
from vars.Awsrest import Awsrequest
from vars.Functions import Processfunc


def build_runtime_context(environment):
    with open("config_files/api/varenvironment.yml", "r") as varyaml:
        connvar = yaml.safe_load(varyaml)

    product_identity = get_product_identity()
    organizacion, catalogo = resolve_catalog_context(
        os.environ.get("ORGANIZACION") or os.environ.get("Organizacion"),
        os.environ.get("CATALOGO") or os.environ.get("Catalogo"),
    )
    variable_map = {
        "environment": environment,
        "organizacion": organizacion,
        "catalogo": catalogo,
        "nameProduct": product_identity["nameProduct"],
        "versionProduct": product_identity["versionProduct"],
        "nameProductyaml": product_identity["nameProductyaml"],
        "urlmanager": connvar["environment"][environment]["urlmanager"],
        "realm": connvar["environment"][environment]["realm"],
        "aws_da": connvar["environment"][environment]["aws_da"],
        "aws_dr": connvar["environment"][environment]["aws_dr"],
        "region": connvar["environment"][environment]["region"],
        "jfPath": connvar["environment"][environment].get("jf-repo", ""),
    }
    validate_required_fields(
        variable_map,
        ["environment", "organizacion", "catalogo", "nameProduct", "versionProduct", "urlmanager", "realm"],
    )
    return connvar, variable_map, product_identity["path"]


def main():
    environment = os.environ.get("TARGET_BRANCH") or os.environ.get("envi") or "development"
    check_environment(environment)

    connvar, vars_deploy, product_file = build_runtime_context(environment)
    process = Processfunc()
    vars_subs = build_subscription_payload(environment, product_file)

    secrets = Awsrequest()
    apirqs = Apicrequest(vars_deploy)
    login_api = secrets.getSecret(
        connvar["environment"]["production"]["aws_da"],
        connvar["environment"]["production"]["aws_dr"],
        "usr_apiconnectv10pipeline",
    )
    apirqs.getToken(login_api)
    process.replaceConfigFiles(environment, ".", vars_deploy)
    subs_list_catalog = apirqs.getSubscriptionByCatalog()
    old_version = {"name": vars_deploy["nameProduct"], "version": vars_deploy["versionProduct"]}
    list_old_subs = process.subsFromOldVersion(subs_list_catalog, old_version, environment)
    list_subs_merge = process.combineSubscription(vars_subs, list_old_subs, environment)
    print("Buscando para eliminar el Producto a Reinstalar...")
    apirqs.deleteProduct(vars_deploy["nameProduct"], vars_deploy["versionProduct"])
    deploy_result = apirqs.ejecutar_comando_api(login_api)
    if deploy_result != 0:
        print("Existe un error al desplegar")
        sys.exit(1)

    if list_subs_merge is None:
        print("No existen subscripciones")
        return

    print("Suscribiendo a las siguientes Aplicaciones")
    for item in list_subs_merge:
        print(item)
        apirqs.createSubscription(item)


if __name__ == "__main__":
    main()