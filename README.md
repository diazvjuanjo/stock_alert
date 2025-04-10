🔔 Sistema de Alerta de Stock

Este proyecto automatiza la vigilancia de cambios en el stock de productos. Compara diariamente un archivo .xlsx actualizado vía FTP y genera alertas cuando detecta:

Referencias que han pasado de tener stock a 0 (agotado)

Referencias que han pasado de 0 a tener stock (nuevo stock)

Cuando se detectan cambios, se genera un Excel con los detalles y se envía por email automáticamente.

¿Cómo funciona?

GitHub Actions ejecuta diariamente el script app.py.

El script:

Descarga el archivo actualizado desde una URL pública.

Compara los datos con el stock del día anterior.

Detecta cambios y los marca en una columna CAMBIO_STOCK.

Si hay cambios, genera un Excel y lo envía por email.

El archivo de stock de hoy se guarda como base para la comparación de mañana.

Todo queda registrado en la pestaña Actions de GitHub:

Archivos de alerta (alerta_stock_YYYY-MM-DD.xlsx)

Histórico de stock (stock_anterior.xlsx)

🛠 Requisitos

Secrets (en GitHub → Settings → Secrets and variables → Actions)

URL_FTP: URL del archivo .xlsx actualizado diariamente.

EMAIL_SENDER: Cuenta de Gmail remitente (con verificación en 2 pasos).

EMAIL_RECEIVER: Dirección de correo que recibirá las alertas.

EMAIL_PASSWORD: Contraseña de aplicación de Gmail.

Dependencias

Declaradas en requirements.txt:

pandas
openpyxl
requests
python-dotenv

🗕 Frecuencia de ejecución

El workflow está configurado para ejecutarse cada día a las 06:30 UTC (08:30 en España), y también se puede lanzar manualmente desde la pestaña Actions.

📂 Estructura

├── app.py                    # Script principal
├── requirements.txt
├── .github
│   └── workflows
│       └── alerta_stock.yml # Workflow de GitHub Actions

✅ Notas

El primer día no se realiza comparación porque no existe un stock anterior.

Si no se detectan cambios, no se envía ningún email ni se genera archivo de alerta.

Puedes ver o descargar los archivos generados en la pestaña Actions > Artifacts.

🧠 Mantenimiento

Si no recibes emails durante varios días, revisa los últimos runs en Actions.

Puedes forzar un envío modificando temporalmente la condición if num_agotados + num_nuevos > 0 a if True, pero no se recomienda en producción.

Si necesitas cambiar la hora, modifica la expresión cron en el archivo alerta_stock.yml.

