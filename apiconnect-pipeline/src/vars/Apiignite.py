# import os
# import yaml
# import json
# import subprocess
# import sys
# import requests
# import time
# from pathlib import Path
# class Ignitefunc:
#     def __init__(self,igniteData):
#         self.var=""
#         #self.CLIENT_ID = igniteData['ignite_uat_client_id']
#         #self.CLIENT_SECRET = igniteData['ignite_uat_client_secret']
#         #self.URL = igniteData['ignite_uat_base_url']
#         #self.URL_AUTH=igniteData['ignite_uat_base_url_auth']
#         self.CLIENT_ID = igniteData['ignite_client_id']
#         self.CLIENT_SECRET = igniteData['ignite_client_secret']
#         self.URL = igniteData['ignite_base_url']
#         self.URL_AUTH=igniteData['ignite_base_url_auth']
#         basePath = os.path.abspath(os.path.join(os.getcwd(), "."))
#         ignitepath="ignite"
#         self.fullignitepath=os.path.join(basePath, ignitepath)
#         os.environ["SCRIPTS_ROOT"] = self.fullignitepath
#         os.environ["CLIENT_ID_IGNITE"] = self.CLIENT_ID
#         os.environ["CLIENT_SECRET_IGNITE"] = self.CLIENT_SECRET
#         os.environ["URL_IGNITE"] = self.URL

#     def checkdesign(self,DESIGN_ID,expand="true"):
#         print(f"checkdesign : {DESIGN_ID}")
#         bearer_token = self.get_bearer_token()
#         data= self.call_api(
#                     bearer_token,
#                     f"{self.URL}rest/v2/designs/{DESIGN_ID}?expanded={expand}",
#                     "GET")
#         if "status" in data and data["status"]:
#             print("Error: No hay datos disponibles para el diseño indicado.")
#             sys.exit(1)  # Salir del programa con código de error 1    
#         child_specs = data["aggregate"]["childSpecs"]
#         sorted_specs = sorted(child_specs, key=lambda x: x["version"], reverse=True)
#         SPEC_ID = sorted_specs[0]["specId"]
#         STATE = sorted_specs[0]["disposition"]
#         mapa = {
#            "SPEC_ID": SPEC_ID,
#            "Design ID": DESIGN_ID,
#            "State": STATE
#        }
#         return mapa
    
#     def checkdesignFilterByVersion(self,DESIGN_ID,VERSION,expand="true"):
#         print(f"checkdesign : {DESIGN_ID}")
#         print(f"version : {VERSION}")
#         bearer_token = self.get_bearer_token()
#         data= self.call_api(
#                     bearer_token,
#                     f"{self.URL}rest/v2/designs/{DESIGN_ID}?expanded={expand}",
#                     "GET")
#         if "status" in data and data["status"]:
#             print("Error: No hay datos disponibles para el diseño indicado.")
#             sys.exit(1)  # Salir del programa con código de error 1   
#         child_specs = data["aggregate"]["childSpecs"]
#         for child_spec in child_specs:
#             if child_spec['version'] == VERSION:
#                  child_spec=child_spec  # Retorna el registro encontrado
#                  break
#         if not child_spec:
#             print("Error: No hay datos disponibles para el diseño indicado.")
#             sys.exit(1)  # Salir del programa con código de error 1  

#         SPEC_ID = child_spec["specId"]
#         STATE = child_spec["disposition"]
#         mapa = {
#            "SPEC_ID": SPEC_ID,
#            "Design ID": DESIGN_ID,
#            "State": STATE
#             }
#         return mapa
    
#     def checkspect(self, SPEC_ID,expand="true"):

#         print(f"checkspect : {SPEC_ID}")
#         bearer_token = self.get_bearer_token()
#         data= self.call_api(
#                     bearer_token,
#                     f"{self.URL}rest/v2/specifications/{SPEC_ID}?expanded={expand}",
#                     "GET")
#         if "status" in data and data["status"]:
#             print("Error: No hay datos disponibles para el spect indicado.")
#             sys.exit(1)  # Salir del programa con código de error 1    
#         mapa = {
#             "spect_id": SPEC_ID,
#             "spect_version": data['version'],
#             "spect_lc_type": data["disposition"]["type"],
#             "spect_lc_name": data["disposition"]["name"],
#             "attachments":data["attachments"],
#             "lockField":data["lockField"]
#         }
#         return mapa

#     def createNewSpec(self, DESIGN_ID, VERSION_API):
#     # Establecer variables de entorno

#         # Crear el directorio "tmp" si no existe
#         tmp_dir = os.path.join(os.getcwd(), "tmp")
#         os.makedirs(tmp_dir, exist_ok=True)

#         # Obtener el diseño y extraer datos relevantes
#         subprocess.run([f"{self.fullignitepath}/scripts/get-design.sh", DESIGN_ID, "true", "design-json" ])
#         with open("design-json") as f:
#             design_data = json.load(f)
#             child_specs = design_data["aggregate"]["childSpecs"]
#             sorted_specs = sorted(child_specs, key=lambda x: x["version"], reverse=True)
#             SPEC_ID = sorted_specs[0]["specId"]
#             STATE = sorted_specs[0]["disposition"]

#         # Imprimir información relevante
#         print("SPEC ID is:", SPEC_ID)
#         print("Design ID is:", DESIGN_ID)
#         print("State is:", STATE)

#         # Establecer variables de estado y versión
#         CODE = "Development"
#         APP_VERSION = VERSION_API

#         if len(child_specs) == 1 and STATE == "repositoryInitSuccessful":
#             print("Hay 1 child spec")
#             # Clonar la especificación y cambiar el estado a "Realized"
#             subprocess.run([f"{self.fullignitepath}/scripts/get-specification.sh", SPEC_ID, "clone-spec.json"])
#             patch_data = {
#                 "lifecycleState": {
#                     "type": "LifecycleState",
#                     "pathName": "Realized",
#                     "name": "Realized",
#                     "description": "A Type",
#                     "visualStyle": "",
#                     "code": "realized",
#                     "id": 372
#                 },
#                 "id": DESIGN_ID
#             }
#             with open("patchrealized.json", "w") as f:
#                 json.dump(patch_data, f)
#             subprocess.run([f"{self.fullignitepath}/scripts/patch-design.sh", DESIGN_ID, "patchrealized.json"])
#             print("Cambio estado diseño a Realized")
#         else:
#             print("Hay más de 1 child spec, se procede a clonado")
#             # Clonar la especificación si hay más de una
#             subprocess.run([f"{self.fullignitepath}/scripts/clone-specification.sh", str(SPEC_ID), "true", "clone-spec.json"])

#         # Asignar el ID de la especificación clonada o única
#         with open("clone-spec.json") as f:
#             clone_spec_data = json.load(f)
#             print(clone_spec_data)
#             SPEC_ID = clone_spec_data["serviceSpecification"]["specificationId"]
#         print("Nueva spec id:", SPEC_ID)

#         # Modificar la versión de la especificación clonada
#         print("Cambiando versión gitlab > ignite")
#         clone_spec_data["version"] = APP_VERSION
#         clone_spec_data["description"] = "esto es un mensaje custom"
#         with open("patch.json", "w") as f:
#             json.dump(clone_spec_data, f)
#         print("Versión a la que se modifica es:", APP_VERSION)

#         # Actualizar la especificación con la nueva versión
#         subprocess.run([f"{self.fullignitepath}/scripts/update-specification.sh", str(SPEC_ID), "patch.json"])

#         # Actualizar el estado de la especificación
#         patch_data = {
#             "id": SPEC_ID,
#             "disposition": {
#                 "code": CODE,
#                 "type": "Lifecycle"
#             }
#         }
#         with open("patch.json", "w") as f:
#             json.dump(patch_data, f)
#         subprocess.run([f"{self.fullignitepath}/scripts/patch-specification.sh", str(SPEC_ID), "patch.json"])

#         return SPEC_ID

#     def createSpectVersion():
#          # Crear el directorio "tmp" si no existe
#         tmp_dir = os.path.join(os.getcwd(), "tmp")
#         os.makedirs(tmp_dir, exist_ok=True)
#         #subprocess.call(["ignite/scripts/import-openapi-spec.sh", str(DESIGN_ID), "true", "design-json"])
#         #./import-openapi-spec.sh ../../../.download/Dummy/dummy-get_api/dummy-get_1.0.0.yaml iuapilegacy ccvc8957@itau.cl false dummy-test 234951

#     def promoteSpec(self, DESIGN_ID,VERSION_API, TARGET_BRANCH):

#         # Crear el directorio "tmp" si no existe
#         tmp_dir = os.path.join(os.getcwd(), "tmp")
#         os.makedirs(tmp_dir, exist_ok=True)
    
#         # Obtener la versión de la aplicación desde Git
#         #app_version = subprocess.check_output(["git", "tag", "--contains", subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()]).decode().strip().split('v')[-1]
    
#         # Ejecutar el script get-design.sh con los argumentos DESIGN_ID, true, design-json
#         subprocess.call([f"{self.fullignitepath}/scripts/get-design.sh", str(DESIGN_ID), "true", "design-json"])
    
#         # Leer el archivo design-json y obtener el SPEC_ID correspondiente a la APP_VERSION
#         with open("design-json") as file:
#             design_data = json.load(file)
#             child_specs = design_data["aggregate"]["childSpecs"]
#             sorted_specs = sorted(child_specs, key=lambda x: x["version"])
#             spec_id = next((spec["specId"] for spec in sorted_specs if spec["version"] == VERSION_API), None)
    
#         # Comprobar si se encontró el SPEC_ID
#         if spec_id is None:
#             print(f"Error: no se encuentra la especificacion para la versión {VERSION_API} del diseño {DESIGN_ID}")
#             with open("design-json") as file:
#                 print(file.read())
#             exit(1)
    
#         # Establecer el valor de CODE según el valor de TARGET_BRANCH
#         code = ""
#         if TARGET_BRANCH == "quality":
#             code = "Test"
#         elif TARGET_BRANCH == "production":
#             code = "Production"
    
#         # Crear el archivo patch.json con el contenido apropiado
#         patch_data = {
#             "id": spec_id,
#             "disposition": {
#                 "code": code,
#                 "type": "Lifecycle"
#             }
#         }
#         with open("patch.json", "w") as file:
#             json.dump(patch_data, file)
    
#         # Ejecutar el script patch-specification.sh con los argumentos SPEC_ID y patch.json
#         subprocess.call([f"{self.fullignitepath}/scripts/patch-specification.sh", str(DESIGN_ID), "patch.json"])

#     def updateIgniteInfo(self,varDeploy,namefile):
#         filename=namefile
#         with open(filename, 'w') as archivo:
#             yaml.dump(varDeploy, archivo)
#         print("Resultado guardado exitosamente en el archivo. ")  

#     def get_bearer_token(self):
#         # Realizar la autenticación y obtener el token
#         auth_url = self.URL_AUTH  # Reemplaza con la URL de autenticación
#         auth_data = {
#             "grant_type": "client_credentials",
#             "client_id": self.CLIENT_ID,
#             "client_secret": self.CLIENT_SECRET
#         }
#         auth_response = requests.post(auth_url, data=auth_data)

#         if auth_response.status_code == 200:
#             auth_token = auth_response.json().get("access_token")
#         else:
#             print("Error en la autenticación:", auth_response.status_code)
#         return auth_token
    
#     def call_api(self, bearer_token, api_call, method, json_data=None, binary_data=None, taxo=False):
#         try:
#             if bearer_token:
#                 headers = {"Authorization": f"Bearer {bearer_token}"}
#                 if method.upper() == "GET":
#                     if taxo:
#                         headers.update({'content-type': 'application/json', 'accept': 'application/json'})
#                     response = requests.get(api_call, headers=headers)
#                 elif method.upper() == "PUT":
#                     response = requests.put(api_call, headers=headers, json=json_data)
#                 elif method.upper() == "POST":
#                     if binary_data:
#                         response = requests.post(api_call, headers=headers, files={"file": binary_data})
#                     else:
#                         response = requests.post(api_call, headers=headers, json=json_data)
#                 elif method.upper() == "PATCH":
#                     response = requests.patch(api_call, headers=headers, json=json_data)
#                 else:
#                     raise ValueError("Método HTTP no válido. Use GET, PUT, POST o PATCH.")

#                 response.raise_for_status()  # Lanza una excepción si el código de estado no es exitoso
#                 if response.status_code == 200:
#                     if response.headers.get('content-type') == "application/json":
#                         data = response.json()
#                     # if response.headers.get('content-type') == 'applications/json':
#                     #     data = response.json()
#                     else:
#                         data = response.text
#                 else:
#                         print("Error en la solicitud:", response.status_code)
#                         data = None
#             else:
#                 print("Error en la solicitud:", response.status_code)
#                 return None
#             return data
#         except requests.exceptions.RequestException as e:
#             print("Error en la conexión:", e)
#         except requests.exceptions.HTTPError as e:
#             print("Error HTTP:", e)
#         except json.JSONDecodeError as e:
#             print("Error al decodificar JSON:", e)
#         except Exception as e:
#             print("Error inesperado:", e)
#         return None

#     def normalize_spec(self, design_id):
#         disposition_data = {
#             "type": "Lifecycle",
#             "pathName": "Repository Initialization Successful",
#             "name": "Repository Initialization Successful",
#             "description": "A Type",
#             "visualStyle": "{\"transitions\": [{\"action\": \"basic\",  \"state\":\"design\"},{\"action\": \"basic\",  \"state\":\"development\"},{\"action\": \"basic\",  \"state\":\"archived\"}]}",
#             "code": "repositoryInitSuccessful",
#             "id": 148010
#         }
#         bearer_token = self.get_bearer_token()
#         call_back = self.call_api(
#             bearer_token,
#             f"https://ignite.itau.digitalml.com/ICS/rest/v2/designs/{design_id}?expanded=true",
#         )
#         spec_id = call_back["aggregate"]["childSpecs"][0]["specId"]
#         print("spect_id: ", spec_id)
#         spec_data = self.call_api(
#             bearer_token,
#             f"https://ignite.itau.digitalml.com/ICS/rest/v2/specifications/{spec_id}?expanded=false",
#         )
#         if spec_data["version"] != "1.0.0":
#             spec_data["version"] = "1.0.0"
#             spec_data["disposition"] = disposition_data
#             self.call_api(
#                 bearer_token,
#                 f"https://ignite.itau.digitalml.com/ICS/rest/v2/specifications/{spec_id}?expanded=false",
#                 method="PUT",
#                 json_data=spec_data,
#             )

#         with open(
#             "download/Dummy/dummy-put_api/dummy-put_1.0.0.yaml", "rb"
#         ) as binary_file:
#             binary_data = binary_file
#             #print("lockFile", spec_data["lockField"])
#             lock = spec_data["lockField"]
#             self.call_api(
#                 bearer_token,
#                 f"https://ignite.itau.digitalml.com/ICS/rest/v2/specifications/{spec_id}/attachments?lockField={lock}",
#                 method="POST",
#                 binary_data=binary_data,
#             )
#     #  return response_data
#     def upload_attachment_spec(self,new_spect,yamlpath):
#         spec_data=self.checkspect(new_spect)
#         bearer_token = self.get_bearer_token()
#         with open(
#             yamlpath, "rb"
#         ) as binary_file:
#             binary_data = binary_file
#             lock = spec_data["lockField"]
#             id = spec_data["spect_id"]
#             self.call_api(
#                 bearer_token,
#                 f"https://ignite.itau.digitalml.com/ICS/rest/v2/specifications/{id}/attachments?lockField={lock}",
#                 method="POST",
#                 binary_data=binary_data,
#             )

#     def download_attachment_spec(self,spec_data,path):
        
#         bearer_token = self.get_bearer_token()
#         for datos in spec_data:
#             uri_file = datos['uri'].lstrip('./')
#             data=self.call_api(
#                     bearer_token,
#                     f"{self.URL}{uri_file}",
#                     method="GET"
#                     )
            
#             output_file = Path(f"{path}{datos['name']}")
#             output_file.parent.mkdir(exist_ok=True, parents=True)
#             output_file.write_text(data) 
#             #ruta_completa = os.path.join(path, datos['name'])
#             #print(ruta_completa)
#             #with open(ruta_completa, 'w') as archivo:
#             #    archivo.write(data)
#             print(f"Archivo {datos['name']} descargado exitosamente.")
#             return output_file
        
#     def createNewSpect_api(self,api_yaml,type_design,author,namedesign,design_id):
#         print("Creando Nuevo Spect api")
#         subprocess.run([f"{self.fullignitepath}/scripts/import-openapi-spec.sh",api_yaml,type_design,author,"false",namedesign, design_id])

#     def get_jobid(self, openapi_spec):
#         jobpath = "tmp/started/"
#         basename = os.path.basename(openapi_spec)
#         jobfile = jobpath + basename.split(".")[0] + ".json"

#         with open(f"{jobfile}") as f:
#             data = json.load(f)
#         #print(data["id"])
#         job_ignite_id = data["id"]

#         return job_ignite_id
    
#     def get_job_detail(self, jobid):
#         bearer_token = self.get_bearer_token()
#         while True:
#             data = self.call_api(
#                 bearer_token,
#                     f"{self.URL}rest/v2/jobs/{jobid}",
#                     "GET")
#             if data["jobSteps"][0]["state"] == "COMPLETED":
#                 break
#             if data["jobSteps"][0]["state"] == "ERRORED":
#                 break
#             else:
#                 print(f'esperando respuesta')
#                 time.sleep(5)
#         data=subprocess.run([f"{self.fullignitepath}/scripts/get-job-detail.sh",str(jobid)],capture_output=True, text=True).stdout.strip()
#         spect_id = json.loads(data)
#         return spect_id["resources"][1]["identifier"]
    
#     def update_spect_id(self,spec_id,version,enviroment):
#         code = ""
#         if enviroment == "quality":
#             code = "Test"
#         elif enviroment == "production":
#             code = "Production"
#         elif enviroment == "development":
#             code = "Development"

#         disposition_data = {
#             "type": "Lifecycle",
#             "pathName": code,
#             "name": code,
#             "description": "A Type",
#             "visualStyle": "{\"transitions\": [{\"action\": \"basic\",  \"state\":\"design\"},{\"action\": \"basic\",  \"state\":\"development\"},{\"action\": \"basic\",  \"state\":\"archived\"}]}",
#             "code": code.lower()
#         }
#         bearer_token = self.get_bearer_token()
#         spec_data = self.call_api(
#                 bearer_token,
#                     f"{self.URL}rest/v2/specifications/{spec_id}?expanded=false",
#                     "GET"
#         )
#         spec_data["version"] = version
#         spec_data["disposition"] = disposition_data
#         self.call_api(
#             bearer_token,
#             f"{self.URL}rest/v2/specifications/{spec_id}?expanded=false",
#             "PUT",
#             json_data=spec_data,
#             )
