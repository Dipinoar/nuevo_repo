def check_environment(environment):
    """
    Error si la variable no corresponde al ambiente 
    """
    valid_environments = {'development', 'quality', 'production'}
    if environment not in valid_environments:
        print(environment)
        raise ValueError("Ambiente no corresponde")
    return

def validate_required_fields(data: dict, required_fields: list):
    """
    Valida que las claves especificadas en el diccionario tengan valores no nulos

    Args:
        data: Diccionario con los datos a validar
        required_fields: Lista de claves que deben tener valores no nulos

    Raises:
        ValueError: Si algún campo requerido es nulo o no existe

    """
    missing_fields = []
    null_fields = []

    for field in required_fields:
        # Verificar si el campo existe en el diccionario
        if field not in data:
            missing_fields.append(field)
        # Verificar si el valor es None
        elif data[field] is None:
            null_fields.append(field)

    # Construir mensaje de error si hay problemas
    errors = []
    if missing_fields:
        errors.append(f"Campos faltantes: {', '.join(missing_fields)}")
    if null_fields:
        errors.append(f"Campos con valor nulo: {', '.join(null_fields)}")

    if errors:
        print("Uno o más valores no validos")
        print("; ".join(errors))
        raise ValueError("Uno o más valores no validoss")

    return 