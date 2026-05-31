import json
import yaml

class Formatfunc:
    def __init__(self,envirovars):
        vars=""

    def formater(self,varDeploy,responseapp,responseSecret, write_result):
        fileResponse={
            'consumerOrg': varDeploy['consumerOrg'],
            'secretKey': responseapp['client_secret'],
            'clientKey': responseapp['client_id'],
            'arnName': responseSecret['Name'],
            'arnPath': responseSecret['ARN']
        }
        write_result(code=200, result = fileResponse)