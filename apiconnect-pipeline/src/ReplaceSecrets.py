import os
import sys
import yaml
import packaging.version as pv
from vars.Formatted import Formatfunc
from vars.Functions import Processfunc
from vars.Apicrest import Apicrequest
from vars.Awsrest import Awsrequest

def main():
   
    # Configuración de variables produccion
    environment= os.environ.get('TARGET_BRANCH')
    path_varsEnvi='CICD/resources/varenvironment.yaml'
    path_varsDeploy='detail_vars.yaml'
    path_varsSubs='configSubs.yaml'
    directorio_busqueda = "."
    # Carga de archivos YAML
    with open(path_varsEnvi, 'r') as varyaml:
        connvar = yaml.safe_load(varyaml)
    with open(path_varsDeploy, "r") as varsenvironmentyaml:
        varsDeploy = yaml.safe_load(varsenvironmentyaml)
    with open(path_varsSubs, "r") as subsvars:
        varsSubs = yaml.safe_load(subsvars)
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
    # Obtener la lista de productos y suscripciones
    listversionproduct = apirqs.getListProduct()
    SubsListCatalog = apirqs.getSubscriptionByCatalog()
    checkSubs=process.checkEmptySubs(varsSubs,environment)
    if len(listversionproduct['results']) == 0:
        print(f'''No existen versiones previas para el producto {varsDeploy['nameProduct']} Ejecutando primera instalacion...''')
        deployResult = apirqs.ejecutar_comando_api(loginApi)
        if deployResult == 0:
            print('Ejecutando suscripcion por archivo yaml')
            if checkSubs:
                listFilessub = varsSubs['subscription']['environment'][environment]
                for item in listFilessub:
                    print(item)  # Debe mostrar en pantalla si se suscribe correctamente
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
                print('Ejecutando suscripcion por archivo yaml')
                if checkSubs:
                    listFilessub = varsSubs['subscription']['environment'][environment]
                    for item in listFilessub:
                        print(item)  # Debe mostrar en pantalla si se suscribe correctamente
                        apirqs.createSubscription(item)
            else:
                print("Existe un error al desplegar")
                #sys.exit(1)
            print('Advertencia : ESTE DESPLIGUE NO PUEDE SER MEZCLADO A LA RAMA DESTINO NO CUMPLE CON EL VERSIONAMIENTO')
            sys.exit(1)

if __name__ == "__main__":
    main()