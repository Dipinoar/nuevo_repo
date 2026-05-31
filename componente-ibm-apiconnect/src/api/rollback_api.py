import os
import sys
import time

import yaml

from common.RepoMetadata import build_subscription_payload
from common.RepoMetadata import get_product_identity
from common.RepoMetadata import resolve_catalog_context
from common.Validation import check_environment
from common.Validation import validate_required_fields
from vars.Apicrest import Apicrequest
from vars.Awsrest import Awsrequest
from vars.Functions import Processfunc


def load_yaml_optional(file_path):
    try:
        with open(file_path, "r") as yaml_file:
            return yaml.safe_load(yaml_file)
    except FileNotFoundError:
        print(f"Info: No se encontro el archivo {file_path}")
        return None


def build_runtime_context(environment):
    with open("config_files/api/varenvironment.yml", "r") as varyaml:
        connvar = yaml.safe_load(varyaml)

    process = Processfunc()
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
    return connvar, variable_map, process, product_identity["path"]


def main():
    environment = os.environ.get("TARGET_BRANCH") or os.environ.get("envi") or "development"
    check_environment(environment)

    connvar, vars_deploy, process, product_file = build_runtime_context(environment)
    vars_subs = load_yaml_optional("subsOldVersion.yaml") or build_subscription_payload(environment, product_file)
    name_actual = vars_deploy["nameProduct"]
    version_actual = vars_deploy["versionProduct"]

    secrets = Awsrequest()
    apirqs = Apicrequest(vars_deploy)

    login_api = secrets.getSecret(
        connvar["environment"]["production"]["aws_da"],
        connvar["environment"]["production"]["aws_dr"],
        "usr_apiconnectv10pipeline",
    )
    apirqs.getToken(login_api)
    list_version_product = apirqs.getListProduct()
    size_list_version_product = len(list_version_product["results"])
    sort_version = sorted(
        list_version_product["results"],
        key=lambda x: tuple(map(int, x["version"].split("."))),
        reverse=True,
    )
    filter_version = process.filterVersionList(sort_version, vars_deploy)

    if len(filter_version) == 0:
        print("no existen registros para la busqueda solicitada")
        sys.exit(1)
    if filter_version[0]["name"] == name_actual and filter_version[0]["version"] != version_actual:
        print(f"No es posible reversar la version indicada {version_actual}")
        for item in filter_version:
            print(f"Nombre : [{item['name']}], Version [{item['version']}]")
        sys.exit(1)
    if size_list_version_product == 1:
        print(
            f"Este es el unico producto {name_actual} registrado con la version {version_actual}, el producto sera eliminado"
        )
        apirqs.updateProductStatus(name_actual, version_actual, {"state": "retired"})
        apirqs.deleteProduct(name_actual, version_actual)
        return

    if len(filter_version) == 1 and filter_version[0]["version"] == version_actual:
        print(f"Este es el unico producto registrado {version_actual}, esta version sera eliminada")
        print(f"Reversa a la version: {sort_version[1]['version']}")
        list_subs_merge = process.combineSubscription(vars_subs, None, environment)
        apirqs.updateProductStatus(name_actual, sort_version[1]["version"], {"state": "published"})
        print("Suscribiendo a las siguientes Aplicaciones")
        time.sleep(20)
        apirqs.updateProductStatus(name_actual, version_actual, {"state": "retired"})
        apirqs.deleteProduct(name_actual, version_actual)
        return

    print(f"Reversa a la version: {filter_version[1]['version']}")
    list_subs_merge = process.combineSubscription(vars_subs, None, environment)
    apirqs.updateProductStatus(name_actual, filter_version[1]["version"], {"state": "staged"})
    apirqs.updateProductStatus(
        name_actual,
        filter_version[1]["version"],
        {
            "visibility": {
                "view": {"enabled": "true", "type": "public", "org_urls": [], "group_urls": []},
                "subscribe": {"enabled": "true", "type": "authenticated", "org_urls": [], "group_urls": []},
            },
            "state": "published",
        },
    )
    time.sleep(10)
    print("Suscribiendo a las siguientes Aplicaciones")
    if list_subs_merge is not None:
        for item in list_subs_merge:
            print(item)
            apirqs.createSubscription(item, name_actual, filter_version[1]["version"])
    apirqs.updateProductStatus(name_actual, version_actual, {"state": "retired"})
    apirqs.deleteProduct(name_actual, version_actual)


if __name__ == "__main__":
    main()
