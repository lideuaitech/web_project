import psycopg2
from backend.connectors.base import BaseConnector


class PostgresConnector(BaseConnector):

    def __init__(self, host, database, user, password):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.conn = None

    def connect(self):
        self.conn = psycopg2.connect(
            host=self.host,
            database=self.database,
            user=self.user,
            password=self.password
        )
        return self.conn

    def test(self):
        try:
            self.connect()
            return True
        except Exception as e:
            return str(e)

    def fetch_schema(self):
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema='public'
        """)

        tables = cursor.fetchall()
        return tables

    def run_query(self, query: str):
        cursor = self.conn.cursor()
        cursor.execute(query)

        try:
            result = cursor.fetchall()
        except:
            result = []

        return result

    def disconnect(self):
        if self.conn:
            self.conn.close()