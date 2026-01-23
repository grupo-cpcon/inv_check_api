from app.core.database import MongoConnection


def get_connection(db_name: str):
    client = MongoConnection.get_client()
    return client.get_database(db_name)