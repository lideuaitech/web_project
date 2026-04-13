from .base import BaseConnector
import pandas as pd
from schema_extractor import SchemaExtractor

class CSVConnector(BaseConnector):
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.df = None

    def connect(self):
        try:
            # Detect file type
            if self.file_path.endswith(".csv"):
                if self.file_path.endswith(".csv"):
                    self.df = pd.read_csv(self.file_path)
                else:
                    self.df = pd.read_excel(self.file_path)            
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

        for col in self.df.columns:
            schema.append({
                "column": col,
                "type": str(self.df[col].dtype),
                "nulls": int(self.df[col].isnull().sum())
            })

        return schema

def run_query(self, question=None):
    if self.df is None:
        return {"error": "No data loaded"}

    if not question:
        return self.df.head(5).to_dict(orient="records")

    question = question.lower()

    try:
        # 🔥 smarter column match
        def find_column():
            for col in self.df.columns:
                if col.lower() in question:
                    return col

            # fallback: partial match
            for col in self.df.columns:
                for word in question.split():
                    if word in col.lower():
                        return col

            return None

        col = find_column()

        if not col:
            return {"error": "Column not found"}

        # ===== OPERATIONS =====
        if "average" in question or "mean" in question:
            return {col: float(self.df[col].mean())}

        if "max" in question:
            return {col: float(self.df[col].max())}

        if "min" in question:
            return {col: float(self.df[col].min())}

        if "sum" in question or "total" in question:
            return {col: float(self.df[col].sum())}

        return self.df.head(5).to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}

    question = question.lower()

    try:
        # ===== AVERAGE =====
        if "average" in question or "mean" in question:
            for col in self.df.columns:
                if col.lower() in question:
                    return {col: float(self.df[col].mean())}

        # ===== MAX =====
        if "max" in question:
            for col in self.df.columns:
                if col.lower() in question:
                    return {col: float(self.df[col].max())}

        # ===== MIN =====
        if "min" in question:
            for col in self.df.columns:
                if col.lower() in question:
                    return {col: float(self.df[col].min())}

        # ===== SUM =====
        if "total" in question or "sum" in question:
            for col in self.df.columns:
                if col.lower() in question:
                    return {col: float(self.df[col].sum())}

        # ===== DEFAULT =====
        return self.df.head(5).to_dict(orient="records")

    except Exception as e:
        return {"error": str(e)}
    def disconnect(self):
        self.df = None