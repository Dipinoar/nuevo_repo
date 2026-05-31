from vars.Formatted import Formatfunc
from vars.Functions import Processfunc
from vars.Apicrest import Apicrequest
from vars.Awsrest import Awsrequest
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
    print("Obteniendo Token")
    apirqs.getToken(loginApi)
    #lista suscripciones del catalogo filtrado por producto
    listApps=apirqs.getAppByCatalog(varsDeploy)
    listSubs=apirqs.getSubscriptionByCatalog(varsDeploy)
    listFilessub = varsSubs['subscription']['environment']['development']#cambiaar por variable ambiente
    resultSubsCheck=process.checkSubFile(listFilessub,listSubs,listApps)
   
if __name__ == "__main__":
    main()
