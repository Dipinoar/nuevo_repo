from vars.Formatted import Formatfunc
from vars.Functions import Processfunc
from vars.Apicrest import Apicrequest
from vars.Awsrest import Awsrequest
import os
import yaml

def main():
    with open('CICD/resources/varenvironment.yaml', 'r') as varyaml:
        connvar = yaml.safe_load(varyaml)
    with open("detail_vars.yaml", "r") as varsEnvironmentyaml:
        varsDeploy =  yaml.safe_load(varsEnvironmentyaml)
    with open("configSubs.yaml", "r") as subsvars:
       varsSubs = yaml.safe_load(subsvars)
    
    secrets = Awsrequest()
    apirqs = Apicrequest(varsDeploy)
    filevars = Formatfunc()
    process= Processfunc()

    loginApi = secrets.getSecret(
        connvar['environment']['production']['aws_da'],
        connvar['environment']['production']['aws_dr'],
        'usr_apiconnectv10pipeline'
    )
    print('variables de ambiente')
    print(varsDeploy)
    print("Obteniendo Token")
    apirqs.getToken(loginApi)

    for root, dirs, files in os.walk('.'):
            for file in files:
                if file.endswith('.conf'):
                    archivo = os.path.join(root, file)
                    with open(archivo, 'r') as file:
                        contenido = file.read()
                        print(f'contenido config : {contenido}')

if __name__ == "__main__":
    main()
