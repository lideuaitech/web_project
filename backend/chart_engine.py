import pandas as pd


class ChartEngine:

    def __init__(self, df):

        self.df = df.copy()

    # =========================
    # DETECT CHART TYPE
    # =========================

    def detect_chart_type(self):

        first_col = str(
            self.df.columns[0]
        ).lower()

        row_count = len(self.df)

        # ===== TIME SERIES =====

        time_words = [
            "date",
            "month",
            "year",
            "day",
            "time"
        ]

        if any(
            word in first_col
            for word in time_words
        ):
            return "line"

        # ===== PIE CHART =====

        category_words = [
            "category",
            "segment",
            "type",
            "region"
        ]

        if any(
            word in first_col
            for word in category_words
        ):

            if row_count <= 6:
                return "pie"

        # ===== SMALL DATA =====

        if row_count <= 12:
            return "bar"

        # ===== LARGE DATA =====

        return "line"

    # =========================
    # SAFE NUMBER CONVERSION
    # =========================

    def clean_number(self, value):

        try:

            if pd.isna(value):
                return 0

            return round(float(value), 2)

        except:
            return 0

    # =========================
    # BUILD CHART RESPONSE
    # =========================

    def build(self):

        # ===== EMPTY DATA =====

        if self.df.empty:

            return {
                "type": "text",
                "answer": "No data found"
            }

        # ===== SINGLE VALUE =====

        if len(self.df.columns) == 1:

            value = self.clean_number(
                self.df.iloc[0, 0]
            )

            return {
                "type": "chart",
                "chart_type": "bar",
                "labels": ["Result"],
                "values": [value],
                "summary":
                    f"Result value is {value}"
            }

        # =========================
        # NORMAL CHART
        # =========================

        metric_col = self.df.columns[-1]

        # ===== SORT =====

        self.df = self.df.sort_values(
            metric_col,
            ascending=False
        )

        # ===== LIMIT =====

        self.df = self.df.head(15)

        # ===== LABELS =====

        labels = (
            self.df.iloc[:, 0]
            .astype(str)
            .tolist()
        )

        # ===== VALUES =====

        raw_values = (
            self.df.iloc[:, 1]
            .tolist()
        )

        values = [
            self.clean_number(v)
            for v in raw_values
        ]

        # ===== SUMMARY =====

        top_label = labels[0]
        top_value = values[0]

        summary = (
            f"{top_label} has the highest "
            f"value of {top_value}"
        )

        return {

            "type": "chart",

            "chart_type":
                self.detect_chart_type(),

            "labels": labels,

            "values": values,

            "summary": summary
        }