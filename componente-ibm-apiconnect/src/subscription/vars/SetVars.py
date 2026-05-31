from vars.Formatted import Formatfunc
from vars.Functions import Processfunc
from common.RepoMetadata import get_consumer_defaults
from common.RepoMetadata import get_product_identity
from common.RepoMetadata import resolve_catalog_context
from common.Validation import check_environment
import os
import yaml
import json
import re
import glob

def set_vars():

    filevars = Formatfunc()
    process= Processfunc()
    env_vars = os.environ
    #for var in env_vars:
        #print(f"{var}: {env_vars[var]}")
    environment = os.environ.get('TARGET_BRANCH') or os.environ.get('envi') or "development"
    check_environment(environment)
    projectPath = os.environ.get('CI_PROJECT_PATH')
    product_identity = get_product_identity()
    consumer_defaults = get_consumer_defaults(environment, product_identity['path'])
    nombreProducto = os.environ.get('PRODUCT_NAME') or product_identity['nameProduct']
    versionProducto = os.environ.get('PRODUCT_VERSION') or product_identity['versionProduct']
    organizacion, catalogo = resolve_catalog_context(
        os.environ.get('ORGANIZACION') or os.environ.get('Organizacion'),
        os.environ.get('CATALOGO') or os.environ.get('Catalogo')
    )
    # Split CI_PROJECT_PATH into base path and project path
    pathParts = projectPath.split('/') if projectPath else []
    ciCustomBasePath = '/'.join(pathParts[:2]) if len(pathParts) >= 2 else ''
    ciCustomProjectPath = '/'.join(pathParts[2:]) if len(pathParts) > 2 else ''
    directorio = '.'
    with open('config_files/subscription/varenvironment.yml', 'r') as varyaml:
        connvar = yaml.safe_load(varyaml)
    
    variableMap = {
        'environment': environment,
        'organizacion': organizacion,
        'catalogo': catalogo,
        'nameProduct': nombreProducto,
        'versionProduct': versionProducto,
        'consumerOrg': os.environ.get('CONSUMER_ORG') or consumer_defaults.get('consumerOrg'),
        'application': os.environ.get('APPLICATION') or consumer_defaults.get('application'),
        'plan': os.environ.get('PLAN') or consumer_defaults.get('plan') or 'default-plan',
        #'nameProductyaml': namefile,
        'urlmanager': connvar['environment'][environment]['urlmanager'],
        'realm': connvar['environment'][environment]['realm'],
        'aws_da': connvar['environment'][environment]['aws_da'],
        'aws_dr': connvar['environment'][environment]['aws_dr'],
        'region': connvar['environment'][environment]['region'],
        #'plans': plansresult,
        'projectPath': projectPath,
        'ciCustomBasePath': ciCustomBasePath,
        'ciCustomProjectPath': ciCustomProjectPath
    }

    print(json.dumps(variableMap, indent=4))
    filevars.formater(variableMap,'detail_vars.yaml')
    
    # Create .env file
    with open('build_vars.env', 'w') as env_file:
        for key, value in variableMap.items():
            env_file.write(f"{key.upper()}={value}\n")
