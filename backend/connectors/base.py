class BaseConnector:
    
    def connect(self):
        raise NotImplementedError

    def test(self):
        raise NotImplementedError

    def fetch_schema(self):
        raise NotImplementedError

    def run_query(self, query: str):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError