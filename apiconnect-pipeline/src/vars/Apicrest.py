import requests
import urllib3
import json
import re
import subprocess
import sys

class Apicrequest:
    def __init__(self,varenvironment):
        self.vars=varenvironment
        self.disable_insecure_request_warning()
        self.getCredential()
        self.userLogin="usr_api_devops"
        
    def disable_insecure_request_warning(self):
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
    def getCredential(self):
        url = 'http://'+self.vars['urlmanager']+'/ui/credentials'
        headers = {'Content-Type': 'application/json'}
        response = requests.get(url, headers=headers, verify=False)
        credential=response.json()
        self.cred=credential

    def getToken(self,login):
        url = 'http://'+self.vars['urlmanager']+'/api/token' #variable URL
        headers = {'Content-Type': 'application/json'}
        payload = json.dumps({
            "username": login['keys']['apiUser'], #variable
            "password": login['keys']['apiPassword'], #variable
            "realm": self.vars['realm'], #variable
            "client_id": self.cred['client_id'],
            "client_secret": self.cred['client_secret'],
            "grant_type": "password"
            })
        response = requests.request("POST",url, headers=headers, data=payload, verify=False)
        token=response.json()
        self.token=token
    # no usado #
    def getConsumerOrgList(self,vars):
        datareturn = {}
        url = 'https://'+vars['urlmanager']+'/api/catalogs/'+vars['organizacion']+'/'+vars['catalogo']+'/consumer-orgs'#  URL,variables organizacion y catalogo
        print(url)
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        response = requests.request("get",url, headers=headers, verify=False)
        data=response.json()
        if response.status_code == 200:
            datareturn["result"]=data
            datareturn["status"]=response.status_code
            datareturn["check"]=True
        else:
            datareturn["result"]=data['message']
            if 'results' in data and data['results']:
                 datareturn["status"]=data['results']
            else:
                 datareturn["status"]="Sin Datos"
            datareturn["check"]=False
        return datareturn
    # no usado #
    def getConsumerOrgxName(self,vars):
        datareturn = {}
        
        url = 'https://'+vars['urlmanager']+'/api/consumer-orgs/'+vars['organizacion']+'/'+vars['catalogo']+'/'+vars['consumerOrg']#URL, variables organizacion, catalogo, nombre app
        
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        response = requests.request("get",url, headers=headers, verify=False)
        data=response.json()
        if response.status_code == 200:
            datareturn["result"]=data
            datareturn["status"]=response.status_code
            datareturn["check"]=True
        else:
            datareturn["result"]=data['message']
            if 'results' in data and data['results']:
                 datareturn["status"]=data['results']
            else:
                 datareturn["status"]="Sin Datos"
            datareturn["check"]=False
        return datareturn
    # no usado #
    def getUserDetail(self,vars):
        realmEdit = re.sub(r'^provider/', '', vars['realm'])
        userReplace=self.userLogin.replace('_','-')
        url = 'https://'+vars['urlmanager']+'/api/user-registries/'+vars['organizacion']+'/'+realmEdit+'/users/'+userReplace #URL, variables organizacion, catalogo, nombre app
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        response = requests.request("get",url, headers=headers, verify=False)
        data=response.json()
        return data
    # no usado #
    def getAppDetail(self,vars):
        datareturn = {}
        url = 'https://'+vars['urlmanager']+'/api/apps/'+vars['organizacion']+'/'+vars['catalogo']+'/'+vars['consumerOrg']+'/'+vars['nombreAPP']
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        response = requests.request("get",url, headers=headers, verify=False)
        data=response.json()
        if response.status_code == 200:
            datareturn["result"]=data
            datareturn["status"]=response.status_code
            datareturn["check"]=True
        else:
            datareturn["result"]=data['message']
            if 'results' in data and data['results']:
                 datareturn["status"]=data['results']
            else:
                 datareturn["status"]="Sin Datos"
            datareturn["check"]=False
        return datareturn
    # no usado #
    def createConsumerOrg(self,vars):
        userUrl=vars['url']
        url = 'https://'+vars['urlmanager']+'/api/catalogs/'+vars['organizacion']+'/'+vars['catalogo']+'/consumer-orgs'
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        payload = json.dumps({
            "name": vars['consumerOrg'],
            "owner_url": userUrl,
            "title": vars['consumerOrg']
            })
        response = requests.request("POST",url, headers=headers, data=payload, verify=False)
        result=response.json()
    # no usado #
    def createApp(self,vars):
        url = 'https://'+vars['urlmanager']+'/api/consumer-orgs/'+vars['organizacion']+'/'+vars['catalogo']+'/'+vars['consumerOrg']+"/apps"
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        payload = json.dumps({
            "name": vars['nombreAPP'],
            "summary": "aplicacion creada mediante automatizacion",
            "title": vars['tituloAPP']
            })
        response = requests.request("POST",url, headers=headers, data=payload, verify=False)
        result=response.json()
        return result
    # no usado #
    def getSubscriptionByCatalog(self):
        url = 'https://'+self.vars['urlmanager']+'/api/catalogs/'+self.vars['organizacion']+'/'+self.vars['catalogo']+'/subscriptions?fields=app,consumer_org,id,plan,plan_title,product,product_version,state,updated_at,url&expand=product,app,consumer_org'
        print(url)
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        response = requests.get(url, headers=headers, verify=False)
        result=response.json()
        status_code = response.status_code
        print(f"status :{status_code}")
        return result
    # no usado #
    def getAppByCatalog(self,vars):
        url = 'https://'+vars['urlmanager']+'/api/catalogs/'+vars['organizacion']+'/'+vars['catalogo']+'/apps?fields=consumer_org,credentials,id,lifecycle_state,lifecycle_state_pending,name,state,title,updated_at,url&expand=credentials,consumer_org'
        print(url)
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        response = requests.get(url, headers=headers, verify=False)
        result=response.json()
        status_code = response.status_code
        print(f"status :{status_code}")
        return result
    
    def getListProduct(self):
        url = 'https://'+self.vars['urlmanager']+'/api/catalogs/'+self.vars['organizacion']+'/'+self.vars['catalogo']+'/products/'+self.vars['nameProduct']
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        response = requests.get(url, headers=headers, verify=False)
        result=response.json()
        status_code = response.status_code
        print(f"status :{status_code}")
        return result
    
    def ejecutar_comando_api(self,login):
        print(f"Realizando el despliegue del producto {self.vars['nameProductyaml']} con Version {self.vars['versionProduct']}")
        comandos = [
        f"apic login --server {self.vars['urlmanager']} --username {login['keys']['apiUser']} --password {login['keys']['apiPassword']} --realm {self.vars['realm']}",
        f"apic products publish {self.vars['nameProductyaml']} --server {self.vars['urlmanager']} --org {self.vars['organizacion']} --catalog {self.vars['catalogo']} --debug"
        ]
        for comando in comandos:
            resultado = subprocess.run(comando, shell=True, capture_output=True, text=True)

            if resultado.returncode == 0:
                # El comando se ejecutó exitosamente
                salida = resultado.stdout
                #print("Salida del comando:")
                #print(salida)
            else:
                # Ocurrió un error al ejecutar el comando
                error = resultado.stderr
                print("Error al ejecutar el comando:")
                print(error)
                sys.exit(1)
        return resultado.returncode
    
    def setSupersed(self,payloadvars):
        url = 'https://'+self.vars['urlmanager']+'/api/catalogs/'+self.vars['organizacion']+'/'+self.vars['catalogo']+'/products/'+self.vars['nameProduct']+'/'+self.vars['versionProduct']+'/supersede'
        print(url)
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        payload = json.dumps(payloadvars)
        print(payload)
        response = requests.request("POST",url, headers=headers, data=payload, verify=False)
        result=response.json()
        print(result)
        return result
    
    def executeMigration(self,oldversion):
        url = 'https://'+self.vars['urlmanager']+'/api/catalogs/'+self.vars['organizacion']+'/'+self.vars['catalogo']+'/products/'+self.vars['nameProduct']+'/'+oldversion['max_version']+'/execute-migration-target'
        print(url)
        tokenAccess=self.token
        print(tokenAccess)
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        response = requests.request("POST",url, headers=headers, verify=False)
        print(response)
        result=response.json()
        status_code = response.status_code
        print(f"status :{status_code}")
        print(result)
        return result
    
    def createSubscription(self, subsVars,name=None,version=None):
        if name is not None:
            self.vars['nameProduct'] = name
        if version is not None:
            self.vars['versionProduct'] = version
        try:
            url = 'https://' + self.vars['urlmanager'] + '/api/apps/' + self.vars['organizacion'] + '/' + self.vars['catalogo'] + '/' + subsVars['consumerorg'] + '/' + subsVars['application'] + "/subscriptions"
            tokenAccess = self.token
            headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + tokenAccess['access_token']}
            payload = json.dumps({
                "product_url": f"https://{self.vars['urlmanager']}/api/catalogs/{self.vars['organizacion']}/{self.vars['catalogo']}/products/{self.vars['nameProduct']}/{self.vars['versionProduct']}",
                "plan": "default-plan"
            })
            #print(f"payload = {json.dumps(payload, indent=4)}")
            response = requests.request("POST", url, headers=headers, data=payload, verify=False)
            response.raise_for_status()  # Lanza una excepción si la solicitud no fue exitosa
            result = response.json()
            #print(f"list_version_product = {json.dumps(result, indent=4)}")
            status_code = response.status_code
            print(f"status_code = {status_code}")
            return result
        except requests.exceptions.RequestException as e:
            # Manejar errores de solicitud (puede ser Timeout, conexión fallida, etc.)
            print(f"Error de solicitud: {e}")
            return None  # O maneja el error de alguna otra manera según tu necesidad
        except json.JSONDecodeError as e:
            # Manejar errores de decodificación JSON si la respuesta no es válida JSON
            print(f"Error de decodificación JSON: {e}")
            return None  # O maneja el error de alguna otra manera según tu necesidad

    def updateProductStatus(self, name, version, dataupdate):
        url = 'https://'+self.vars['urlmanager']+'/api/catalogs/'+self.vars['organizacion']+'/'+self.vars['catalogo']+'/products/'+name+'/'+version
        print(url)
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        payload = json.dumps(dataupdate)
        response = requests.request("PATCH",url, headers=headers, data=payload, verify=False)
        result=response.json()
        return result
    
    def deleteProduct(self, name, version):
        print(f"Eliminando producto {name} version {version}")
        try:
            print("try eliminando")
            url = 'https://' + self.vars['urlmanager'] + '/api/catalogs/' + self.vars['organizacion'] + '/' + self.vars['catalogo'] + "/products/" + name + '/' + version
            tokenAccess = self.token
            headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + tokenAccess['access_token']}
            response = requests.request("DELETE", url, headers=headers, verify=False)
            print(f'{response}')
            result = response.json()
            print(f'{result}')
            response.raise_for_status()  # Lanza una excepción si la solicitud no fue exitosa
            result = response.json()
            status_code = response.status_code
            print(f'status_code = {status_code}')
            return result
        except requests.exceptions.RequestException as e:
            # Manejar errores de solicitud (puede ser Timeout, conexión fallida, etc.)
            if response.status_code == '404':
                print('Producto No encontrado para eliminar se procede a la instalacion')
            return None  # O maneja el error de alguna otra manera según tu necesidad
        except json.JSONDecodeError as e:
            # Manejar errores de decodificación JSON si la respuesta no es válida JSON
            print(f"Error de decodificación JSON: {e}")
            return None  # O maneja el error de alguna otra manera según tu necesidad