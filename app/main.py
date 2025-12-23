from MyDbConnection import MyDbConnection
from unittest.mock import patch
import os

URI = os.getenv('MONGO_URI', 'mongodb://admin:adminpassword@localhost:27017/dbDevOps?authSource=admin')
DB_NAME = os.getenv('DB_NAME', 'dbDevOps')
COLLECTION = os.getenv('COLLECTION_NAME', 'studenti')

def main():
    connection = MyDbConnection(URI, DB_NAME)
    connection.connect()

    collection = connection.get_result(collection_name=COLLECTION)

    matricola = "12345" #input("inserire il numero di matricola: ")
    document = collection.find_one({'matricola': matricola})
    
    if document:
        print(f"Matricola: {matricola} trovata!")
        print(f"Nome: {document.get('nome', 'N/A')}")
        print(f"Cognome: {document.get('cognome', 'N/A')}")
        print(f"Corso: {document.get('corso', 'N/A')}")
    else:
        print("Nessun match trovato")

    connection.disconnect()


if __name__ == "__main__":
    # Usa 'test' come input di default per i test automatici
    with patch('builtins.input', return_value="test"):
        main()