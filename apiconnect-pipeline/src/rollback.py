import sys
import yaml
import time
import packaging.version as pv
from vars.Formatted import Formatfunc
from vars.Functions import Processfunc
from vars.Apicrest import Apicrequest
from vars.Awsrest import Awsrequest
import json

def load_yaml(file_path):
    try:
        print(f'leyendo el archivo {file_path}')
        with open(file_path, 'r') as yaml_file:
            return yaml.safe_load(yaml_file)
    except FileNotFoundError:
        print(f"Info: No se encontro el archivo {file_path} validar el tipo de instalacion, el archivo subsOldVersion.yaml no existira si es primera version ")
        return None

def main(config_paths,login_api_data):
    print('Ejecutando Rollback')
    path_varsEnvi, path_varsDeploy, path_varsSubs, directorio_busqueda = config_paths

    connvar = load_yaml(path_varsEnvi)
    varsDeploy = load_yaml(path_varsDeploy)
    #print(f" LINEA 21 varsDeploy: {json.dumps(varsDeploy, indent=4)}")
    varsSubs = load_yaml(path_varsSubs)
    name_actual=varsDeploy['nameProduct']
    version_actual=varsDeploy['versionProduct']

    secrets = Awsrequest()
    apirqs = Apicrequest(varsDeploy)
    filevars = Formatfunc()
    process = Processfunc()

    try:
        loginApi = login_api_data
         # Obtener el token de API
        loginApi = secrets.getSecret(
            connvar['environment']['production']['aws_da'],
            connvar['environment']['production']['aws_dr'],
            'usr_apiconnectv10pipeline')
        apirqs.getToken(loginApi)
        environment = varsDeploy['environment']
        list_version_product = apirqs.getListProduct()
        size_list_version_product= len(list_version_product['results'])
        #print(f"list_version_product = {json.dumps(list_version_product, indent=4)}")
        #print(f'tamaño size_list_version_product {size_list_version_product}')
        sort_version = sorted(list_version_product['results'], key=lambda x: tuple(map(int, x['version'].split('.'))), reverse=True)
        #print(f"sort_version = {json.dumps(sort_version, indent=4)}")
        #print(f'tamaño {len(sort_version)}')
        filter_version = process.filterVersionList(sort_version, varsDeploy)
        #print(f"filter_version = {json.dumps(filter_version, indent=4)}")
        #print(f'tamaño {len(filter_version)}')
        #print(json.dumps(variableMap, indent=4))

        if len(filter_version) == 0:
           print("IF 1")
           print("no existen registros para la busqueda solicitada")
           sys.exit(1)
        elif filter_version[0]['name'] == name_actual and filter_version[0]['version'] != version_actual:
            print("IF 2")
            print(f"No es posible reversar la version indicada {version_actual}")
            for item in filter_version:
                print(f"Nombre : [{item['name']}], Version [{item['version']}]")
            sys.exit(1)
        elif size_list_version_product == 1:
            print("IF 3")
            print(f"Este es el único producto {name_actual} Registrado con la version {version_actual}, Producto sera Eliminado")
            product_update_data = {"state": "retired"}
            print(f"Producto: {version_actual} Cambiando estado a retirado")
            apirqs.updateProductStatus(name_actual, version_actual, product_update_data)
            apirqs.deleteProduct(name_actual, version_actual)

        elif len(filter_version) == 1 and filter_version[0]['name'] == name_actual and filter_version[0]['version'] == version_actual:
            print("IF 4")
            print(f"Este es el único producto Registrado {filter_version[0]['version']}, esta versión será eliminada")
            print(f"Reversa a la versión: {sort_version[1]['version']}")
            list_subs_merge = process.combineSubscription(varsSubs, None, environment)
            product_update_data = {"state": "published"}
            print(f"Producto: {sort_version[1]['version']} Cambiando estado a Re-Publicado")
            apirqs.updateProductStatus(name_actual, sort_version[1]['version'], product_update_data)
            print(f"Suscribiendo a las siguientes Aplicaciones")
            time.sleep(20)
            #if list_subs_merge is not None:
            #    for item in list_subs_merge:
            #        print(item)  # Debe mostrar en pantalla si se suscribe correctamente
            #        apirqs.createSubscription(item, name_actual, sort_version[1]['version'])
            product_update_data = {"state": "retired"}
            print(f"Producto: {version_actual} Cambiando estado a retirado")
            apirqs.updateProductStatus(name_actual, version_actual, product_update_data)
            apirqs.deleteProduct(name_actual, version_actual)
        elif len(filter_version) > 1:
            print("IF 5")
            print(f"Reversa a la versión: {filter_version[1]['version']}")
            list_subs_merge = process.combineSubscription(varsSubs, None, environment)
            product_update_data = {"state": "staged"}
            print(f"Producto: {filter_version[1]['version']} Cambiando estado a Disponible")
            apirqs.updateProductStatus(name_actual, filter_version[1]['version'], product_update_data)
            print(f"Producto: {filter_version[1]['version']} Cambiando estado a Publicado")
            product_publish_data = {
                "visibility": {
                    "view": {"enabled": "true", "type": "public", "org_urls": [], "group_urls": []},
                    "subscribe": {"enabled": "true", "type": "authenticated", "org_urls": [], "group_urls": []}
                },
                "state": "published"
            }
            apirqs.updateProductStatus(name_actual, filter_version[1]['version'], product_publish_data)
            time.sleep(10)
            print(f"Suscribiendo a las siguientes Aplicaciones")
            if list_subs_merge is not None:
                for item in list_subs_merge:
                    print(item)  # Debe mostrar en pantalla si se suscribe correctamente
                    apirqs.createSubscription(item, name_actual, filter_version[1]['version'])
            #print(f" LINEA 91 varsDeploy: {json.dumps(varsDeploy, indent=4)}")
            product_update_data = {"state": "retired"}
            print(f"Producto: {version_actual} Cambiando estado a retirado")
            apirqs.updateProductStatus(name_actual, version_actual, product_update_data)
            apirqs.deleteProduct(name_actual, version_actual)
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    config_paths = (
        'CICD/resources/varenvironment.yaml',
        'detail_vars.yaml',
        'subsOldVersion.yaml',
        '.'
    )
    login_api_data=''
    main(config_paths,login_api_data)