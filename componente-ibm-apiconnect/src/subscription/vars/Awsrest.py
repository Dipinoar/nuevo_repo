import json
import boto3
import yaml

class Awsrequest:
    def __init__(self):
        self.var=""

    def getSecret(self,ada,adr,namesecret):
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
        secret_name = namesecret
        result_dict = {}
        response = assumed_secretsmanager_client.get_secret_value(SecretId=secret_name)
        secret_values = json.loads(response['SecretString'])
        result_dict['secretname'] = namesecret
        result_dict['keys'] = {}
        # Agregar los pares clave-valor al diccionario 'keys'
        for key, value in secret_values.items():
            result_dict['keys'][key] = value
        yaml_data = yaml.dump(result_dict)
        data = yaml.safe_load(yaml_data)
        return data
    
    def getSecretNoSts(self, namesecret):
        session = boto3.Session()
        secretsmanager_client = session.client('secretsmanager')
        secret_name = namesecret
        response = secretsmanager_client.get_secret_value(SecretId=secret_name)
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
        with open('resources/'+self.vars['policyfile']) as f:
            policy = json.load(f)
        responsepolicy = client.put_resource_policy(
            SecretId=secret_name,
            ResourcePolicy=json.dumps(policy)
        )
        return response