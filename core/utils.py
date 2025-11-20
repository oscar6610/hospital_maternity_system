def validar_run(run_completo: str) -> bool:
    """
    Valida RUN/RUT chileno con formato XXXXXXXX-D
    Retorna True si es válido, False si no.
    """
    run_completo = run_completo.replace(".", "").replace("-", "").lower()

    if len(run_completo) < 2:
        return False

    cuerpo = run_completo[:-1]
    dv_ingresado = run_completo[-1]

    if not cuerpo.isdigit():
        return False

    reversed_digits = map(int, reversed(cuerpo))
    factors = [2, 3, 4, 5, 6, 7]
    suma = 0
    factor_index = 0

    for d in reversed_digits:
        suma += d * factors[factor_index]
        factor_index = (factor_index + 1) % len(factors)

    dv_calculado = 11 - (suma % 11)

    if dv_calculado == 11:
        dv_calculado = '0'
    elif dv_calculado == 10:
        dv_calculado = 'k'
    else:
        dv_calculado = str(dv_calculado)

    return dv_ingresado == dv_calculado
