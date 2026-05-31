import json

def write_result(code: int, message: str = "", result: dict = {} , filename: str = "result.json"):
    """
    Escribe código y mensaje a un archivo JSON

    Args:
        code: Código de resultado entero
        message: Cadena de mensaje descriptivo
        filename: Nombre del archivo de salida (por defecto: result.json)
    """
    # Crear diccionario con los resultados
    output = {
        "code": code,
        "message": message,
        "result": result
    }

    # Escribir al archivo JSON
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)