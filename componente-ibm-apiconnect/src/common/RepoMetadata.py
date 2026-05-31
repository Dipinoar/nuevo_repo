import glob
import os

import yaml


def find_product_yaml(search_dir="."):
    patterns = ("*.yaml", "*.yml")
    for pattern in patterns:
        for candidate in sorted(glob.glob(os.path.join(search_dir, pattern))):
            with open(candidate, "r") as product_file:
                content = yaml.safe_load(product_file)
            if isinstance(content, dict) and "product" in content:
                return candidate
    raise FileNotFoundError("No se encontro un product yaml en el repositorio")


def load_product_yaml(product_file=None):
    product_file = product_file or find_product_yaml(".")
    with open(product_file, "r") as descriptor:
        content = yaml.safe_load(descriptor) or {}
    return content, product_file


def parse_catalog_context(project_namespace=None):
    namespace = project_namespace or os.environ.get("CI_PROJECT_NAMESPACE") or ""
    parts = [segment for segment in namespace.split("/") if segment]
    if len(parts) < 2:
        return None, None
    return parts[-2], parts[-1]


def resolve_catalog_context(organizacion=None, catalogo=None):
    namespace_org, namespace_catalog = parse_catalog_context()
    return organizacion or namespace_org, catalogo or namespace_catalog


def normalize_subscription_entries(raw_config):
    if raw_config is None:
        return []

    if isinstance(raw_config, dict) and isinstance(raw_config.get("subscriptions"), list):
        raw_entries = raw_config["subscriptions"]
    elif isinstance(raw_config, list):
        raw_entries = raw_config
    else:
        raw_entries = [raw_config]

    entries = []
    for entry in raw_entries:
        if not isinstance(entry, dict):
            continue
        if entry.get("enabled") is False:
            continue
        entries.append({
            "consumerorg": entry.get("consumerorg") or entry.get("consumerOrg"),
            "application": entry.get("application") or entry.get("app"),
            "plan": entry.get("plan") or "default-plan",
        })
    return entries


def get_environment_consumer_config(environment, product_file=None):
    product_data, _ = load_product_yaml(product_file)
    x_idp = product_data.get("x-idp") or {}
    consumer_config = x_idp.get("consumer") or {}
    if not isinstance(consumer_config, dict):
        return []

    raw_config = consumer_config.get(environment)
    if raw_config is None:
        raw_config = consumer_config.get("default")
    return normalize_subscription_entries(raw_config)


def get_all_environment_consumer_config(product_file=None):
    product_data, _ = load_product_yaml(product_file)
    x_idp = product_data.get("x-idp") or {}
    consumer_config = x_idp.get("consumer") or {}
    if not isinstance(consumer_config, dict):
        return {}

    environment_entries = {}
    for environment, raw_config in consumer_config.items():
        if environment == "default":
            continue
        entries = normalize_subscription_entries(raw_config)
        if entries:
            environment_entries[environment] = entries
    return environment_entries


def build_subscription_payload(environment, product_file=None):
    entries = get_environment_consumer_config(environment, product_file)
    if not entries:
        return None
    return {"subscription": {"environment": {environment: entries}}}


def build_all_subscription_payloads(product_file=None):
    environment_entries = get_all_environment_consumer_config(product_file)
    if not environment_entries:
        return None
    return {"subscription": {"environment": environment_entries}}


def get_consumer_defaults(environment, product_file=None):
    entries = get_environment_consumer_config(environment, product_file)
    if not entries:
        return {}
    first_entry = entries[0]
    return {
        "consumerOrg": first_entry.get("consumerorg"),
        "application": first_entry.get("application"),
        "plan": first_entry.get("plan") or "default-plan",
    }


def get_product_identity(product_file=None):
    product_data, product_file = load_product_yaml(product_file)
    info = product_data.get("info") or {}
    return {
        "path": product_file,
        "nameProduct": info.get("name"),
        "versionProduct": info.get("version"),
        "nameProductyaml": os.path.basename(product_file),
        "plans": list((product_data.get("plans") or {}).keys()),
    }