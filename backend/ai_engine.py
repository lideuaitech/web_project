from intent_parser import IntentParser
from entity_resolver import EntityResolver
from execution_engine import ExecutionEngine
from chart_engine import ChartEngine
from response_builder import ResponseBuilder
from insight_generator import InsightGenerator


class AIEngine:

    def __init__(self, df):

        self.df = df

    def run(self, question):

        # =========================
        # STEP 1 → PARSE INTENT
        # =========================

        parser = IntentParser(question)

        parsed = parser.parse()

        # =========================
        # STEP 2 → RESOLVE ENTITIES
        # =========================

        resolver = EntityResolver(
            self.df,
            question
        )

        entities = resolver.resolve()

        # =========================
        # STEP 3 → EXECUTE
        # =========================

        executor = ExecutionEngine(
            self.df,
            parsed,
            entities
        )

        result = executor.execute()

        # =========================
        # NO RESULT
        # =========================

        if result is None:

            return {
                "type": "table",
                "data": [],
                "summary": "No results found"
            }

        # =========================
        # GENERATE INSIGHT
        # =========================

        insight = InsightGenerator(result)

        summary = insight.generate()

        # =========================
        # CHART RESPONSE
        # =========================

        if parsed.get("chart") and len(result.columns) > 1:

            chart_engine = ChartEngine(result)

            chart_response = chart_engine.build()

            chart_response["summary"] = summary

            return chart_response

        # =========================
        # SINGLE VALUE RESPONSE
        # =========================

        if (
            len(result.columns) == 1
            and len(result) == 1
        ):

            value = result.iloc[0, 0]

            column = result.columns[0]

            operation = parsed.get(
                "operation",
                ""
            )

            if operation == "sum":

                text = f"Total {column} is {value}"

            elif operation == "mean":

                text = f"Average {column} is {round(value, 2)}"

            elif operation == "max":

                text = f"Highest {column} is {value}"

            elif operation == "min":

                text = f"Lowest {column} is {value}"

            elif operation == "count":

                text = f"Total count is {value}"

            else:

                text = f"{column} is {value}"

            return {
                "type": "text",
                "answer": text,
                "summary": summary
            }

        # =========================
        # TABLE RESPONSE
        # =========================

        response = ResponseBuilder.table(
            result,
            summary
        )

        return response