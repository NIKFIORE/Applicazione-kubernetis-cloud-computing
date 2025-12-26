# Servizio Python con MongoDB – Deployment Kubernetes

Applicazione Python che esegue operazioni **CRUD (Create, Read, Update, Delete)** su un database **MongoDB**, deployata su **Kubernetes** utilizzando tre modalità:

* **Imperativa**
* **Dichiarativa (YAML)**
* **Kustomize**

L'applicazione si connette al database, esegue una singola interrogazione di lettura e termina la propria esecuzione.

---

## Prerequisiti

- Docker Engine 20.10+
- Kubernetes (Minikube o cluster equivalente)
- kubectl
- (Opzionale) Kustomize integrato in kubectl
- Accesso a GitHub nella VM remota (per deployment dell'applicazione)

---

## Architettura

L'applicazione è composta da:

* **App Python**
  * Container che si connette a MongoDB
  * Esegue una query di lettura e termina
* **MongoDB**
  * Database NoSQL
  * Inizializzato tramite script `init-mongo.js`
* **ConfigMap**
  * Contiene lo script di inizializzazione del database
* **PersistentVolumeClaim**
  * Garantisce la persistenza dei dati MongoDB
* **Service Kubernetes**
  * Espone MongoDB all'interno del cluster

---

## Struttura del Progetto

```
.
├── app/
│   ├── Dockerfile                  # Immagine Docker dell'applicazione Python
│   ├── requirements.txt            # Dipendenze Python
│   ├── MyDbConnection.py           # Classe per la connessione a MongoDB
│   ├── main.py                     # Script principale dell'applicazione
│   └── init-mongo.js               # Script di inizializzazione del database MongoDB
│
├── k8s/
│   ├── declarative/
│   │   ├── app-deployment.yaml     # Deployment dell'applicazione Python
│   │   ├── mongodb-deployment.yaml # Deployment MongoDB
│   │   ├── mongodb-service.yaml    # Service MongoDB
│   │   ├── mongodb-pvc.yaml        # PersistentVolumeClaim per MongoDB
│   │   └── mongodb-init-configmap.yaml # ConfigMap per init-mongo.js
│   │
│   ├── imperative/
│   │   └── commands.txt            # Comandi kubectl per la modalità imperativa
│   │
│   └── kustomize/
│       ├── base/
│       │   ├── app.yaml             # Risorse base applicazione Python
│       │   ├── mongodb.yaml         # Risorse base MongoDB
│       │   ├── mongodb-init-configmap.yaml # ConfigMap per inizializzazione DB
│       │   ├── pvc.yaml             # Volume persistente MongoDB
│       │   └── kustomization.yaml   # Kustomization base
│       │
│       └── overlay/
│           └── limits/
│               └── kustomization.yaml # Overlay con limiti CPU e RAM
│
└── README.md                        # Documentazione del progetto
```

---

## Deployment su VM Remota

### 1. Ottenere Token GitHub

1. Effettuare login in GitHub
2. Vai su **Settings** (foto profilo in alto a destra)
3. Scorri fino a **Developer settings** nel menu laterale
4. Clicca su **Personal access tokens** → **Tokens (classic)**
5. Clicca **"Generate new token (classic)"**
6. Configura il token:
   - Nome: es. "VM Token"
   - Durata: es. 90 giorni
   - Permessi necessari:
     - `repo`
     - `read:user`
7. Clicca **Generate token**
8. **Copia subito il token** (non sarà più visibile)

### 2. Clonare la Repository sulla VM

```bash
# Connettiti alla VM e clona la repository
git clone <LINK_REPOSITORY>

# Inserisci:
# - Username: tuo username GitHub
# - Password: il token generato al punto 1

# Entra nella directory del progetto
cd <nome-repository>
```

---

## Inizializzazione del Database

Il database MongoDB viene inizializzato automaticamente tramite lo script `init-mongo.js`, che viene montato nel container MongoDB nel percorso `/docker-entrypoint-initdb.d/`.

Lo script crea il database `dbDevOps` con la collection `studenti`, popolata con dati di test.

### Dati di Test Iniziali

| Matricola | Nome  | Cognome | Corso                      |
|-----------|-------|---------|----------------------------|
| test      | Mario | Rossi   | Ingegneria Informatica     |
| 12345     | Luigi | Verdi   | Informatica                |
| 67890     | Anna  | Bianchi | Ingegneria del Software    |

---

## Modalità Imperativa

La modalità imperativa utilizza comandi `kubectl` diretti per creare le risorse Kubernetes.

### Esecuzione

```bash
# 1. Navigazione nella directory del progetto
cd <nome-repository>

# 2. Build immagine Docker
docker build -t python-app:latest app/

# 3. Caricamento immagine in Minikube
minikube image load python-app:latest

# 4. Creazione deployment MongoDB
kubectl create deployment mongodb --image=mongo:7.0

# 5. Esposizione servizio MongoDB
kubectl expose deployment mongodb \
  --port=27017 \
  --name=mongodb

# 6. Configurazione variabili ambiente MongoDB
kubectl set env deployment/mongodb \
  MONGO_INITDB_ROOT_USERNAME=admin \
  MONGO_INITDB_ROOT_PASSWORD=adminpassword

# 7. Creazione deployment applicazione Python
kubectl create deployment python-app --image=python-app:latest

# 8. Configurazione variabili ambiente applicazione Python
kubectl set env deployment/python-app \
  MONGO_URI=mongodb://admin:adminpassword@mongodb:27017/dbDevOps?authSource=admin \
  DB_NAME=dbDevOps \
  COLLECTION_NAME=studenti

# 9. Configurazione policy di pull dell'immagine
kubectl patch deployment python-app -p \
'{"spec":{"template":{"spec":{"containers":[{"name":"python-app","imagePullPolicy":"IfNotPresent"}]}}}}'

# 10. Riavvio deployment per applicare modifiche
kubectl rollout restart deployment python-app
```

---

### Inizializzazione Manuale del Database

**⚠️ Nota:** In modalità imperativa il database **non è inizializzato automaticamente**. È necessario inserire i dati manualmente:

```bash
# 11. Accesso interattivo a MongoDB
kubectl exec -it deployment/mongodb -- \
  mongosh -u admin -p adminpassword --authenticationDatabase admin

# 12. All'interno di mongosh, esegui:
use dbDevOps

db.studenti.insertMany([
  {
    matricola: "test",
    nome: "Mario",
    cognome: "Rossi",
    corso: "Ingegneria Informatica"
  },
  {
    matricola: "12345",
    nome: "Luigi",
    cognome: "Verdi",
    corso: "Informatica"
  },
  {
    matricola: "67890",
    nome: "Anna",
    cognome: "Bianchi",
    corso: "Ingegneria del Software"
  }
])

exit

# 13. Riavvio applicazione dopo inizializzazione database
kubectl rollout restart deployment python-app
```

---

### Verifica

```bash
# Verifica stato dei pods
kubectl get pods

# Visualizza logs dell'applicazione
kubectl logs deployment/python-app
```

**Output atteso:**

```text
Pinged your deployment. You successfully connected to MongoDB!
Matricola: 12345 trovata!
Nome: Luigi
Cognome: Verdi
Corso: Informatica
Disconnected successfully!
```

---

### Verifica Database (GET)

```bash
kubectl exec -it deployment/mongodb -- \
mongosh -u admin -p adminpassword \
--authenticationDatabase admin dbDevOps \
--eval "db.studenti.findOne({matricola: '12345'})"
```

---

### Pulizia

```bash
kubectl delete deployment python-app mongodb
kubectl delete service mongodb
```

---

## Modalità Dichiarativa (YAML)

La modalità dichiarativa utilizza file YAML per definire tutte le risorse Kubernetes.

### Esecuzione

```bash
# Build immagine Docker
docker build -t python-app:latest app/

# Caricamento immagine in Minikube
minikube image load python-app:latest

# Deploy di tutte le risorse
kubectl apply -f k8s/declarative/
```

Questa modalità crea:

* ConfigMap con `init-mongo.js`
* PersistentVolumeClaim per persistenza dati
* Deployment e Service MongoDB
* Deployment dell'applicazione Python

---

### Verifica

```bash
# Verifica stato risorse
kubectl get pods
kubectl get svc
kubectl get pvc

# Visualizza logs applicazione
kubectl logs deployment/python-app
```

**Output atteso:**

```text
Pinged your deployment. You successfully connected to MongoDB!
Matricola: 12345 trovata!
Nome: Luigi
Cognome: Verdi
Corso: Informatica
Disconnected successfully!
```

---

### Verifica Database (GET)

```bash
kubectl exec -it deployment/mongodb -- \
mongosh -u admin -p adminpassword \
--authenticationDatabase admin dbDevOps \
--eval "db.studenti.find().pretty()"
```

---

### Pulizia

```bash
kubectl delete -f k8s/declarative/
```

---

## Modalità Kustomize

Kustomize permette di gestire configurazioni Kubernetes in modo modulare, con una base comune e overlay per personalizzazioni.

### Deploy Base

```bash
# Build immagine Docker
docker build -t python-app:latest app/

# Caricamento immagine in Minikube
minikube image load python-app:latest

# Deploy configurazione base
kubectl apply -k k8s/kustomize/base/
```

---

### Deploy con Overlay (Limiti Aumentati)

```bash
# Deploy con limiti di risorse modificati
kubectl apply -k k8s/kustomize/overlay/limits/
```

Questa modalità applica patch che aumentano i limiti:
- **Python App**: CPU 0.3, RAM 300Mi
- **MongoDB**: CPU 0.6, RAM 600Mi

---

### Verifica

```bash
# Verifica stato risorse
kubectl get pods
kubectl get svc
kubectl get pvc

# Logs applicazione
kubectl logs deployment/python-app
```

**Output atteso:**

```text
Pinged your deployment. You successfully connected to MongoDB!
Matricola: 12345 trovata!
Nome: Luigi
Cognome: Verdi
Corso: Informatica
Disconnected successfully!
```

---

### Visualizza Config Generata (Dry Run)

```bash
# Visualizza YAML che verrebbe applicato (senza applicare)
kubectl kustomize k8s/kustomize/base/

# Visualizza overlay
kubectl kustomize k8s/kustomize/overlay/limits/
```

---

### Verifica Database

```bash
kubectl exec -it deployment/mongodb -- \
mongosh -u admin -p adminpassword \
--authenticationDatabase admin dbDevOps \
--eval "db.studenti.find().pretty()"
```

---

### Pulizia

```bash
kubectl delete -k k8s/kustomize/base/
# oppure
kubectl delete -k k8s/kustomize/overlay/limits/
```

---

## Operazioni CRUD sul Database

Oltre alla lettura automatica eseguita dall'applicazione, è possibile effettuare manualmente altre operazioni CRUD.

### CREATE - Inserire un Nuovo Studente

```bash
kubectl exec -it deployment/mongodb -- \
mongosh -u admin -p adminpassword \
--authenticationDatabase admin dbDevOps \
--eval "db.studenti.insertOne({
  matricola: '99999',
  nome: 'Paolo',
  cognome: 'Neri',
  corso: 'Data Science'
})"
```

---

### READ - Leggere Dati

**Visualizza tutti gli studenti:**

```bash
kubectl exec -it deployment/mongodb -- \
mongosh -u admin -p adminpassword \
--authenticationDatabase admin dbDevOps \
--eval "db.studenti.find().pretty()"
```

**Cerca studente specifico per matricola:**

```bash
kubectl exec -it deployment/mongodb -- \
mongosh -u admin -p adminpassword \
--authenticationDatabase admin dbDevOps \
--eval "db.studenti.findOne({matricola: '12345'})"
```

---

### UPDATE - Aggiornare Dati

**Aggiorna il corso di uno studente:**

```bash
kubectl exec -it deployment/mongodb -- \
mongosh -u admin -p adminpassword \
--authenticationDatabase admin dbDevOps \
--eval "db.studenti.updateOne(
  {matricola: '12345'},
  {\$set: {corso: 'Computer Science'}}
)"
```

---

### DELETE - Eliminare Dati

**Elimina uno studente specifico:**

```bash
kubectl exec -it deployment/mongodb -- \
mongosh -u admin -p adminpassword \
--authenticationDatabase admin dbDevOps \
--eval "db.studenti.deleteOne({matricola: '99999'})"
```

---

## Configurazione Risorse

### Limiti Base (Dichiarativa e Kustomize Base)

| Componente  | CPU Limit | RAM Limit | CPU Request | RAM Request |
|-------------|-----------|-----------|-------------|-------------|
| MongoDB     | 0.5       | 512Mi     | 0.25        | 256Mi       |
| Python App  | 0.25      | 256Mi     | 0.1         | 128Mi       |

### Limiti Overlay Kustomize

| Componente  | CPU Limit | RAM Limit |
|-------------|-----------|-----------|
| MongoDB     | 0.6       | 600Mi     |
| Python App  | 0.3       | 300Mi     |

Questi limiti sono stati calibrati in base a test di esecuzione. MongoDB richiede maggiori risorse per gestire query e persistenza dati, mentre l'applicazione Python necessita di risorse contenute poiché esegue una singola interrogazione e termina.

---

## Troubleshooting

### L'app non appare in `kubectl get pods`

Questo è **normale**! L'applicazione Python esegue il suo script e poi termina. Per verificare che abbia funzionato:

```bash
# Visualizza tutti i pods (anche quelli completati)
kubectl get pods --show-all

# Visualizza i logs dell'applicazione
kubectl logs deployment/python-app
```

L'output dovrebbe mostrare "Matricola: 12345 trovata!" e i dettagli dello studente.

---

### Il pod rimane in stato CrashLoopBackOff

Possibili cause:

1. **MongoDB non ancora pronto**: Attendi qualche secondo
2. **Immagine non caricata**: Verifica con `minikube image ls | grep python-app`
3. **Variabili ambiente errate**: Verifica con `kubectl describe pod <nome-pod>`

---

### Database vuoto in modalità imperativa

In modalità imperativa lo script `init-mongo.js` non viene eseguito automaticamente. Devi inserire i dati manualmente come descritto nella sezione "Inizializzazione Manuale del Database".

---

## Note Finali

* L'applicazione Python **non è un servizio persistente**: esegue una query e termina
* MongoDB utilizza **storage persistente** tramite PVC
* L'inizializzazione automatica del database funziona solo nelle modalità **dichiarativa** e **Kustomize**
* Il progetto dimostra l'uso comparativo di:
  * **kubectl imperativo** - comandi diretti
  * **kubectl dichiarativo** - file YAML
  * **Kustomize** - gestione modulare con base e overlay

---