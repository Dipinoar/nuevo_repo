from vars.Formatted import Formatfunc
from vars.Functions import Processfunc
import os
import yaml
import json
import re
import glob

def main():

    filevars = Formatfunc()
    process= Processfunc()
    env_vars = os.environ
    #for var in env_vars:
        #print(f"{var}: {env_vars[var]}")
    environment= os.environ.get('TARGET_BRANCH')
    pathGit = os.environ.get('CI_PROJECT_NAMESPACE')
    directorio = '.'
    with open('CICD/resources/varenvironment.yaml', 'r') as varyaml:
    #with open('../resources/varenvironment.yaml', 'r') as varyaml:
        connvar = yaml.safe_load(varyaml)
        #print(connvar)
    #pathGit = "microservicios-api/ecosistema-apis/outer/sandbox"
    patron = r"/([^/]+)/([^/]+)$"
    resultado = re.search(patron, pathGit)
    organizacion=resultado.group(1)
    catalogo=resultado.group(2)
    archivoyaml=process.findProductYaml(directorio)
    print(archivoyaml)
    nombreProducto,versionProducto,namefile,plansresult = process.validateProductYaml(archivoyaml)
    variableMap = {
        'environment': environment,
        'organizacion': organizacion,
        'catalogo': catalogo,
        'nameProduct': nombreProducto,
        'versionProduct': versionProducto,
        'nameProductyaml': namefile,
        'urlmanager': connvar['environment'][environment]['urlmanager'],
        'realm': connvar['environment'][environment]['realm'],
        'aws_da': connvar['environment'][environment]['aws_da'],
        'aws_dr': connvar['environment'][environment]['aws_dr'],
        'region': connvar['environment'][environment]['region'],
        'jfPath': connvar['environment'][environment]['jf-repo'],
        'plans': plansresult
    }

    #print(json.dumps(variableMap, indent=4))
    filevars.formater(variableMap,'detail_vars.yaml')
if __name__ == "__main__":
    main() 