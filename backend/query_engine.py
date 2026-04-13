class QueryEngine:

    def __init__(self, df):
        self.df = df

    def run(self, query: str):
        query = query.lower()

        # Average
        if "average" in query or "mean" in query:
            for col in self.df.columns:
                if self.df[col].dtype != "object":
                    return {col: float(self.df[col].mean())}

        # Count
        elif "count" in query:
            return {"count": len(self.df)}

        # Max
        elif "max" in query:
            for col in self.df.columns:
                if self.df[col].dtype != "object":
                    return {col: self.df[col].max()}

        # Min
        elif "min" in query:
            for col in self.df.columns:
                if self.df[col].dtype != "object":
                    return {col: self.df[col].min()}

        return {"message": "Query not understood"}