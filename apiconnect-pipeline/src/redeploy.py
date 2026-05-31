
import sys
import yaml
from vars.Formatted import Formatfunc
from vars.Functions import Processfunc
from vars.Apicrest import Apicrequest
from vars.Awsrest import Awsrequest


def load_yaml(file_path):
    try:
        print(f'leyendo el archivo {file_path}')
        with open(file_path, 'r') as yaml_file:
            return yaml.safe_load(yaml_file)
    except FileNotFoundError:
        print(f"Info: No se encontro el archivo {file_path} validar el tipo de instalacion, el archivo subsOldVersion.yaml no existira si es primera version ")
        return None


def main(config_paths, login_api_data):
    path_varsEnvi, path_varsDeploy, path_varsSubs, directorio_busqueda = config_paths
    connvar = load_yaml(path_varsEnvi)
    varsDeploy = load_yaml(path_varsDeploy)
    varsSubs = load_yaml(path_varsSubs)
    secrets = Awsrequest()
    apirqs = Apicrequest(varsDeploy)
    filevars = Formatfunc()
    process = Processfunc()

    try:
        loginApi = login_api_data
        # Obtener el token de API
        loginApi = secrets.getSecret(
            connvar["environment"]["production"]["aws_da"],
            connvar["environment"]["production"]["aws_dr"],
            "usr_apiconnectv10pipeline",
        )
        apirqs.getToken(loginApi)
        environment = varsDeploy["environment"]
        process.replaceConfigFiles(environment, directorio_busqueda, varsDeploy)
        SubsListCatalog = apirqs.getSubscriptionByCatalog()
        OldVersion = {
            "name": varsDeploy["nameProduct"],
            "version": varsDeploy["versionProduct"],
        }
        listOldSubs = process.subsFromOldVersion(
            SubsListCatalog, OldVersion, environment
        )
        listSubsMerge = process.combineSubscription(varsSubs, listOldSubs, environment)
        print(f'Buscando para eliminar el Producto a Reinstalar...')
        apirqs.deleteProduct(varsDeploy["nameProduct"], varsDeploy["versionProduct"])
        deployResult = apirqs.ejecutar_comando_api(loginApi)
        deployResult = 0
        if deployResult == 0:
            if listSubsMerge is not None:
                print(f"Suscribiendo a las siguientes Aplicaciones")
                for item in listSubsMerge:
                    print(item)  # Debe mostrar en pantalla si se suscribe correctamente
                    apirqs.createSubscription(item)
            else:
                print(f"No existen subscripciones")
        else:
            print("Existe un error al desplegar")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    config_paths = (
        "CICD/resources/varenvironment.yaml",
        "detail_vars.yaml",
        "configSubs.yaml",
        ".",
    )
    login_api_data = ""
    main(config_paths, login_api_data)
