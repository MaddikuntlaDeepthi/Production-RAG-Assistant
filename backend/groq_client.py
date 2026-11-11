
import os

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq(api_key=api_key)


def test_groq_connection():

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {
                    "role": "user",
                    "content": "Explain HDFS in two sentences."
                }
            ],
            temperature=0
        )

        print("\nQWEN MODEL CONNECTION SUCCESSFUL\n")
        print(response.choices[0].message.content)

    except Exception as error:
        print("\nQWEN MODEL CONNECTION FAILED")
        print(error)


if __name__ == "__main__":
    test_groq_connection()


