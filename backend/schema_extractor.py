class SchemaExtractor:

    def __init__(self, df):
        self.df = df

    def extract(self):
        schema = []

        for col in self.df.columns:
            column_data = self.df[col]

            schema.append({
                "column": col,
                "type": str(column_data.dtype),
                "nulls": int(column_data.isnull().sum()),
                "sample_values": column_data.dropna().unique().tolist()[:3]
            })

        return schema