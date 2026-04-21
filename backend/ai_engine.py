import pandas as pd


class AIEngine:

    def __init__(self, df, schema):
        self.df = df
        self.schema = schema

    # ================= MAIN ENTRY =================
    def run(self, question: str):
        q = question.lower()

        # 🔹 MOCK AI LOGIC (temporary until API key)
        if "average" in q or "mean" in q:
            return self.execute({
                "operation": "average",
                "column": self.find_column(q)
            })

        if "sum" in q or "total" in q:
            return self.execute({
                "operation": "sum",
                "column": self.find_column(q)
            })

        if "max" in q or "highest" in q:
            return self.execute({
                "operation": "max",
                "column": self.find_column(q)
            })

        if "min" in q or "lowest" in q:
            return self.execute({
                "operation": "min",
                "column": self.find_column(q)
            })

        if "count" in q:
            return self.execute({
                "operation": "count",
                "column": None
            })

        return {"error": "AI couldn't understand the question"}

    # ================= COLUMN DETECTION =================
    def find_column(self, question):
        # exact match
        for col in self.df.columns:
            if col.lower() in question:
                return col

        # partial match fallback
        for col in self.df.columns:
            for word in question.split():
                if word in col.lower():
                    return col

        return None

    # ================= SAFE EXECUTION =================
    def execute(self, parsed):
        op = parsed.get("operation")
        col = parsed.get("column")

        df = self.df

        # 🔹 COUNT
        if op == "count":
            return {"answer": len(df)}

        # ❌ column missing
        if not col:
            return {"error": "Column not found"}

        # ❌ column invalid
        if col not in df.columns:
            return {"error": f"Column '{col}' not found"}

        # ❌ non-numeric
        if df[col].dtype == "object":
            return {"error": f"Column '{col}' is not numeric"}

        # 🔹 OPERATIONS
        if op == "average":
            return {"answer": float(df[col].mean())}

        if op == "sum":
            return {"answer": float(df[col].sum())}

        if op == "max":
            return {"answer": float(df[col].max())}

        if op == "min":
            return {"answer": float(df[col].min())}

        return {"error": "Unknown operation"}
