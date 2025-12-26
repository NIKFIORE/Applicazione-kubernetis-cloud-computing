# Servizio Python con MongoDB – Deployment Kubernetes

Applicazione Python che esegue operazioni **CRUD (Create, Read, Update, Delete)** su un database **MongoDB**, deployata su **Kubernetes** utilizzando tre modalità:

* **Imperativa**
* **Dichiarativa (YAML)**
* **Kustomize**

L’applicazione si connette al database, esegue una singola interrogazione di lettura e termina la propria esecuzione.

---

## Prerequisiti

- Docker Engine 20.10+
- Kubernetes (Minikube o cluster equivalente)
- kubectl
- (Opzionale) Kustomize integrato in kubectl
- Accesso a GitHub nella VM remota (per deployment dell'applicazione)

---

## Architettura

L’applicazione è composta da:

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

  * Espone MongoDB e l’applicazione all’interno del cluster

---

## Struttura
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
│   │   ├── app-service.yaml        # Service dell'applicazione Python
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


## Deployment su VM Remota


### 1. Ottenere token

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

### 2. Trasferire i file

```bash
# Dalla VM, clona la repository
git clone <link>
# Verranno chiesti successivamente USERNAME di git e PSW utilizza token precedentemente generato
```

### 4. Deploy sulla VM

```bash
# Sulla VM
cd app_cloud
```

## Inizializzazione del Database

Il database MongoDB viene inizializzato automaticamente tramite lo script:

```
init-mongo.js
```

Lo script viene montato nel container MongoDB nel percorso:

```
/docker-entrypoint-initdb.d/
```

e crea il database `dbDevOps` con la collection `studenti`, popolata con dati di test.

---

## Dati di Test Iniziali

Il database viene inizializzato con i seguenti studenti:

* `test` – Mario Rossi (Ingegneria Informatica)
* `12345` – Luigi Verdi (Informatica)
* `67890` – Anna Bianchi (Ingegneria del Software)

---

## Modalità Imperativa

### Esecuzione

```bash
docker build -t python-app:latest app/
minikube image load python-app:latest
```

```bash
kubectl create deployment mongodb --image=mongo:7.0
kubectl expose deployment mongodb --port=27017 --name=mongodb
kubectl set env deployment/mongodb \
  MONGO_INITDB_ROOT_USERNAME=admin \
  MONGO_INITDB_ROOT_PASSWORD=adminpassword
```

```bash
kubectl create deployment python-app --image=python-app:latest
kubectl set env deployment/python-app \
  MONGO_URI=mongodb://admin:adminpassword@mongodb:27017/dbDevOps?authSource=admin \
  DB_NAME=dbDevOps \
  COLLECTION_NAME=studenti
```

---

### Verifica

```bash
kubectl get pods
kubectl logs deployment/python-app
```

In questa modalità il database **non è inizializzato automaticamente**, quindi la prima esecuzione non trova dati.

---

### Pulizia

```bash
kubectl delete deployment python-app mongodb
kubectl delete service python-app mongodb
```

---

## Modalità Dichiarativa (YAML)

### Esecuzione

```bash
kubectl apply -f k8s/declarative/
```

Questa modalità crea:

* ConfigMap con `init-mongo.js`
* PersistentVolumeClaim
* Deployment e Service MongoDB
* Deployment e Service dell’applicazione Python

---

### Verifica

```bash
kubectl get pods
kubectl get svc
kubectl get pvc
```

```bash
kubectl logs deployment/python-app
```

Output atteso (esempio):

```text
Matricola: 12345 trovata!
Nome: Luigi
Cognome: Verdi
Corso: Informatica
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
kubectl delete -f k8s/declarative/
```

---

## Modalità Kustomize

### Build immagine applicazione

```bash
docker build -t python-app:latest app/
```

---

### Deployment

```bash
kubectl apply -k k8s/kustomize/overlay/limits
```

Questa modalità utilizza:

* Base YAML comuni
* Overlay per limiti di CPU e RAM
* ConfigMap per inizializzazione database
* PersistentVolumeClaim

---

### Verifica

```bash
kubectl get pods
kubectl get svc
kubectl get pvc
```

```bash
kubectl logs deployment/python-app
```

Output atteso:

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
kubectl delete -k k8s/kustomize/overlay/limits
```

---

## Note Finali

* L’applicazione Python **non è un servizio persistente**: esegue una query e termina
* MongoDB utilizza **storage persistente**
* L’inizializzazione del database replica il comportamento di Docker Compose
* Il progetto dimostra l’uso comparativo di:

  * kubectl imperativo
  * kubectl dichiarativo
  * Kustomize

---

