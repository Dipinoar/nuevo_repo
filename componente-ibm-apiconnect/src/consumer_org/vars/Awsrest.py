import requests
import json
import boto3
import re
from vars.Formatted import Formatfunc

class Awsrequest:
    def __init__(self,varenvironment):
        self.vars=varenvironment
        var=""

    def getSecret(self,ada,adr):
        session = boto3.Session()
        secretsmanager_client = session.client('secretsmanager')
        sts_client = session.client('sts')
        response = sts_client.assume_role(
            RoleArn=f'arn:aws:iam::{ada}:role/{adr}',
            RoleSessionName='AssumeRoleSession'
        )
        credentials = response['Credentials']
        assumed_session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken']
        )
        assumed_secretsmanager_client = assumed_session.client('secretsmanager')
        secret_name = 'usr_apiconnectv10pipeline'
        response = assumed_secretsmanager_client.get_secret_value(SecretId=secret_name)
        secret_values = json.loads(response['SecretString'])
        result_dict = {}  # Diccionario para almacenar los valores del secreto
        for key, value in secret_values.items():
            result_dict[key] = value  # Agregar el par clave-valor al diccionario
        return result_dict

    def Createsecretaws(self,keys):
        sts_client = boto3.client('sts')
        assumed_role_object=sts_client.assume_role(
            RoleArn="arn:aws:iam::"+str(self.vars['aws_da'])+":role/"+self.vars['aws_dr']+"",
            RoleSessionName="AssumeRoleSession1"
        )
        region_name = self.vars['region'] 
        secret_name = self.vars['secretrefix']+self.vars['organizacion']+"/"+self.vars['catalogo']+"/"+self.vars['nombreAPP']
        
        credentials=assumed_role_object['Credentials']
        secret_values = {
                "clientsecret": f"{keys['client_secret']}",
                "clientid": f"{keys['client_id']}"
                        }
        session = boto3.Session(
            aws_access_key_id=credentials['AccessKeyId'],
            aws_secret_access_key=credentials['SecretAccessKey'],
            aws_session_token=credentials['SessionToken'],
            region_name=region_name
        )
        client = session.client('secretsmanager')
        response = client.create_secret(
            Name=secret_name,
            SecretString=json.dumps(secret_values),
            KmsKeyId='alias/kms-secretsmanager'
        )
        with open('config_files/app/'+self.vars['policyfile']) as f:
            policy = json.load(f)
        responsepolicy = client.put_resource_policy(
            SecretId=secret_name,
            ResourcePolicy=json.dumps(policy)
        )
        return response