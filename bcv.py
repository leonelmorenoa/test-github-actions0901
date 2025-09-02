import requests, certifi
from bs4 import BeautifulSoup

URL = "https://www.bcv.org.ve/"
headers = {"User-Agent": "Mozilla/5.0"}

# Primer paso (tal como lo usas)
r = requests.get(URL, headers=headers, timeout=10, verify=False)
r.raise_for_status()
soup = BeautifulSoup(r.content, "lxml")

# --- Segundo paso: extraer datos y guardar CSV ---
from decimal import Decimal
from pathlib import Path
import pandas as pd

# 1) Extraer la tasa (texto dentro de #dolar strong)
node_tasa = soup.select_one('#dolar strong')
if node_tasa is None:
    raise ValueError("No se encontró el nodo de tasa: '#dolar strong'.")

raw_tasa = node_tasa.get_text(strip=True)
# Normaliza: elimina separadores de miles y convierte coma decimal a punto
norm_tasa = (raw_tasa
             .replace('\xa0', '')
             .replace(' ', '')
             .replace('.', '')
             .replace(',', '.'))
tasa = float(Decimal(norm_tasa))  # Decimal -> float para CSV

# 2) Extraer la fecha del atributo content del span.date-display-single (ISO 8601)
node_fecha = soup.select_one('span.date-display-single[content]')
if node_fecha is None or not node_fecha.has_attr('content'):
    raise ValueError("No se encontró la fecha en 'span.date-display-single[content]'.")

fecha = pd.to_datetime(node_fecha['content']).date()  # solo fecha (YYYY-MM-DD)

# 3) DataFrame y persistencia en CSV (append si existe, solo si es tasa nueva)
csv_path = Path("bcv_tasa_usd.csv")
nueva = pd.DataFrame([{"fecha": fecha, "tasa": tasa}])

if csv_path.exists():
    exist = pd.read_csv(csv_path, parse_dates=["fecha"])
    if not exist.empty:
        # Misma tasa que la última fila
        ultima_tasa = exist["tasa"].iloc[-1]
        mismo_ultimo = (ultima_tasa == tasa)

        # Ya existe una fila con misma fecha y misma tasa
        exist_fecha_date = exist["fecha"].dt.date
        existe_misma = ((exist_fecha_date == fecha) & (exist["tasa"] == tasa)).any()

        if mismo_ultimo or existe_misma:
            print("Sin cambios: tasa repetida, no se agrega fila.")
        else:
            nueva.to_csv(csv_path, index=False, mode="a", header=False)
            print("Fila agregada (tasa nueva).")
    else:
        # Archivo existe pero está vacío
        nueva.to_csv(csv_path, index=False)
        print("CSV creado con primera fila.")
else:
    # Primera vez: crea el archivo con encabezado
    nueva.to_csv(csv_path, index=False)
    print("CSV creado con primera fila.")
