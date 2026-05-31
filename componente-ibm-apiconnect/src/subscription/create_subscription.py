import os
import sys
import yaml
#import packaging.version as pv
from vars.Formatted import Formatfunc
from vars.Functions import Processfunc
from vars.Apicrest import Apicrequest
from vars.Awsrest import Awsrequest
from vars.SetVars import set_vars
from common.Validation import validate_required_fields

def main():
    set_vars()
    # Configuración de variables produccion
    environment = "development"
    #path_varsEnvi='CICD/resources/varenvironment.yaml'
    path_varsEnvi='config_files/subscription/varenvironment.yml'
    path_varsDeploy='detail_vars.yaml'
    #path_varsSubs='configSubs.yaml'
    directorio_busqueda = "."
    # Carga de archivos YAML
    with open(path_varsEnvi, 'r') as varyaml:
        connvar = yaml.safe_load(varyaml)
    with open(path_varsDeploy, "r") as varsenvironmentyaml:
        varsDeploy = yaml.safe_load(varsenvironmentyaml)
    #with open(path_varsSubs, "r") as subsvars:
    #    varsSubs = yaml.safe_load(subsvars)
    secrets = Awsrequest()
    apirqs = Apicrequest(varsDeploy)
    filevars = Formatfunc()
    process = Processfunc()
    # Obtener el token de API
    environment = varsDeploy['environment']
    loginApi = secrets.getSecret(
        connvar['environment']['production']['aws_da'],
        connvar['environment']['production']['aws_dr'],
        #connvar['environment'][environment]['aws_da'],
        #connvar['environment'][environment]['aws_dr'],
        'usr_apiconnectv10pipeline')
    apirqs.getToken(loginApi)
    
    item = {
        'consumerorg': varsDeploy.get('consumerOrg'),
        'application': varsDeploy.get('application'),
        'plan': varsDeploy.get('plan')
    }
    validate_required_fields(item, ['consumerorg', 'application', 'plan'])
    version = varsDeploy['versionProduct']
    apirqs.createSubscription(item, version=version)


if __name__ == "__main__":
    main()