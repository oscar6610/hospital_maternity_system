def validar_run(run_completo: str) -> bool:
    try:
        run = run_completo.lower().replace(".", "").replace("-", "")
        
        if len(run) < 2:
            return False
        
        cuerpo = run[:-1]
        dv_ingresado = run[-1]
        
        if not cuerpo.isdigit():
            return False
        
        suma = 0
        multiplicador = 2
        
        for d in reversed(cuerpo):
            suma += int(d) * multiplicador
            multiplicador = 2 if multiplicador == 7 else multiplicador + 1
        
        resto = suma % 11
        dv = 11 - resto
        
        if dv == 11:
            dv = "0"
        elif dv == 10:
            dv = "k"
        else:
            dv = str(dv)
        
        return dv_ingresado == dv
    except:
        return False



def normalizar_run(run: str) -> str:
    run_limpio = run.replace(".", "").replace("-", "").lower()

    if not validar_run(run_limpio):
        raise ValueError("RUN inválido, no se puede normalizar")

    return f"{run_limpio[:-1]}-{run_limpio[-1]}"

