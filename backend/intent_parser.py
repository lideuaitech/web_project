import re


class IntentParser:

    def __init__(self, question):

        self.question = question.lower()

    # =========================
    # OPERATION DETECTION
    # =========================

    def detect_operation(self):

        q = self.question

        # =========================
        # SHOW / ROW REQUESTS
        # =========================

        if any(
            w in q
            for w in [
                "show",
                "display",
                "list",
                "rows",
                "top rows",
                "top 5 rows",
                "first rows",
                "first 5 rows",
                "last rows",
                "last 10 rows"
            ]
        ):
            return "show"

        # =========================
        # SUMMARY
        # =========================

        if "summary" in q:
            return "summary"

        # =========================
        # MEAN
        # =========================

        if any(
            w in q
            for w in [
                "average",
                "mean",
                "avg"
            ]
        ):
            return "mean"

        # =========================
        # SUM
        # =========================

        if any(
            w in q
            for w in [
                "sum",
                "total",
                "overall"
            ]
        ):
            return "sum"

        # =========================
        # MAX
        # =========================

        if any(
            w in q
            for w in [
                "max",
                "highest",
                "best",
                "largest"
            ]
        ):
            return "max"

        # =========================
        # MIN
        # =========================

        if any(
            w in q
            for w in [
                "min",
                "lowest",
                "bottom",
                "worst",
                "smallest"
            ]
        ):
            return "min"

        # =========================
        # COUNT
        # =========================

        if any(
            w in q
            for w in [
                "count",
                "how many"
            ]
        ):
            return "count"

        return None
    # =========================
    # CHART DETECTION
    # =========================

    def detect_chart(self):

        q = self.question

        chart_words = [
            "chart",
            "graph",
            "plot",
            "trend",
            "distribution",
            "compare",
            "comparison",
            "visualize",
            "dashboard"
        ]

        # explicit chart request only
        if any(
            w in q
            for w in chart_words
        ):
            return True

        return False

        # auto chart for grouped analytics
        if " by " in q:
            return True

        return False

    # =========================
    # LIMIT DETECTION
    # =========================

    def detect_limit(self):

        q = self.question

        match = re.search(
            r"(top|bottom|first|last)\s+(\d+)",
            q
        )

        if match:
            return int(match.group(2))

        return None
    
    # =========================
    # OFFSET DETECTION
    # =========================

    def detect_offset(self):

        q = self.question

        # rows 6 to 12
        match = re.search(
            r"(\d+)\s*(to|-)\s*(\d+)",
            q
        )

        if match:

            start = int(match.group(1))

            end = int(match.group(3))

            return {
                "start": start,
                "end": end
            }

        return None

    # =========================
    # SORT DETECTION
    # =========================

    def detect_sort(self):

        q = self.question

        if (
            "top rows" not in q
            and "top 5 rows" not in q
        ):

            if any(
                w in q
                for w in [
                    "top",
                    "highest",
                    "largest",
                    "best"
                ]
            ):

                return "desc"

        if any(
            w in q
            for w in [
                "lowest",
                "smallest",
                "bottom",
                "worst"
            ]
        ):
            return "asc"

        return None

    # =========================
    # FILTER DETECTION
    # =========================

    def detect_filters(self):

        q = self.question

        filters = []

        patterns = [
            r"where (.+)",
            r"for (.+)",
            r"in (.+)"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                q
            )

            if match:

                value = match.group(1).strip()

                filters.append(value)

        return filters

    # =========================
    # FINAL PARSE
    # =========================

    def parse(self):

        return {

            "question":
                self.question,

            "operation":
                self.detect_operation(),

            "chart":
                self.detect_chart(),

            "limit":
                self.detect_limit(),

            "offset":
                self.detect_offset(),

            "sort":
                self.detect_sort(),

            "filters":
                self.detect_filters()
        }