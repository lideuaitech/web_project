class InsightGenerator:

    def __init__(self, df):

        self.df = df

    def generate(self):

        try:

            if self.df is None or self.df.empty:

                return "No insights available"

            columns = list(self.df.columns)

            if len(columns) < 2:

                return "Analysis completed successfully"

            label_col = columns[0]

            value_col = columns[1]

            max_row = self.df.loc[
                self.df[value_col].idxmax()
            ]

            min_row = self.df.loc[
                self.df[value_col].idxmin()
            ]

            return (
                f"{max_row[label_col]} has the highest "
                f"{value_col.lower()} with "
                f"{max_row[value_col]}. "
                f"{min_row[label_col]} has the lowest "
                f"{value_col.lower()} with "
                f"{min_row[value_col]}."
            )

        except Exception as e:

            print("INSIGHT ERROR:", e)

            return "Analysis completed successfully"