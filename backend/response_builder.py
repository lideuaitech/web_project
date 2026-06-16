import json
import pandas as pd


class ResponseBuilder:

    @staticmethod
    def clean_data(records):

        cleaned = json.loads(
            json.dumps(
                records,
                default=str
            )
        )

        return cleaned

    @staticmethod
    def table(df, summary=None):

        df = df.fillna("")

        columns = df.columns.tolist()

        rows = df.values.tolist()

        rows = ResponseBuilder.clean_data(rows)

        return {
            "type": "table",
            "columns": columns,
            "rows": rows,
            "summary": summary
        }

    @staticmethod
    def chart(
        labels,
        values,
        chart_type,
        summary=None
    ):

        labels = ResponseBuilder.clean_data(labels)

        values = ResponseBuilder.clean_data(values)

        return {
            "type": "chart",
            "chart_type": chart_type,
            "labels": labels,
            "values": values,
            "summary": summary
        }