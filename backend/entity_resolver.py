from difflib import get_close_matches
import pandas as pd


class EntityResolver:

    def __init__(self, df, question):

        self.df = df
        self.question = question.lower()

        self.columns = df.columns.tolist()

    # =========================
    # FIND NUMERIC COLUMN
    # =========================

    def resolve_value_column(self):

        numeric_cols = self.df.select_dtypes(
            include="number"
        ).columns.tolist()

        # exact match
        for col in numeric_cols:

            if col.lower() in self.question:
                return col

        # fuzzy match
        words = self.question.split()

        for word in words:

            matches = get_close_matches(
                word,
                numeric_cols,
                n=1,
                cutoff=0.6
            )

            if matches:
                return matches[0]

        return None

    # =========================
    # FIND GROUP BY COLUMN
    # =========================

    def resolve_groupby(self):

        # =========================
        # AUTO TIME GROUPING
        # =========================

        if any(
            word in self.question
            for word in [
                "trend",
                "growth",
                "over time"
            ]
        ):

            for col in self.columns:

                col_lower = col.lower()

                if any(
                    word in col_lower
                    for word in [
                        "date",
                        "month",
                        "year",
                        "day",
                        "time"
                    ]
                ):

                    return col

        # =========================
        # AUTO DISTRIBUTION
        # =========================

        if any(
            word in self.question
            for word in [
                "distribution",
                "breakdown",
                "composition"
            ]
        ):

            categorical_cols = [
                col for col in self.columns
                if self.df[col].dtype == "object"
            ]

            priority_words = [
                "customer",
                "category",
                "segment",
                "region",
                "type"
            ]

            for word in priority_words:

                for col in categorical_cols:

                    if word in col.lower():
                        return col

            if categorical_cols:
                return categorical_cols[0]

        # =========================
        # NORMAL BY LOGIC
        # =========================

        if "by" not in self.question:
            return None

        after_by = (
            self.question
            .split("by")[-1]
            .strip()
        )

        # exact + partial match
        for col in self.columns:

            col_clean = (
                col.lower().strip()
            )

            if after_by == col_clean:
                return col

            if after_by in col_clean:
                return col

        # fuzzy match
        matches = get_close_matches(
            after_by,
            [
                c.lower().strip()
                for c in self.columns
            ],
            n=1,
            cutoff=0.5
        )

        if matches:

            matched = matches[0]

            for col in self.columns:

                if (
                    col.lower().strip()
                    == matched
                ):
                    return col

        return None

    # =========================
    # FILTER RESOLUTION
    # =========================

    def resolve_filter(self):

        q = self.question.lower()

        if "where" not in q:
            return None

        condition = (
            q.split("where")[-1]
            .strip()
        )

        words = condition.split()

        for col in self.columns:

            col_lower = col.lower()

            if col_lower in condition:

                idx = words.index(col_lower)

                remaining = words[idx + 1:]

                remaining = [
                    w for w in remaining
                    if w not in [
                        "is",
                        "=",
                        "equals"
                    ]
                ]

                if remaining:

                    value = remaining[0]

                    return {
                        "column": col,
                        "value": value.capitalize()
                    }

        return None

    # =========================
    # MAIN RESOLVE
    # =========================

    def resolve(self):

        return {

            "value_column":
                self.resolve_value_column(),

            "group_by":
                self.resolve_groupby(),

            "filter":
                self.resolve_filter()
        }