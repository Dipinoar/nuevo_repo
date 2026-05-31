from vars.Awsrest import Awsrequest
import yaml
import tarfile
import subprocess

def main():
    with open("detail_vars.yaml", "r") as varsEnvironmentyaml:
        varsDeploy =  yaml.safe_load(varsEnvironmentyaml)
    secrets = Awsrequest()
    ruta = './'
    nombre_archivo_tar = f"{varsDeploy['nameProduct']}-{varsDeploy['versionProduct']}.tar"
    
    # Lista de archivos a excluir
    archivos_excluir = ['detail_vars.yaml','.gitlab-ci.yml','digitalml.zip','README.md']
    # Lista de carpetas a excluir
    carpetas_excluir = ['pipe','.git','ignite','CICD']

    def excluir_elementos(tarinfo):
        if tarinfo.name in archivos_excluir:
            return None
        if tarinfo.isdir() and tarinfo.name in carpetas_excluir:
            return None
        return tarinfo
    with tarfile.open(nombre_archivo_tar, 'w') as tar:
        tar.add(ruta, arcname='', filter=excluir_elementos)

    loginjf = secrets.getSecretNoSts('jfrog-credentials')

    jf_url = "https://artifactory.itauchile.cl"
    jf_user=loginjf['username']
    jf_pass=loginjf['password']
    token=loginjf['token']
    pathjf=f"{varsDeploy['jfPath']}/{varsDeploy['organizacion']}/{varsDeploy['catalogo']}/{varsDeploy['nameProduct']}/{varsDeploy['versionProduct']}"
    namefile=f"{varsDeploy['nameProduct']}-{varsDeploy['versionProduct']}.tar"
    # Comando para agregar las credenciales de Artifactory
    add_credentials_cmd = ['jfrog', 'c', 'add', '--url='+jf_url,'--access-token=' + token, '--interactive=false']
    print(add_credentials_cmd)

    # Comando para descargar el archivo desde Artifactory
    upload_cmd = ['jfrog', 'rt', 'u',namefile, pathjf + '/' + namefile, '--recursive=false']
    print(upload_cmd)
    # Ejecutar el comando para agregar las credenciales
    subprocess.run(add_credentials_cmd, check=True)

    # Ejecutar el comando para descargar el archivo
    subprocess.run(upload_cmd, check=True)
if __name__ == "__main__":
    main()