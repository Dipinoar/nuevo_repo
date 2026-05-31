# from vars.Formatted import Formatfunc
# from vars.Apicrest import Apicrequest
# from vars.Awsrest import Awsrequest
# from vars.Apiignite import Ignitefunc
# from vars.Functions import Processfunc
# import os
# import yaml
# import json

# def main():
#     environment= os.environ.get('TARGET_BRANCH')
#     path_varsEnvi='CICD/resources/varenvironment.yaml'
#     path_varsDeploy='detail_vars.yaml'
#     path_varsSubs='configSubs.yaml'
#     directorio_busqueda = "."
#     with open(path_varsEnvi, 'r') as varyaml:
#         varsEnvi = yaml.safe_load(varyaml)
#     with open(path_varsDeploy, "r") as varsEnvironmentyaml:
#         varsDeploy =  yaml.safe_load(varsEnvironmentyaml)
#     with open(path_varsSubs, "r") as subsvars:
#         varsSubs = yaml.safe_load(subsvars)

#     secrets = Awsrequest()
#     loginIgnite = secrets.getSecretNoSts('repocreation-secrets')
#     process= Processfunc()
#     spectIgnite=Ignitefunc(loginIgnite)
#     print("******** Checking Ignite ******")
#     DESIGN_ID = os.environ.get('DESIGN_ID')

#     parseDI = json.loads(DESIGN_ID)
#     # Buscar Yaml de las Apis
#     if environment=="development":
#         process.buscarCompararApis(directorio_busqueda,loginIgnite,parseDI,"update")
#     if environment=="quality" or environment=="production":
#         detalle_api=process.obtener_detalles_api(directorio_busqueda)
#         for key, detalle in detalle_api.items():
#             print(key)
#             print(detalle)
#             spect_version_promote=spectIgnite.checkdesignFilterByVersion(parseDI[key],detalle['version'])
#             print(spect_version_promote)
#             spectIgnite.update_spect_id(spect_version_promote['SPEC_ID'],detalle['version'],environment)
    

# if __name__ == "__main__":
#     main()