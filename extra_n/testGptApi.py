# test_gpt4o_api.py

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# === Load API key from .env
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("API_KEY")

# === Define prompt
prompt = PromptTemplate.from_template("Answer concisely: What is the capital of France?")
chain = prompt | ChatOpenAI(model="gpt-4o", temperature=0)

# === Run test
def main():
    try:
        result = chain.invoke({})
        print("✅ GPT-4o response:\n", result)
    except Exception as e:
        print("❌ API call failed:\n", str(e))

if __name__ == "__main__":
    main()
