import pandas as pd


class ExecutionEngine:

    def __init__(self, df, parsed, entities):

        self.df = df
        self.parsed = parsed
        self.entities = entities

    def execute(self):

        df = self.df.copy()

        operation = self.parsed.get("operation")

        value_col = self.entities.get("value_column")

        group_by = self.entities.get("group_by")

        # =========================
        # AUTO DETECT VALUE COLUMN
        # =========================

        if value_col is None or str(value_col) == "nan":

            numeric_cols = df.select_dtypes(
                include="number"
            ).columns.tolist()

            ignore_cols = [
                "orders",
                "customers",
                "id"
            ]

            numeric_cols = [
                col for col in numeric_cols
                if col.lower() not in ignore_cols
            ]

            if numeric_cols:
                value_col = numeric_cols[0]

            else:
                return pd.DataFrame({
                    "Result": [
                        "No numeric column found"
                    ]
                })

        print("FINAL VALUE COL:", value_col)

        # =========================
        # APPLY FILTER
        # =========================

        filter_obj = self.entities.get("filter")

        if filter_obj:

            filter_col = filter_obj["column"]

            filter_value = filter_obj["value"]

            df = df[
                df[filter_col]
                .astype(str)
                .str.lower()
                ==
                str(filter_value).lower()
            ]

        # =========================
        # AUTO DETECT OPERATION
        # =========================

        question = str(
            self.parsed.get("question", "")
        ).lower()
        print("QUESTION:", question)
        print("OPERATION:", operation)

        if operation is None:

            if any(
                word in question
                for word in [
                    "average",
                    "avg",
                    "mean"
                ]
            ):
                operation = "mean"

            elif any(
                word in question
                for word in [
                    "highest",
                    "maximum",
                    "max",
                    "top",
                    "best"
                ]
            ):
                operation = "max"

            elif any(
                word in question
                for word in [
                    "lowest",
                    "minimum",
                    "min",
                    "worst"
                ]
            ):
                operation = "min"

            elif any(
                word in question
                for word in [
                    "count",
                    "how many",
                    "total rows"
                ]
            ):
                operation = "count"

            else:
                operation = "sum"

        result = None

        # =========================
        # SHOW DATA
        # =========================

        if operation == "show":

            question = self.parsed.get(
                "question",
                ""
            ).lower()

            limit = self.parsed.get("limit")

            offset = self.parsed.get("offset")

            # =========================
            # LAST ROWS
            # =========================

            if "last" in question:

                if limit:
                    return df.tail(limit)

                return df.tail(5)

            # =========================
            # RANGE ROWS
            # =========================

            if offset:

                start = offset["start"]

                end = offset["end"]

                return df.iloc[
                    start - 1:end
                ]

            # =========================
            # TOP/FIRST ROWS
            # =========================

            if limit:

                return df.head(limit)

            return df.head(50)

        # =========================
        # SUMMARY
        # =========================

        if operation == "summary":

            numeric_cols = (
                df.select_dtypes(include="number")
                .columns.tolist()
            )

            summary_rows = []

            for col in numeric_cols:

                summary_rows.append([
                    col,
                    round(df[col].sum(), 2),
                    round(df[col].mean(), 2),
                    round(df[col].max(), 2),
                    round(df[col].min(), 2)
                ])

            return pd.DataFrame(
                summary_rows,
                columns=[
                    "Column",
                    "Total",
                    "Average",
                    "Max",
                    "Min"
                ]
            )
        # =========================
        # COUNT
        # =========================

        if operation == "count":

            if group_by:

                result = (
                    df.groupby(group_by)
                    .size()
                    .reset_index(name="count")
                )

            else:

                result = pd.DataFrame({
                    "count": [len(df)]
                })

        # =========================
        # GROUP BY
        # =========================

        elif group_by and value_col:

            grouped = df.groupby(group_by)[value_col]

            if operation == "sum":
                result = grouped.sum()

            elif operation == "mean":
                result = grouped.mean()

            elif operation == "max":
                result = grouped.max()

            elif operation == "min":
                result = grouped.min()

            result = result.reset_index()

        # =========================
        # SIMPLE AGGREGATION
        # =========================

        else:

            if operation == "sum":

                result = pd.DataFrame({
                    value_col: [df[value_col].sum()]
                })

            elif operation == "mean":

                result = pd.DataFrame({
                    value_col: [df[value_col].mean()]
                })

            elif operation == "max":

                result = pd.DataFrame({
                    value_col: [df[value_col].max()]
                })

            elif operation == "min":

                result = pd.DataFrame({
                    value_col: [df[value_col].min()]
                })

        # =========================
        # SORTING
        # =========================

        if result is not None and len(result.columns) > 1:

            metric_col = result.columns[-1]

            # AUTO SORT FOR TOP/BEST
            if any(
                word in question
                for word in [
                    "top",
                    "highest",
                    "best"
                ]
            ):

                result = result.sort_values(
                    metric_col,
                    ascending=False
                )

            # AUTO SORT FOR LOWEST
            elif any(
                word in question
                for word in [
                    "lowest",
                    "worst"
                ]
            ):

                result = result.sort_values(
                    metric_col,
                    ascending=True
                )

            # MANUAL SORT
            elif self.parsed.get("sort"):

                ascending = (
                    self.parsed["sort"] == "asc"
                )

                result = result.sort_values(
                    metric_col,
                    ascending=ascending
                )

        # =========================
        # LIMIT
        # =========================

        limit = self.parsed.get("limit")

        if limit and result is not None:

            result = result.head(limit)

        # =========================
        # EMPTY RESULT
        # =========================

        if result is None or result.empty:

            return pd.DataFrame({
                "Result": [
                    "No matching data"
                ]
            })

        return result