import json

class detail():
    print("Detail")
    with open("development_detail.txt", "r") as archivo:
        desacontenido = archivo.read()
    with open("quality_detail.txt", "r") as archivo:
        qacontenido = archivo.read()
    with open("production_detail.txt", "r") as archivo:
        prodcontenido = archivo.read()

    print('****** Detalle desa ******')
    datosdesa = json.loads(desacontenido)
    texto = "Organizacion Consumo: {}\nSecret Key: {}\nClient Key: {}\nARN Name: {}\nARN Path: {}".format(
    datosdesa['consumerOrg'], datosdesa['secretKey'], datosdesa['clientKey'], datosdesa['arnName'], datosdesa['arnPath']
    )
    print(texto)


    print('****** Detalle qa ******')
    datosqa = json.loads(qacontenido)
    texto = "Organizacion Consumo: {}\nClient Key: {}\nARN Name: {}\nARN Path: {}".format(
    datosqa['consumerOrg'], datosqa['clientKey'], datosqa['arnName'], datosqa['arnPath']
    )
    print(texto)
    
    print('****** Detalle PROD ******')
    datosqa = json.loads(prodcontenido)
    texto = "Organizacion Consumo: {}\nClient Key: {}\nARN Name: {}\nARN Path: {}".format(
    datosqa['consumerOrg'], datosqa['clientKey'], datosqa['arnName'], datosqa['arnPath']
    )
    print(texto)

    with open("development_detail.txt", "w") as archivo:
        archivo.write("")
    with open("quality_detail.txt", "w") as archivo:
        archivo.write("")
    with open("production_detail.txt", "w") as archivo:
        archivo.write("")