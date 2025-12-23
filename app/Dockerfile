# Usa un'immagine Python leggera
FROM python:3.11-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file requirements
COPY requirements.txt .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY MyDbConnection.py .
COPY main.py .

# Comando di default
CMD ["python", "main.py"]