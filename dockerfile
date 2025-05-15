# Usa una imagen oficial de Python
FROM python:3.11-slim

# Variables de entorno para que flask no genere buffers y trabaje en modo producción
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Directorio de la app en el contenedor
WORKDIR /app

# Copia requirements.txt (debes crearlo con tus dependencias)
COPY requirements.txt .

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código
COPY . .

# Expone el puerto donde correrá Flask (por defecto 5000)
EXPOSE 5000

# Define la variable de entorno para flask app
ENV FLASK_APP=app.py

# Comando para ejecutar la app
CMD ["flask", "run", "--host=0.0.0.0"]
