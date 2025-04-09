import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import datetime
import os
import ssl
from dotenv import load_dotenv  

# Cargar variables de entorno
load_dotenv()

# Configuración desde .env
URL_FTP = os.environ["URL_FTP"]
EMAIL_SENDER = os.environ["EMAIL_SENDER"]
EMAIL_RECEIVER = os.environ["EMAIL_RECEIVER"]
EMAIL_PASSWORD = os.environ["EMAIL_PASSWORD"]

# Rutas locales
LOCAL_PATH = "stock_actual.xlsx"
PREVIOUS_PATH = "stock_anterior.xlsx"
OUTPUT_PATH = f"alerta_stock_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

def descargar_archivo(url, destino):
    df = pd.read_excel(url)
    df.to_excel(destino, index=False)
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

# Descargar archivo actual
df_actual = descargar_archivo(URL_FTP, LOCAL_PATH)
if df_actual.empty:
    print("Archivo vacío. No se realiza ninguna acción.")
    exit()
    
if os.path.exists(PREVIOUS_PATH):
    df_anterior = pd.read_excel(PREVIOUS_PATH)
    df_actual = detectar_cambios(df_actual, df_anterior)

    # Contar cambios
    num_agotados = (df_actual["CAMBIO_STOCK"] == "AGOTADO").sum()
    num_nuevos = (df_actual["CAMBIO_STOCK"] == "NUEVO STOCK").sum()

    # Guardar alerta
    df_actual.to_excel(OUTPUT_PATH, index=False)

    # Enviar email si hay cambios
    if num_agotados + num_nuevos > 0:
        enviar_email(OUTPUT_PATH, num_agotados, num_nuevos)

# Guardar el archivo actual para la próxima ejecución
df_actual.to_excel(PREVIOUS_PATH, index=False)
