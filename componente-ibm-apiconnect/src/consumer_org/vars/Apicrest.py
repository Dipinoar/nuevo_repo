import requests
import json
import boto3
import re
from vars.Formatted import Formatfunc

class Apicrequest:
    def __init__(self,varenvironment):
        self.vars=varenvironment
        self.getCredential()
        self.userLogin="usr_api_devops"
        

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
            "username": login['apiUser'], #variable
            "password": login['apiPassword'], #variable
            "realm": self.vars['realm'], #variable
            "client_id": self.cred['client_id'],
            "client_secret": self.cred['client_secret'],
            "grant_type": "password"
            })
        response = requests.request("POST",url, headers=headers, data=payload, verify=False)
        token=response.json()
        self.token=token

    def getConsumerOrgList(self):
        datareturn = {}
        url = 'http://{self.urlmanager}/api/catalogs/outer/sandbox/consumer-orgs'#  URL,variables organizacion y catalogo
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        response = requests.request("get",url, headers=headers, verify=False)
        if response.status_code == 200:
            data=response.json()
            datareturn["result"]=data['results']
            datareturn["status"]=True
        else:
            datareturn["result"]=data['results']
            datareturn["status"]=True
        return datareturn
    
    def getConsumerOrgxName(self):
        datareturn = {}
        
        url = 'https://'+self.vars['urlmanager']+'/api/consumer-orgs/'+self.vars['organizacion']+'/'+self.vars['catalogo']+'/'+self.vars['consumerOrg']#URL, variables organizacion, catalogo, nombre app
        
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
    
    def getUserDetail(self):
        realmEdit = re.sub(r'^provider/', '', self.vars['realm'])
        userReplace=self.userLogin.replace('_','-')
        url = 'https://'+self.vars['urlmanager']+'/api/user-registries/'+self.vars['organizacion']+'/'+realmEdit+'/users/'+userReplace #URL, variables organizacion, catalogo, nombre app
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        response = requests.request("get",url, headers=headers, verify=False)
        data=response.json()
        return data

    def getAppDetail(self):
        datareturn = {}
        url = 'https://'+self.vars['urlmanager']+'/api/apps/'+self.vars['organizacion']+'/'+self.vars['catalogo']+'/'+self.vars['consumerOrg']+'/'+self.vars['nombreAPP']
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
    
    def createConsumerOrg(self,userdata):
        userUrl=userdata['url']
        url = 'https://'+self.vars['urlmanager']+'/api/catalogs/'+self.vars['organizacion']+'/'+self.vars['catalogo']+'/consumer-orgs'
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        payload = json.dumps({
            "name": self.vars['consumerOrg'],
            "owner_url": userUrl,
            "title": self.vars['consumerOrg']
            })
        response = requests.request("POST",url, headers=headers, data=payload, verify=False)
        return response

    def createApp(self):
        url = 'https://'+self.vars['urlmanager']+'/api/consumer-orgs/'+self.vars['organizacion']+'/'+self.vars['catalogo']+'/'+self.vars['consumerOrg']+"/apps"
        tokenAccess=self.token
        headers = {'Content-Type': 'application/json','Authorization': 'Bearer ' + tokenAccess['access_token']}
        payload = json.dumps({
            "name": self.vars['nombreAPP'],
            "summary": "aplicacion creada mediante automatizacion",
            "title": self.vars['tituloAPP']
            })
        response = requests.request("POST",url, headers=headers, data=payload, verify=False)
        result=response.json()
        return result