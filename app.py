import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import datetime
import os
import ssl
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración desde GitHub Secrets o .env
URL_FTP = os.environ["URL_FTP"]
EMAIL_SENDER = os.environ["EMAIL_SENDER"]
EMAIL_RECEIVER = os.environ["EMAIL_RECEIVER"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]

# Rutas locales
LOCAL_PATH = "stock_actual.xlsx"
PREVIOUS_PATH = "../stock_anterior.xlsx"  # Se guarda y lee fuera del directorio de trabajo
OUTPUT_PATH = f"alerta_stock_{datetime.now().strftime('%Y-%m-%d')}.xlsx"


def descargar_archivo(url, destino):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Error al descargar el archivo: {response.status_code}")

    with open(destino, "wb") as f:
        f.write(response.content)

    df = pd.read_excel(destino)
    if df.empty:
        raise ValueError("El archivo descargado está vacío. Revisa la URL.")
    return df

def detectar_cambios(df_actual, df_anterior):
    stock_ayer = dict(zip(df_anterior["EAN_13"], df_anterior["STOCK"]))
    cambios = []

    for index, row in df_actual.iterrows():
        ean = row["EAN_13"]
        stock_hoy = row["STOCK"]
        stock_ayer_val = stock_ayer.get(ean, None)

        if stock_ayer_val is not None:
            if stock_ayer_val > 0 and stock_hoy == 0:
                cambios.append("AGOTADO")
            elif stock_ayer_val == 0 and stock_hoy > 0:
                cambios.append("NUEVO STOCK")
            else:
                cambios.append("")
        else:
            cambios.append("")

    df_actual["CAMBIO_STOCK"] = cambios
    return df_actual

def enviar_email(ruta_adjunto, num_agotados, num_nuevos):
    asunto = f"\U0001F4E6 Alerta Stock - {num_agotados} agotados, {num_nuevos} nuevos"
    cuerpo = "Adjunto encontrarás el informe de cambios de stock de hoy."

    em = EmailMessage()
    em['From'] = EMAIL_SENDER
    em['To'] = EMAIL_RECEIVER
    em['Subject'] = asunto
    em.set_content(cuerpo)

    with open(ruta_adjunto, 'rb') as f:
        em.add_attachment(f.read(), maintype='application', subtype='octet-stream', filename=os.path.basename(ruta_adjunto))

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
        smtp.send_message(em)

# === EJECUCIÓN ===
print("📥 Descargando archivo actual...")
df_actual = descargar_archivo(URL_FTP, LOCAL_PATH)

# Si no existe stock anterior, guardar el actual como base y terminar
if not os.path.exists(PREVIOUS_PATH):
    print("📦 No hay stock anterior. Guardando el actual como base.")
    df_actual.to_excel(PREVIOUS_PATH, index=False)
    exit()

print("📊 Comparando stock actual con stock anterior...")
df_anterior = pd.read_excel(PREVIOUS_PATH)
df_actual = detectar_cambios(df_actual, df_anterior)

# Mostrar resumen de cambios
print("🔍 Resumen de cambios detectados:")
print(df_actual["CAMBIO_STOCK"].value_counts())

# Guardar siempre el archivo de salida, aunque no se envíe
df_actual.to_excel(OUTPUT_PATH, index=False)

# Contar cambios
num_agotados = (df_actual["CAMBIO_STOCK"] == "AGOTADO").sum()
num_nuevos = (df_actual["CAMBIO_STOCK"] == "NUEVO STOCK").sum()

if num_agotados + num_nuevos > 0:
    print("💌 Se enviará el correo con el Excel adjunto.")
    print(f"Enviando desde: {EMAIL_SENDER} a: {EMAIL_RECEIVER}")
    enviar_email(OUTPUT_PATH, num_agotados, num_nuevos)
else:
    print("✅ No hay cambios en el stock. No se envía correo.")

# Guardar el archivo actual como base para la próxima comparación
df_actual.to_excel(PREVIOUS_PATH, index=False)
print("🗃️ Guardado como nuevo stock_anterior.xlsx")

