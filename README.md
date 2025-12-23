# Servizio Python con MongoDB - Deployment Kubernetis

Applicazione Python che esegue delle operazioni CRUD su un database MongoDB, il tutto utilizzando container docker.

## Prerequisiti

- Docker Engine 20.10+
- Docker Compose 2.0+
- Accesso a GitHub nella VM remota (per deployment dell'applicazione)

## Architettura

L'applicazione è composta da:
- **App Python**: servizio che interroga il database MongoDB
- **MongoDB**: database NoSQL per memorizzare dati degli studenti
- **Network privata**: comunicazione sicura tra i container
- **Volume persistente**: storage dei dati MongoDB

### Caratteristiche Docker Compose

- **Volume gestito** (`mongodb_data`) per persistenza dati
- **Network virtuale** (`app_network`) per isolamento
- **Limiti risorse**: CPU e RAM configurati per entrambi i servizi
- **Healthcheck**: MongoDB ha controlli di salute configurati

## Struttura File

```
.
├── Dockerfile              # Immagine per l'app Python
├── docker-compose.yml      # Orchestrazione dei servizi
├── requirements.txt        # Dipendenze Python
├── MyDbConnection.py       # Classe per connessione MongoDB
├── main.py                 # Script principale
├── init-mongo.js          # Script inizializzazione database
└── README.md              
```

## Build e Deployment Locale

### 1. Avviare i servizi con Docker Compose

```bash
# Avvia tutti i servizi in background
docker-compose up -d --build

# Verifica lo stato dei container
docker-compose ps

# Visualizza i log
docker-compose logs -f
```

### 2. Comandi utili

```bash
# Fermare i servizi
docker-compose down

# Fermare e rimuovere anche i volumi (ATTENZIONE: cancella i dati)
docker-compose down -v
```

## Deployment su VM Remota

### 1. Preparare la VM

```bash
# Connettiti alla VM

# Verifica che Docker e Docker Compose siano installati
docker --version
docker-compose --version
```

### 2. Ottenere token

* Effettuare login in GitHub
* Ottenere link della repo (schermata principale code - HTTPS link)
* Ottenere token per autenticazione nella VM
* Vai su GitHub → in alto a destra clicca sulla tua foto → Settings
* Nel menu laterale, scorri giù fino a Developer settings
* Clicca su Personal access tokens → Tokens (classic)
* Clicca "Generate new token (classic)"
* Dai un nome (es. VM Token) e scegli una durata (es. 90 giorni)
* Seleziona i permessi minimi necessari:
  * repo
  * read:user
* Clicca Generate token
* Copia il token subito (non potrai più vederlo dopo)

### 3. Trasferire i file

```bash
# Dalla VM, clona la repository
git clone <link>
# Verranno chiesti successivamente USERNAME di git e PSW utilizza token precedentemente generato
```

### 4. Deploy sulla VM

```bash
# Sulla VM
cd app_cloud

# Build e avvio
docker-compose up -d --build

# Verifica lo stato
docker-compose ps
docker-compose logs
```

## Operazioni CRUD sul Database

Questa sezione mostra come eseguire operazioni CRUD (Create, Read, Update, Delete) direttamente sul database MongoDB.
L’applicazione non è concepita per rimanere in esecuzione permanente: viene avviata, stabilisce una connessione con il database, effettua una singola interrogazione e, una volta ottenuto il risultato, termina la propria esecuzione.

### CREATE - Inserire un Nuovo Studente

```bash
docker-compose exec mongodb mongosh -u admin -p adminpassword \
    --authenticationDatabase admin dbDevOps \
    --eval "db.studenti.insertOne({
        matricola: '99999',
        nome: 'Paolo',
        cognome: 'Neri',
        corso: 'Data Science'
    })"
```

### READ - Leggere Dati

**Visualizza tutti gli studenti:**
```bash
docker-compose exec mongodb mongosh -u admin -p adminpassword \
    --authenticationDatabase admin dbDevOps \
    --eval "db.studenti.find().pretty()"
```

**Cerca studente specifico per matricola:**
```bash
docker-compose exec mongodb mongosh -u admin -p adminpassword \
    --authenticationDatabase admin dbDevOps \
    --eval "db.studenti.findOne({matricola: 'test'})"
```

### UPDATE - Aggiornare Dati

**Aggiorna il corso di uno studente:**
```bash
docker-compose exec mongodb mongosh -u admin -p adminpassword \
    --authenticationDatabase admin dbDevOps \
    --eval "db.studenti.updateOne(
        {matricola: 'test'},
        {\$set: {corso: 'Computer Science'}}
    )"
```

### DELETE - Eliminare Dati

**Elimina uno studente specifico:**
```bash
docker-compose exec mongodb mongosh -u admin -p adminpassword \
    --authenticationDatabase admin dbDevOps \
    --eval "db.studenti.deleteOne({matricola: '99999'})"
```

## Configurazione

### Variabili d'Ambiente

Le seguenti variabili sono configurate in `docker-compose.yml`:

| Variabile | Valore | Descrizione |
|-----------|--------|-------------|
| `MONGO_URI` | `mongodb://admin:adminpassword@mongodb:27017/dbDevOps?authSource=admin` | URI connessione MongoDB |
| `DB_NAME` | `dbDevOps` | Nome del database |
| `COLLECTION_NAME` | `studenti` | Nome della collection |

### Limiti Risorse

**MongoDB:**
- CPU Limit: 0.5 core
- RAM Limit: 512 MB
- CPU Reservation: 0.25 core
- RAM Reservation: 256 MB

**App Python:**
- CPU Limit: 0.25 core
- RAM Limit: 256 MB
- CPU Reservation: 0.1 core
- RAM Reservation: 128 MB

Questi determinati limiti sono stati impostati **a seguito di test di esecuzione** e perchè imposto da consegna.
si è osservato che MongoDB richiede maggiori risorse per gestire le query e la persistenza dei dati, mentre l’app Python, eseguendo solo un’interrogazione e terminando subito dopo, necessita di risorse molto più contenute. Per questo motivo sono stati definiti valori equilibrati.


## Dati di Test

Il database viene inizializzato con i seguenti studenti:

- Matricola: `test` - Mario Rossi (Ingegneria Informatica)
- Matricola: `12345` - Luigi Verdi (Informatica)
- Matricola: `67890` - Anna Bianchi (Ingegneria del Software)

## Troubleshooting

### L'app non appare in docker-compose ps

Questo è **normale**! L'applicazione Python esegue il suo script e poi termina. Per verificare che abbia funzionato:

```bash
# Visualizza tutti i container (anche quelli terminati)
docker-compose ps -a

# Visualizza i log dell'applicazione
docker-compose logs app
```

L'output dovrebbe mostrare "Matricola: test trovata!" e i dettagli dello studente.

## Note

- Il database è accessibile solo attraverso la rete Docker (non esposto esternamente)
- I dati persistono nel volume `mongodb_data` anche dopo il riavvio dei container
- L'applicazione Python esegue il suo task e termina (non è un servizio continuo)