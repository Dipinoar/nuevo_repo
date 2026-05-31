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
        with open('config_files/app/varenvironment.yml', 'r') as varyaml:
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
            os.environ.get('Consumer_org')
            or os.environ.get('CONSUMER_ORG')
            or defaults.get('consumerOrg')
        )
        application_name = (
            os.environ.get('Nombre')
            or os.environ.get('APPLICATION')
            or defaults.get('application')
        )

        variableMap = {
            'environment': environment,
            'organizacion': organizacion,
            'catalogo': catalogo,
            'consumerOrg': consumer_org_name,
            'nombreAPP': application_name,
            'tituloAPP': application_name,
            'urlmanager': connvar['environment'][environment]['urlmanager'],
            'realm': connvar['environment'][environment]['realm'],
            'aws_da': connvar['environment'][environment]['aws_da'],
            'aws_dr': connvar['environment'][environment]['aws_dr'],
            'region': connvar['environment'][environment]['region'],
            'secretrefix': connvar['environment'][environment]['secretrefix'],
            'policyfile': connvar['environment'][environment]['policyfile']
        }
        validate_required_fields(variableMap,["environment", "organizacion", "catalogo", "consumerOrg", "nombreAPP", "tituloAPP"])

        print("**********************************")
        print("Ejecuccion Creacion Aplicaciones Apiconnect")
        print("Ambiente: " + variableMap['environment'])
        print("Organizacion: " + variableMap['organizacion'])
        print("Catalogo: " + variableMap['catalogo'])
        print("Organizacion Consumo: " + variableMap['consumerOrg'])
        print("Nombre APP: " + variableMap['nombreAPP'])

        print("**********************************")

        secrets = Awsrequest(variableMap)
        newappcreate = Apicrequest(variableMap)
        filevars = Formatfunc(variableMap)

        loginApi = secrets.getSecret(
            connvar['environment']['production']['aws_da'],
            connvar['environment']['production']['aws_dr']
        )
        print("Obteniendo Token")
        newappcreate.getToken(loginApi)

        print("***************Organizacion de Consumo Revision*******************")
        resultxname = newappcreate.getConsumerOrgxName()
        print(resultxname)


        if not resultxname['check']:
            print("***************Creando Organizacion de Consumo *******************")
            userdata = newappcreate.getUserDetail()
            print(userdata)
        
            resultcreateconsumerorg = newappcreate.createConsumerOrg(userdata)
            print(resultcreateconsumerorg)

        else:
            print("***************Encontrado, Detalle Organizacion de Consumo *******************")
            print(json.dumps(resultxname['result'], indent=4))
        print("***************Creacion de aplicacion *******************")
        resultGetApp = newappcreate.getAppDetail()
        if not resultGetApp['check']:
            print("***************Creando nueva aplicacion *******************")
            resultcreateapp = newappcreate.createApp()
            print("***************respuesta crear app *******************")
            if (resultcreateapp.status_code != 201):
                raise Exception("Error creacion de la app")
            
            resultCreateSecret = secrets.Createsecretaws(resultcreateapp.json())
            print("***************respuesta crear secreto*******************")
            
            fileResponse = filevars.formater(variableMap,resultcreateapp.json(),resultCreateSecret, write_result)
        else:
            print("***************Encontrado, Detalle Aplicacion *******************")
            print(json.dumps(resultGetApp['result'], indent=4))
            write_result(400, "La aplicacion ya existe.")
            raise Exception("Error creacion de la app")

        print("***********FIN CREACION *************")

    except ValueError as e:
        print(f"Error: {str(e)}")
        if "Ambiente no corresponde" in str(e):
            write_result(400, "Ambiente invalido")
            raise Exception("Error creacion de la app")
        elif "Uno o más valores no validos" in str(e):
            write_result(400, "Uno o mas valores no validos")
            raise Exception("Error creacion de la app")
        else:
            write_result(500, "Ocurrio un error")
            raise Exception("Error creacion de la app")
    except Exception as e:
        print(f"Error: {str(e)}")
        write_result(500, "Ocurrio un error")
        raise Exception("Error creacion de la capp")

if __name__ == "__main__":
    main()