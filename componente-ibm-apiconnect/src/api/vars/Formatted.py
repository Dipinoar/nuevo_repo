import json
import yaml

class Formatfunc:
    def __init__(self):
        vars=""

    def formater(self,varDeploy,namefile):
        filename=namefile
        with open(filename, 'w') as archivo:
            yaml.dump(varDeploy, archivo)
        print("Resultado guardado exitosamente en el archivo. ")

    def formatPayss(self,varDeploy,versionplansold):
        #print(json.dumps(varDeploy, indent=4))
        print(json.dumps(versionplansold, indent=4))
        url = 'https://' + varDeploy['urlmanager'] + '/api/catalogs/' + varDeploy['organizacion'] + '/' + varDeploy['catalogo'] + '/products/' + varDeploy['nameProduct'] + '/' + versionplansold['max_version']
        urlProdOld = {'product_url': url}
    #print(urlProdOld)
        results = []
        for plan_name in versionplansold["plan_names"]:
            source = plan_name
            target = "default-plan"
            if plan_name in varDeploy["plans"]["plans"]:
                target = plan_name
            results.append({"source": source, "target": target})
        output_variable = {"plans": results}
        payload = {
            "product_url": urlProdOld['product_url'],
            "plans": output_variable['plans']
        }
        return payload
