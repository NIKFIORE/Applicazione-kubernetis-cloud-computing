from pymongo.mongo_client import MongoClient

class MyDbConnection:
    def __init__(self, uri, db_name):
        self.uri = uri
        self.db_name = db_name
        self.client = None
        self.db = None

    def connect(self):
        
        try:
            # Create a new client and connect to the server
            self.client = MongoClient(self.uri)
            # Send a ping to confirm a successful connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]

            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

    def disconnect(self):
        if self.client:
            self.client.close()
            print("Disconnected successfully!")
        else:
            print("Something went wrong during disconnection!")

    def get_result(self,collection_name):
        if self.db is None:
            return None
        else:
            return self.db[collection_name]