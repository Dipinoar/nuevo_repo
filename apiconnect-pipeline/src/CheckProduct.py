from vars.Awsrest import Awsrequest
from vars.Functions import Processfunc
import os
import yaml
import json
import sys


def main():
    path_varsEnvi='CICD/resources/varenvironment.yaml'
    path_varsDeploy='detail_vars.yaml'
    path_varsSubs='configSubs.yaml'
    directorio_busqueda = "."
    with open(path_varsEnvi, 'r') as varyaml:
        varsEnvi = yaml.safe_load(varyaml)
    with open(path_varsDeploy, "r") as varsEnvironmentyaml:
        varsDeploy =  yaml.safe_load(varsEnvironmentyaml)
    with open(path_varsSubs, "r") as subsvars:
        varsSubs = yaml.safe_load(subsvars)

    secrets = Awsrequest()
    #loginIgnite = secrets.getSecretNoSts('repocreation-secrets')
    process= Processfunc()
    loginApi = secrets.getSecret(
        varsEnvi['environment']['production']['aws_da'],
        varsEnvi['environment']['production']['aws_dr'],
        'usr_apiconnectv10pipeline'
        )


    default_design = '{"synaptic-token": "11111", "type": "noIgnite"}'

    DESIGN_ID = os.environ.get('DESIGN_ID', default_design)
    parseDI = json.loads(DESIGN_ID)
    print(json.dumps(parseDI, indent=4))

    print("******** REVISANDO VISIBILITY  ******")
    process.checkvisibility(directorio_busqueda)
    
    if parseDI['type'] == 'iuapilegacy':
        print("******** REVISANDO DATAPOWER GATEWAY  ******")
        process.checkDp(directorio_busqueda)
    elif parseDI['type'] == 'iuapi':
        print("******** NO aplica revision Datapower Gateway  ******")
        #sys.exit(1)
    else:
        print("******** No Ignite API ******")
        #sys.exit(1)

    #print("******** REVISANDO DESING ID EN IGNITE ******")
    # Buscar Yaml de las Apis
    #process.buscarCompararApis(directorio_busqueda,loginIgnite,parseDI,"check")

    print("******** REVISANDO Suscripciones en Desarrollo, QA y Produccion ******")
    #revision de las subscripciones en todos los ambientes
    checkDesa=process.checkEmptySubs(varsSubs,'development')
    checkQa=process.checkEmptySubs(varsSubs,'quality')
    checkProd=process.checkEmptySubs(varsSubs,'production')
    contardesa = contarqa = contarprod = 0

    if checkDesa:
        contardesa=process.get_subscriptions_and_print_results(loginApi,varsDeploy,'development',varsSubs,varsEnvi)
    if checkQa:
        contarqa=process.get_subscriptions_and_print_results(loginApi,varsDeploy,'quality',varsSubs,varsEnvi)
    if checkProd:
        contarprod=process.get_subscriptions_and_print_results(loginApi,varsDeploy,'production',varsSubs,varsEnvi)
    if(contardesa >= 1 or contarqa >= 1 or contarprod >= 1):
        print(f'SE ENCONTRARON PROBLEMAS PARA VALIDAR LA SUSCRIPCION ')
        sys.exit(1)


if __name__ == "__main__":
    main()