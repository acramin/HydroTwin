from math import isnan

# utils para normalização e conversão de dados
def to_float(valor):
	if valor is None:
		return None

	try:
		numero = float(valor)
	except (TypeError, ValueError):
		return None

	if isnan(numero):
		return None

	return numero

## utils de formatação de data e hora
from datetime import datetime, timedelta
def formatar_data(dth):
    if not isinstance(dth, datetime):
        dth = datetime.strptime(dth, "%Y-%m-%d %H:%M:%S")
    if not dth:
        return "N/A"
    return dth.strftime("%d/%m/%Y %H:%M:%S")

def formatar_data_filete(dth):
    if not isinstance(dth, datetime):
        dth = datetime.strptime(dth, "%Y-%m-%d")
    if not dth:
        return "N/A"
    return dth.strftime("%d/%m/%Y")