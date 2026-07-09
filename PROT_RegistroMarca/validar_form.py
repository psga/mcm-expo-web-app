import re

def val_reg(nombre, nit, correo, telefono, patrocinador, codigo):
    errores = []

    # Nombre de la marca
    if nombre.strip() == "":
        errores.append("Debe ingresar el nombre de la marca.")

    # NIT


    if nit.strip() == "":
        errores.append("Debe ingresar el NIT de la empresa.")
    else:
        patron_nit = r'^\d{8}-\d$'

        if not re.match(patron_nit, nit):
            errores.append("El NIT no es válido.")

    # Correo
    patron_correo = r'^[\w\.-]+@[\w\.-]+\.\w+$'

    if correo.strip() == "":
        errores.append("Debe ingresar un correo electrónico.")
    elif not re.match(patron_correo, correo):
        errores.append("El correo electrónico no es válido.")

    # Teléfono
    if telefono.strip() == "":
        errores.append("Debe ingresar un teléfono.")
    elif not telefono.isdigit():
        errores.append("El teléfono solo debe contener números.")
    elif len(telefono) != 10:
        errores.append("El teléfono debe tener 10 dígitos.")

    # Código de patrocinio
    if patrocinador == "Sí":

        if codigo.strip() == "":
            errores.append("Debe ingresar el código de patrocinio.")

    return errores