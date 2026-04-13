from openai import OpenAI
import pandas as pd

client = OpenAI(api_key="YOUR_API_KEY")  # replace later

class AIEngine:

    def __init__(self, df):
        self.df = df

    def run(self, question: str):

        prompt = f"""
        You are a data analyst.

        Data columns:
        {list(self.df.columns)}

        Question:
        {question}

        Write a pandas query to answer this.
        Only return python code.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        code = response.choices[0].message.content.strip()

        try:
            result = eval(code)
            return {"code": code, "result": str(result)}
        except Exception as e:
            return {"error": str(e), "code": code}