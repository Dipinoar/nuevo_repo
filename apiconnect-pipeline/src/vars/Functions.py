import re
import yaml
import os
import glob
import sys
import filecmp
import json
# from vars.Apiignite import Ignitefunc
from vars.Apicrest import Apicrequest
from vars.Awsrest import Awsrequest
# Clase conexión en donde se utiliza url y token
class Processfunc:
    def __init__(self):
        self.url = ''
        self.actionMr= os.environ.get('CI_PIPELINE_SOURCE')

    # Creación de conexión con Gitlab
    def checkSubFile(self, ListFilessub, listSubs, listApp):
        CountSubs = listSubs['total_results']
        if CountSubs == 0:
            print("No existen subscripciones en el catálogo")
        else:
            results = listSubs["results"]
            yaml_records = []
            for result in results:
                record = {
                    "product_name": result["product"]["name"],
                    "consumer_org_name": result["consumer_org"]["name"],
                    "app_name": result["app"]["name"]
                }
                yaml_records.append(record)
            for item1 in ListFilessub:
                consumerorg = item1['consumerorg']
                application = item1['application']
                product_name = 'rappilandingpage'
                matching_items = [
                    item2 for item2 in yaml_records if item2['consumer_org_name'] == consumerorg and
                    item2['app_name'] == application and item2['product_name'] == product_name
                ]
                print(f"""
                Se busca subscripción:
                consumerorg='{consumerorg}'
                application='{application}'
                """)
                if matching_items:
                    print("Subscripción encontrada:")
                    for item in matching_items:
                        print(item)
                else:
                    print(f"""
                    No se encontró subscripción
                    consumerorg='{consumerorg}'
                    application='{application}'
                    """)
                    print("Validando subscripción en ambiente")

                    yaml_items = [{
                        "consumerorg": consumerorg,
                        "application": application
                    }]
                    self.checkAppConOrg(listApp, yaml_items)
                    print('Pase por aquí')

    def checkAppConOrg(self, listApp, listfind):
        CountSubs = listApp['total_results']
        if CountSubs == 0:
            print("No existen Aplicaciones en la Organizacion")
            return
        results = listApp["results"]
        yaml_records = [
            {"app_name": result["name"], "consumer_org_name": result["consumer_org"]["name"]}
            for result in results
        ]
        for item1 in listfind:
            consumerorg = item1['consumerorg']
            application = item1['application']

            matching_items = [
                item2 for item2 in yaml_records
                if item2['consumer_org_name'] == consumerorg and item2['app_name'] == application
            ]
            print(f"""
            Se Busca APP en Catalogo: 
            consumerorg='{consumerorg}'
            application='{application}'
            """)
            if matching_items:
                print("App Encontrada:")
                for item in matching_items:
                    print(item)
            else:
                print(f"""
                No se encontro APP, esta debe ser creada y asociada a una organizacion de consumo en el catalogo de instalacion: 
                consumerorg='{consumerorg}'
                application='{application}'
                """)     

    def listReplaceSecrets(self,config,path):
        pattern = re.compile(r"(?:.*@@@)(.*)(?:@@@.*)")
        allPropsUrban = set()
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(config):
                    with open(os.path.join(root, file), 'r') as f:
                        fileText = f.read()
                        matches = re.findall(pattern, fileText)
                        allPropsUrban.update(matches)
        propToYaml = yaml.dump(list(allPropsUrban), indent=4)
        #print(propToYaml)
        with open('varReplace.yaml', 'w') as f:
            f.write(propToYaml)

    def replaceSecrets(self,listSecrets):
        #print(type(listSecrets))
        #print(listSecrets)
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.conf'):
                    archivo = os.path.join(root, file)
                    with open(archivo, 'r') as file:
                        contenido = file.read()
                    for clave, valores in listSecrets.items():
                        for llave, valor in valores['keys'].items():
                            patron = f'@@@{clave}:{llave}@@@'
                            contenido = re.sub(patron, valor, contenido)
                    with open(archivo, 'w') as file:
                        file.write(contenido)
                    with open(archivo, 'r') as file:
                        contenido = file.read()
    
    def replaceYaml(self,config_files):
        print(config_files)
        if not config_files:
            print(f'No se encontraron archivos config')
            exit()
        for config_file_path in config_files:
            with open(config_file_path, "r") as text_file:
                text_file_content = text_file.read()
            partial_yaml = yaml.safe_load(text_file_content)
            properties = partial_yaml['x-ibm-configuration']['properties']
            print("=" * 60)
            # Obtener la ruta del directorio que contiene el archivo config_file_path
            directory_path = os.path.dirname(config_file_path)
            #print(directory_path)
            parent_directory = os.path.dirname(directory_path)
            #print(parent_directory)
            for entry in os.scandir(parent_directory):
                #print(entry)
                if entry.name.endswith(".yaml") and entry.is_file():
                    print("[INFO] Archivo YAML a modificar: " + entry.name)
                    file_path = entry.path

                    with open(file_path, "r") as yaml_file:
                        yaml_documents = list(yaml.safe_load_all(yaml_file))

                    for document in yaml_documents:
                        document['x-ibm-configuration']['properties'].update(properties)

                    with open(file_path, "w") as updated_yaml_file:
                        yaml.safe_dump_all(yaml_documents, updated_yaml_file, default_flow_style=False)

                    #print("[INFO] El yaml completo es:\n" + yaml.dump_all(yaml_documents))
                    
            print("[INFO] Archivo modificado")

    def buscarApiyaml(self,directorio):
        archivos_yaml = []
        #exclusiones = ['test', '.gitlab-ci.yml', './configSubs.yaml','detail_vars.yaml','CICD','ignite']
        exclusiones = ['.gitlab-ci.yml', './configSubs.yaml','detail_vars.yaml','CICD','ignite']
        for ruta_actual, _, archivos in os.walk(directorio):
            if any(exclusion in ruta_actual for exclusion in exclusiones):
                continue  # Ignorar esta ruta si contiene cualquiera de las exclusiones
            for archivo in archivos:
                ruta_completa = os.path.join(ruta_actual, archivo)
                if any(exclusion in ruta_completa for exclusion in exclusiones):
                    continue  # Ignorar este archivo si contiene cualquiera de las exclusiones
                if archivo.endswith('.yaml') or archivo.endswith('.yml'):
                    archivos_yaml.append(ruta_completa)
        #for ruta_actual, _, archivos in os.walk(directorio):
        #    for archivo in archivos:
        #        if archivo.endswith('.yaml') or archivo.endswith('.yml'):
        #            ruta_completa = os.path.join(ruta_actual, archivo)
        #            archivos_yaml.append(ruta_completa)
        return archivos_yaml

    def get_detail(self,apiyaml):
        with open(apiyaml, 'r') as archivo:
            contenido = yaml.safe_load(archivo)
            #print(contenido)
            if 'info' in contenido and 'x-ibm-name' in contenido['info']:
                #print('entre if')
                mapa = {
                    contenido['info']['x-ibm-name'] : contenido['info']['version']
                    }
                #print(mapa)
                return mapa
        return None
    
    def obtener_detalles_api(self, directorio):
        archivos_yaml = []
        exclusiones = ['.gitlab-ci.yml', './configSubs.yaml', 'detail_vars.yaml', 'CICD', 'ignite']
        detalles = {}

        for ruta_actual, _, archivos in os.walk(directorio):
            if any(exclusion in ruta_actual for exclusion in exclusiones):
                continue
            for archivo in archivos:
                ruta_completa = os.path.join(ruta_actual, archivo)
                if any(exclusion in ruta_completa for exclusion in exclusiones):
                    continue
                if archivo.endswith('.yaml') or archivo.endswith('.yml'):
                    archivos_yaml.append(ruta_completa)
                    with open(ruta_completa, 'r') as archivo_yaml:
                        contenido = yaml.safe_load(archivo_yaml)
                        if 'info' in contenido and 'x-ibm-name' in contenido['info']:
                            detalles[contenido['info']['x-ibm-name']] = {'version': contenido['info']['version'],'path': ruta_completa
                            }
        return detalles
    
    def compare_versions(self,old,new):
        v1 = tuple(map(int, old.split('.')))
        v2 = tuple(map(int, new.split('.')))
        #v1=(2, 5, 2) #antigua version
        #v2= (2, 5, 1) #nueva version
        print(f"Old Version {v1} V/S New Version {v2}")
        comparison_map = {
            "100": "major",
            "010": "minor",
            "001": "patch",
            "000": "equal",
            "222": "block"
        }
        major, minor, patch = "0","0","0"

        major = "0" if v1[0] == v2[0] else "1" if v1[0] < v2[0] else "2"
        print(f"major = {major}")
        if(major == "0"):
            minor = "0" if v1[1] == v2[1] else "1" if v1[1] < v2[1] else "2"
            print(f"minor = {minor}")
        if(minor == "0" and major == "0"):
            patch = "0" if v1[2] == v2[2] else "1" if v1[2] < v2[2] else "2"
            print(f"patch = {patch}")
        combination = major + minor + patch
        if major == "2" or minor == "2" or patch == "2":
            combination = "222"
        key_name = comparison_map.get(combination, "No se pudo determinar la relación")
        return key_name
    
    def compare_yaml(self, path1, path2):
        #test file2_path = '../test/compare/compare_api_file.yaml'
        print(f'comparando : {path1} y {path2}')
        are_equal = filecmp.cmp(path1, path2)
        print(are_equal)
        if are_equal:
            print("Los archivos son iguales. No hay cambios en la Api")
            return True
        else:
            print("Los archivos son diferente y no se detecto un cambio de version ") 
            return False
 
    def checkSubscription(self,varsSubs,listapps,environment):
        print('[INFO] Subscripciones dentro de ConfigSubs.yaml')
        for app in varsSubs['subscription']['environment'][environment]:
            print (f'asociado al consumer org : {app["consumerorg"]} Aplicacion : {app["application"]}  ' )
        print('[INFO FIN]')
        print(f'[INFO] Aplicaciones y consumerOrg disponibles en {environment}')
        for app in listapps['results']:
            print (f'asociado al consumer org : {app["consumer_org"]["name"]} Aplicacion : {app["name"]} ')
        print('[INFO FIN]')
        #print(json.dumps(varsSubs['subscription']['environment']['development'], indent=4))
        #print(json.dumps(listapps['results'], indent=4))
        coincidencias = []
        no_coincidencias = []
        for item1 in varsSubs['subscription']['environment'][environment]:
            found = False
            for item2 in listapps['results']:
                if item1["consumerorg"] == item2["consumer_org"]["name"] and item1["application"] == item2["name"]:
                    coincidencias.append({"consumerorg": item1["consumerorg"], "application": item1["application"]})
                    found = True
                    break
            if not found:
                no_coincidencias.append({"consumerorg": item1["consumerorg"], "application": item1["application"]})
            else:
                found = False  # Restablecer la variable found para continuar con el siguiente registro de dato1
        return coincidencias, no_coincidencias
        
    # def buscarCompararApis(self,pathfind,ignite_data,parseDI,action):
    #     spectIgnite = Ignitefunc(ignite_data)
    #     blockCheck = 0
    #     # Reemplaza con la ruta del directorio a buscar
    #     print(" [INFO INICIO] Archivos Yaml encontrados: ")
    #     archivos_yaml_encontrados = self.obtener_detalles_api(pathfind)
    #     print(json.dumps(archivos_yaml_encontrados, indent=4))
    #     print(" [INFO FIN] ")
    #     full_data_apis = {}  # Convertir en diccionario
    #     path_apis = {}  # Convertir en diccionario
    #     parseDI_keys = set(parseDI.keys())  # Convertir las claves de parseDI a un conjunto para mejorar la eficiencia de búsqueda
    #     for key, detalle in archivos_yaml_encontrados.items():
    #         archivo_yaml = detalle['path']
    #         print(f'Yaml Api : {archivo_yaml}')
    #         if detalle['version'] is not None:
    #             path_apis[key] = archivo_yaml  # Agregar al diccionario path_apis
    #             if key not in parseDI_keys:
    #                 print(f"No se encontró coincidencia para {key}")
    #                 sys.exit(1)
    #         full_data_apis[key] = detalle['version']
    #     print(f"[INFO INICIO] Data Apis Versiones: {json.dumps(full_data_apis, indent=4)} [INFO FIN]")
    #     common_keys = set(full_data_apis.keys()) & set(path_apis.keys()) & set(parseDI.keys())
    #     combined_dict = {}
    #     for key in common_keys:
    #         combined_dict[key] = (full_data_apis[key], path_apis[key], parseDI[key])
    #     design_details = {key: spectIgnite.checkdesign(value_from_dict3) for key, (_,_,value_from_dict3) in combined_dict.items()}
    #     print(f"[INFO INICIO] Design_details: {json.dumps(design_details, indent=4)} [INFO FIN]")

    #     spect_details = {key: spectIgnite.checkspect(str(design_detail['SPEC_ID'])) for key, design_detail in design_details.items()}
    #     print(f"[INFO INICIO] Spect_details: {json.dumps(spect_details, indent=4)} [INFO FIN]")
            
         # comparacion de los versiones y decisiones :
         # comparacion version igniter versus la del yaml Api
         # si la comparacion es major, minor, minor hacia arriba, seguira a validar suscripciones,
         # si la comparacion da Equal, hara una comparacion binaria de los yaml de la Api y el Yaml descargado de la version de la especificacion
         # si la comparacion de los yaml da como resultado diferencia, corta el proceso y lanza el error, que no se cambio la version si cambiaron los yaml, de lo contrario seguira el proceso
        # print(combined_dict)
        # for key, (yaml_version, yaml_path, design_id) in combined_dict.items():
        #     nombres_archivos_sin_extension = {}
        #     # Obtener el nombre del archivo con extensión .yaml
        #     archivo_con_extension = yaml_path.split('/')[-1]
        #     # Quitar la extensión .yaml
        #     archivo_sin_extension = archivo_con_extension.replace('.yaml', '')
        #     # Almacenar el nombre del archivo sin la extensión .yaml en el diccionario
        #     spect_detail = spect_details[key]
        #     print(f"[INFO INICIO] lectura de key : {key} y el detalle :{spect_detail['spect_id']} [INFO FIN]")
        #     print(f"[INFO INICIO] El Api: {key}  la última versión de ignite es {spect_detail['spect_version']} [INFO FIN]")
        #     comparison = self.compare_versions(spect_detail['spect_version'], yaml_version)
        #     print(f'[INFO INICIO] Tipo de cambio : {comparison} [INFO FIN]')
        #     if action == "check":
        #         if comparison == "equal":
        #             print('Versiones iguales')
        #             filecompare = spectIgnite.download_attachment_spec(spect_detail['attachments'], 'compare/')
        #             if not self.compare_yaml(yaml_path, filecompare):
        #                print('Advertencia : Se detectaron cambios en el Yaml pero no se realizo el Versionamiento correcto')
        #                #sys.exit(1)
        #         elif comparison == "block":
        #             print('Advertencia : No se realizo versionamiento Correcto Esto es una Advertencia no sera validado para realizar Merge a la Rama destino')
        #             blockCheck =+ 1
        #             #sys.exit(1)
        #         else:
        #             print('No se detectaron problemas a nivel de versiones')
        #     else:
        #         if comparison == "equal":
        #             print('Versiones iguales')
        #         elif comparison == "block":
        #             print('Advertencia : No cumple con el versionamiento no puede ser creado la nueva especificacion')
        #             blockCheck =+ 1
        #             #sys.exit(1)
        #         else:
        #             print('se crea un nuevo spect')
        #             spectIgnite.createNewSpect_api(yaml_path,'iuapilegacy','cevv356k@itau.cl',key,design_id)
        #             print('Pasa a busqueda de job_id')
        #             print(archivo_sin_extension)
        #             job_id=spectIgnite.get_jobid(archivo_sin_extension)
        #             print(f'job_id = {job_id}')
        #             new_id_spect=spectIgnite.get_job_detail(job_id)
        #             print(f'new_id_spect = {new_id_spect}')
        #             print(f'Se actualiza la especificacion con el spect {new_id_spect} y la version {yaml_version}')
        #             spectIgnite.update_spect_id(new_id_spect,yaml_version,'development')
        #             print(f'se sube archivo {yaml_path}')
        #             spectIgnite.upload_attachment_spec(new_id_spect,yaml_path)
        # if blockCheck > 0 :
        #     print('Advertencia : No cumple con el versionamiento de APIS no puede ser creado la nueva especificacion')
        #     sys.exit(1)

    def get_subscriptions_and_print_results(self,loginApi,varsDeploy,environment,varsSubs,varsEnvi):
        print(f'************** Revisando Ambiente : {environment} ***************')
        no_encontrados=0
        varsDeploy['realm'] = varsEnvi['environment'][environment]['realm']
        varsDeploy['urlmanager'] = varsEnvi['environment'][environment]['urlmanager']
        apirqs = Apicrequest(varsDeploy)
        apirqs.getToken(loginApi)
        listapps = apirqs.getAppByCatalog(varsDeploy)

        coincidencias, no_coincidencias = self.checkSubscription(varsSubs, listapps,environment)
        print(f'{"*"*30}')
        print(f'[INFO] Lista de Coincidencias Comparando ConfigSubs y Ambiente {environment}:')
        if len(coincidencias) > 0:
            print(f'se registraron las siguientes coincidencias : {json.dumps(coincidencias, indent=4)}')
        print('[INFO FIN]')
        print('[INFO] Lista de Aplicaciones no Encontrados para Suscribir :')
        if len(no_coincidencias) > 0:
            no_encontrados+=1
            print(f'[ ERROR ]se registraron las siguientes no coincidencias : {json.dumps(no_coincidencias, indent=4)}')
        print('[INFO FIN]')
        return len(no_coincidencias)

    def subsFromOldVersion(self,listsubs,dataCurrentVersion,environment):
        subscription_data={'subscription':{'environment':{environment:[]}}}
        for subs in listsubs['results']:
            if subs['product']['name'] == dataCurrentVersion['name'] and subs['product']['version'] == dataCurrentVersion['version']:
                subscription_info = {
                    'consumerorg':subs['consumer_org']['name'],
                    'application':subs['app']['name'],
                    'plan': subs['plan'] if 'plan' in subs else 'default-plan'
                }
                subscription_data['subscription']['environment'][environment].append(subscription_info)
                # Aquí guardamos la información actual en un archivo YAML
        with open('subsOldVersion.yaml', 'w') as yaml_file:
            yaml.dump(subscription_data, yaml_file, default_flow_style=False)
        return subscription_data

    def filterVersionList(self,listVersion,dataProduct):
        name=dataProduct['nameProduct']
        version=dataProduct['versionProduct']
        filtered_versions = []
        for variable in listVersion:
            if variable['name'] == name:
                # Comparar el primer carácter después del punto en 'version'
                if variable['version'].split('.')[0][0] == version.split('.')[0][0]:
                    filtered_versions.append(variable)
        return filtered_versions
    
    def replaceConfigFiles(self,environment,directorio_busqueda,varsDeploy):
        secrets = Awsrequest()
        env_mapping = {
                        "development": "DESA",
                        "quality": "QA",
                        "production": "PROD"
                        } 
        if environment in env_mapping:
            config = f'{env_mapping[environment]}.conf'
        else:
            sys(exit) 
        self.listReplaceSecrets(config,directorio_busqueda)
        results_secrets = {}
        with open("varReplace.yaml", "r") as listsecrets:
            secretsname = yaml.safe_load(listsecrets)
        for name in secretsname:
            name = name.split(":")[0]
            print(f'{name}')
            results = secrets.getSecret(varsDeploy['aws_da'], varsDeploy['aws_dr'], name)
            #results = ""
            #print(f'contenido results : {results}')
            if name not in results_secrets:
                results_secrets[name] = results
        #test#
        #results_secrets='{"APIKey/qa/pruebanueva/pruebanueva/contenedorborrar": {"keys": {"llavepruebacliente": "HOLAMUNDOEDUARDO", "llavepruebasecreto": "HOLAMUNDORICARDO"}, "secretname": "APIKey/qa/pruebanueva/pruebanueva/contenedorborrar"}}'
        # end test#
        yaml_data = yaml.safe_dump(results_secrets)
        #test#print(f'yaml_data : {yaml_data}')
        #test#print(type(yaml_data))
        #test#print('escribir resultados archivo')
        with open("resultados.yaml", "w") as yaml_file:
            yaml_file.write(yaml_data)
        with open('resultados.yaml', 'r') as registries:
            listSecret = yaml.safe_load(registries)
        self.replaceSecrets(listSecret)
        #test#
        #pathProperties=f"../**/properties_{config}"
        #end Test#
        pathProperties=f"**/properties_{config}"
        config_files = glob.glob(pathProperties, recursive=True)
        self.replaceYaml(config_files)

    def checkEmptySubs(self,list1,environment):
        response = True
        if list1 is not None:
            found_none = False
            for development_item in list1['subscription']['environment'][environment]:
                for key, value in development_item.items():
                    if value is None:
                        found_none = True  # Establecemos la variable a True si encontramos un 'None'
            if found_none:
                print("No hay registros")
                response = False
        else :
            response = False
        return response
    
    def combineSubscription(self,list1, list2,environment):
        combined_list=[]
        check1=self.checkEmptySubs(list1,environment)
        check2=self.checkEmptySubs(list2,environment)
        if check1:
            print('LISTA SUBS REVISION UNO')
            combined_list+=list1['subscription']['environment'][environment]
        if check2:
            print('LISTA SUBS REVISION DOS')
            combined_list+=list2['subscription']['environment'][environment]
        unique_combined_list = []
        seen = set()
        for item in combined_list:
            if item is not None:
                item_tuple = tuple(item.items()) 
                if item_tuple not in seen:
                    seen.add(item_tuple)
                    unique_combined_list.append(item)
        return unique_combined_list

    def findProductYaml(self, directorio):
        archivos_yaml = glob.glob(os.path.join(directorio, '*.yaml'))
        if not archivos_yaml:
            print("No se encontraron archivos YAML en el directorio.")
            sys.exit(1)
        for archivo in archivos_yaml:
            try:
                with open(archivo, 'r') as archivo_yaml:
                    contenido = yaml.load(archivo_yaml, Loader=yaml.FullLoader)
                if 'product' in contenido:
                    return archivo
            except yaml.YAMLError as exc:
                print(f"Error al leer el archivo {archivo}: {exc}")
                continue
        print("No se encontró un archivo YAML con el tag 'product'.")
        sys.exit(1)
    
    def validateProductYaml(self, archivo):
        try:
            with open(archivo, 'r') as archivo_yaml:
                contenido = yaml.load(archivo_yaml, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(f"Error al procesar el archivo {archivo}: {exc}")
            sys.exit(1)
       # Validaciones
        errores = []
        info = contenido.get('info', {})
        if 'name' not in info or 'version' not in info:
            errores.append("No se encontraron las variables 'name' y 'version'")
        if errores:
            for error in errores:
                print("Error:", error)
            sys.exit(1)
        nombreProducto = contenido['info']['name']
        versionProducto = contenido['info']['version']
        namefile = os.path.basename(archivo)
        plansresult = {'plans': list(contenido['plans'].keys())} if 'plans' in contenido else {}
        print(nombreProducto, versionProducto, namefile)
        return nombreProducto, versionProducto, namefile, plansresult

    def checkvisibility(self,directorio_busqueda):
        error=0
        for nombre_archivo in os.listdir(directorio_busqueda):
            if nombre_archivo.endswith(".yaml"):
                print("=" * 60)
                print(nombre_archivo)
                ruta_completa = os.path.join(directorio_busqueda, nombre_archivo)
                with open(ruta_completa, 'r') as archivo:
                    try:
                        contenido_yaml = yaml.safe_load(archivo)
                        if 'product' in contenido_yaml:
                            if 'visibility' in contenido_yaml:
                                if 'view' in contenido_yaml['visibility']:
                                    if 'type' in contenido_yaml['visibility']['view']:
                                        if contenido_yaml['visibility']['view']['type'] != 'authenticated':
                                            print("[ERROR] El Producto de API tiene visibility.view.type diferente a 'authenticated'")
                                            error=1
                                        else:
                                            print("[OK] El Producto de API tiene visibility.view.type en 'authenticated'")
                                if 'subscribe' in contenido_yaml['visibility']:
                                    if 'type' in contenido_yaml['visibility']['subscribe']:
                                        if contenido_yaml['visibility']['subscribe']['type'] != 'authenticated':
                                            print("[ERROR] El Producto de API tiene visibility.subscribe.type diferente a 'authenticated'")
                                            error=1
                                        else:
                                            print("[OK] El Producto de API tiene visibility.subscribe.type en 'authenticated'")
                    except yaml.YAMLError as exc:
                        print(exc)
        if error == 1 :
            exit(1)

    def checkDp(self,directorio_busqueda):
        print("\n" + "=" * 60)
        error=0

        project_dir = os.environ.get("CI_PROJECT_DIR", "")
        print(f"[INFO] CI_PROJECT_DIR: {project_dir}")

        if "/channels/mobile/" in project_dir:
            expected_gateway = "datapower-gateway"
        else:
            expected_gateway = "datapower-api-gateway"

        print(f"[INFO] Gateway esperado: {expected_gateway}")

        for nombre_archivo in os.listdir(directorio_busqueda):
            if nombre_archivo.endswith(".yaml"):
                print("=" * 60)
                print(nombre_archivo)
                ruta_completa = os.path.join(directorio_busqueda, nombre_archivo)
                with open(ruta_completa, 'r') as archivo:
                    try:
                        contenido_yaml = yaml.safe_load(archivo)
                        if 'product' in contenido_yaml:
                            gateways = contenido_yaml.get('gateways', [])
                            if len(gateways) != 1:
                                print(f"[ERROR] El Producto de API tiene más de {len(gateways)} gateways")
                                error=1
                            else:
                                print(f"[OK] El Producto de API tiene solo {len(gateways)} gateway(s)")
                            if gateways[0] != expected_gateway:
                                print(f"[ERROR] El Producto de API tiene un gateway diferente a {expected_gateway}")
                                print(f"[INFO] Gateway encontrado: {gateways[0]}")
                                error=1
                            else:
                                print(f"[OK] El Producto de API tiene el gateway esperado: {expected_gateway}")
                    except yaml.YAMLError as exc:
                        print(exc)
        if error == 1:
            exit(1)