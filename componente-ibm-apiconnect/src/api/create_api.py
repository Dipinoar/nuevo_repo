import os
import sys
import yaml
import packaging.version as pv
from vars.Formatted import Formatfunc
from vars.Functions import Processfunc
from vars.Apicrest import Apicrequest
from vars.Awsrest import Awsrequest
from common.RepoMetadata import build_subscription_payload
from common.RepoMetadata import resolve_catalog_context
from common.Validation import check_environment
from common.Validation import validate_required_fields
from common.Output import write_result

import json
import re
import glob


def main():

    environment = os.environ.get('TARGET_BRANCH') or os.environ.get('envi') or 'development'
    check_environment(environment)

    filevars = Formatfunc()
    process= Processfunc()
    env_vars = os.environ
    projectPath = os.environ.get('CI_PROJECT_PATH')


    pathParts = projectPath.split('/') if projectPath else []
    ciCustomBasePath = '/'.join(pathParts[:2]) if len(pathParts) >= 2 else ''
    ciCustomProjectPath = '/'.join(pathParts[2:]) if len(pathParts) > 2 else ''
    with open('config_files/api/varenvironment.yml', 'r') as varyaml:
        connvar = yaml.safe_load(varyaml)
    organizacion, catalogo = resolve_catalog_context()
    validate_required_fields(
        {'organizacion': organizacion, 'catalogo': catalogo, 'environment': environment},
        ['organizacion', 'catalogo', 'environment']
    )

    archivoyaml=process.findProductYaml(".")
    nombreProducto,versionProducto,namefile,plansresult = process.validateProductYaml(archivoyaml)
    varsSubs = build_subscription_payload(environment, archivoyaml)
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
        'plans': plansresult,
        'projectPath': projectPath,
        'ciCustomBasePath': ciCustomBasePath,
        'ciCustomProjectPath': ciCustomProjectPath
    }

    filevars.formater(variableMap,'detail_vars.yaml')

    # Create .env file
    with open('build_vars.env', 'w') as env_file:
        for key, value in variableMap.items():
            env_file.write(f"{key.upper()}={value}\n")


    # Configuración de variables produccion
    environment= "development"
    path_varsEnvi='config_files/api/varenvironment.yml'
    path_varsDeploy='detail_vars.yaml'
    directorio_busqueda = "."
    # Carga de archivos YAML
    with open(path_varsEnvi, 'r') as varyaml:
        connvar = yaml.safe_load(varyaml)
    with open(path_varsDeploy, "r") as varsenvironmentyaml:
        varsDeploy = yaml.safe_load(varsenvironmentyaml)
    secrets = Awsrequest()
    apirqs = Apicrequest(varsDeploy)
    filevars = Formatfunc()
    process = Processfunc()
    # Obtener el token de API
    loginApi = secrets.getSecret(
        connvar['environment']['production']['aws_da'],
        connvar['environment']['production']['aws_dr'],
        'usr_apiconnectv10pipeline')
    apirqs.getToken(loginApi)
    environment = varsDeploy['environment']
    # Reemplazar archivos de configuración
    process.replaceConfigFiles(environment, directorio_busqueda,varsDeploy)
    listversionproduct = apirqs.getListProduct()
    SubsListCatalog = apirqs.getSubscriptionByCatalog()
    checkSubs=process.checkEmptySubs(varsSubs,environment)
    if len(listversionproduct['results']) == 0:
        print(f'''No existen versiones previas para el producto {varsDeploy['nameProduct']} Ejecutando primera instalacion...''')
        deployResult = apirqs.ejecutar_comando_api(loginApi)
        if deployResult == 0:
            print('Despliegue correcto')
            if checkSubs:
                print("Suscribiendo aplicaciones declaradas en el product yaml")
                for item in varsSubs['subscription']['environment'][environment]:
                    print(item)
                    apirqs.createSubscription(item)
        else:
            print("Existe un error al desplegar")
            #sys.exit(1)
    else:
        print(f'''
                Existen versiones previas para el producto {varsDeploy['nameProduct']}
                Revision de Versiones...
             ''')

        sortVersion = sorted(listversionproduct['results'], key=lambda x: tuple(map(int, x['version'].split('.'))), reverse=True)
        typeChange = process.compare_versions(sortVersion[0]['version'], varsDeploy['versionProduct'])
        print(f'Versionamiento {typeChange.upper()}')
        if typeChange == 'major':
            OldVersion = sortVersion[0]
            listOldSubs = process.subsFromOldVersion(SubsListCatalog, OldVersion, environment)
            listSubsMerge=process.combineSubscription(varsSubs, listOldSubs,environment)
            dataupdate = {"state": "deprecated"}
            print(f"Producto : {OldVersion['version']} Cambiando estado a Deprecado")
            apirqs.updateProductStatus(OldVersion['name'], OldVersion['version'], dataupdate)
            deployResult = apirqs.ejecutar_comando_api(loginApi)
            if deployResult == 0:
                print(f"Suscribiendo a las siguientes Aplicaciones")
                if listSubsMerge is not None:
                    for item in listSubsMerge:
                        print(item)  # Debe mostrar en pantalla si se suscribe correctamente
                        apirqs.createSubscription(item)
            else:
                print("Existe un error al desplegar")
                #sys.exit(1)
        elif typeChange == 'minor' or typeChange == 'patch':
            filterVersion = process.filterVersionList(listversionproduct['results'], varsDeploy)
            versions = [(pv.parse(entry['version']), entry) for entry in filterVersion]
            max_version, max_element = max(versions, key=lambda x: x[0])
            print(f"Ultima version del producto instalada: {max_element['version']}")
            listOldSubs = process.subsFromOldVersion(SubsListCatalog, max_element, environment)
            listSubsMerge=process.combineSubscription(varsSubs, listOldSubs,environment)
            dataupdate = {"state": "retired"}
            print(f"Producto : {max_element['version']} Cambiando estado a Retirado")
            apirqs.updateProductStatus(max_element['name'], max_element['version'], dataupdate)
            deployResult = apirqs.ejecutar_comando_api(loginApi)
            if deployResult == 0:
                print(f"Suscribiendo a las siguientes Aplicaciones")
                if listSubsMerge is not None:
                    for item in listSubsMerge:
                        print(item)  # Debe mostrar en pantalla si se suscribe correctamente
                        apirqs.createSubscription(item)

            else:
                print("Existe un error al desplegar")
                sys.exit(1)
        else:
            print('No cumple con el versionamiento del PRODUCTO, se realizara la instalacion pero no podra ser mezclada a la Rama Development')
            deployResult = apirqs.ejecutar_comando_api(loginApi)
            if deployResult == 0:
                print('Despliegue OK')
            else:
                print("Existe un error al desplegar")
                #sys.exit(1)
            print('Advertencia : ESTE DESPLIGUE NO PUEDE SER MEZCLADO A LA RAMA DESTINO NO CUMPLE CON EL VERSIONAMIENTO')
            sys.exit(1)


if __name__ == "__main__":
    main()