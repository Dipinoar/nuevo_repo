from vars.Formatted import Formatfunc
from vars.Apicrest import Apicrequest
from vars.Awsrest import Awsrequest
from common.RepoMetadata import get_consumer_defaults
from common.RepoMetadata import resolve_catalog_context
from common.Validation import check_environment
from common.Validation import validate_required_fields
from common.Output import write_result

import os
import yaml
import json

def main():
    try:
        with open('config_files/consumer_org/varenvironment.yml', 'r') as varyaml:
            connvar = yaml.safe_load(varyaml)

        # Validaciones
        environment = os.environ.get('envi') or os.environ.get('TARGET_BRANCH') or 'development'
        check_environment(environment)
        defaults = get_consumer_defaults(environment)
        organizacion, catalogo = resolve_catalog_context(
            os.environ.get('Organizacion') or os.environ.get('ORGANIZACION'),
            os.environ.get('Catalogo') or os.environ.get('CATALOGO')
        )
        consumer_org_name = (
            os.environ.get('Nombre')
            or os.environ.get('CONSUMER_ORG')
            or defaults.get('consumerOrg')
        )

        variableMap = {
            'environment': environment,
            'organizacion': organizacion,
            'catalogo': catalogo,
            'consumerOrg': consumer_org_name,
            'urlmanager': connvar['environment'][environment]['urlmanager'],
            'realm': connvar['environment'][environment]['realm'],
            'aws_da': connvar['environment'][environment]['aws_da'],
            'aws_dr': connvar['environment'][environment]['aws_dr'],
            'region': connvar['environment'][environment]['region'],
            'secretrefix': connvar['environment'][environment]['secretrefix'],
            'policyfile': connvar['environment'][environment]['policyfile']
        }
        validate_required_fields(variableMap,["environment", "organizacion", "catalogo", "consumerOrg"])

        print("**********************************")
        print("Ejecuccion Creacion Consumer Org Apiconnect")
        print("Ambiente: " + variableMap['environment'])
        print("Organizacion: " + variableMap['organizacion'])
        print("Catalogo: " + variableMap['catalogo'])
        print("Nombre ConsumerOrg: " + variableMap['consumerOrg'])

        print("**********************************")

        secrets = Awsrequest(variableMap)
        newconsumerorgcreate = Apicrequest(variableMap)
        filevars = Formatfunc(variableMap)

        loginApi = secrets.getSecret(
            connvar['environment']['production']['aws_da'],
            connvar['environment']['production']['aws_dr']
        )
        print("Obteniendo Token")
        newconsumerorgcreate.getToken(loginApi)

        print("***************Creando Organizacion de Consumo *******************")
        userdata = newconsumerorgcreate.getUserDetail()
        print(userdata)
    
        resultcreateconsumerorg = newconsumerorgcreate.createConsumerOrg(userdata)
        print(resultcreateconsumerorg)

        if (resultcreateconsumerorg.status_code != 201):
            raise Exception("Error creacion de la consumer org")

        print("***********FIN CREACION *************")

    except ValueError as e:
        print(f"Error: {str(e)}")
        if "Ambiente no corresponde" in str(e):
            write_result(400, "Ambiente invalido")
            raise Exception("Error creacion de la consumer org")
        elif "Uno o más valores no validos" in str(e):
            write_result(400, "Uno o mas valores no validos")
            raise Exception("Error creacion de la consumer org")
        else:
            write_result(500, "Ocurrio un error")
            raise Exception("Error creacion de la consumer org")
    except Exception as e:
        print(f"Error: {str(e)}")
        write_result(500, "Ocurrio un error")
        raise Exception("Error creacion de la consumer org")

if __name__ == "__main__":
    main()