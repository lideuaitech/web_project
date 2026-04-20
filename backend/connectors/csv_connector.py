from .base import BaseConnector
import pandas as pd
from schema_extractor import SchemaExtractor


class CSVConnector(BaseConnector):

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None

    def connect(self):
        try:
            if self.file_path.endswith(".csv"):
                self.df = pd.read_csv(self.file_path)

            elif self.file_path.endswith(".xlsx"):
                self.df = pd.read_excel(self.file_path)

            else:
                raise Exception("Unsupported file format")

            return True

        except Exception as e:
            print("Connection error:", e)
            return False

    def test(self):
        return self.df is not None

    def fetch_schema(self):
        extractor = SchemaExtractor(self.df)
        return extractor.extract()

    def run_query(self, question=None):
        if self.df is None:
            return {"error": "No data loaded"}

        if not question:
            return self.df.head(5).to_dict(orient="records")

        return {"message": "Use AI engine for queries"}

    def disconnect(self):
        self.df = None
