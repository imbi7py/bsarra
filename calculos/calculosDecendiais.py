from datetime import date, timedelta
# Funcoes que facilitam a conversao de datas para o formato decendial


def inicioDecendio(data):
    if data.day < 11:
        dia = 1
    elif data.day < 21:
        dia = 11
    else:
        dia = 21

    return date(data.year, data.month, dia)


def converterToDataDecendio(data):
    if data.day < 11:
        decendio = 1
    elif data.day < 21:
        decendio = 2
    else:
        decendio = 3

    return (data.month, decendio)



def proximoDecendio(data):
    decendio = data[1]
    mes = data[0]

    decendio += 1
    if decendio > 3:
        decendio = 1
        mes += 1

        if mes > 12:
            mes = 1

    return (mes, decendio)


def diasNoDecendio(data):
    if data.day < 21:
        return 10
    else:
        data2 = data + timedelta(days=15)
        data2 = date(data2.year, data2.month, 1)
        return (data2 - date(data.year, data.month, 21)).days
