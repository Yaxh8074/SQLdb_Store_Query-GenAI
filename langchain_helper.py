import os
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.utilities import SQLDatabase
from langchain_community.vectorstores import Chroma
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_core.messages import HumanMessage

from few_shots import few_shots


def get_chain_components():
    # ---- Database ----
    db = SQLDatabase.from_uri(
        "mysql+pymysql://root:yash@localhost/tshirts_Showroom",
        sample_rows_in_table_info=3
    )

    # ---- LLM ----
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        groq_api_key=os.environ["GROQ_API_KEY"],
        temperature=0
    )

    # ---- Embeddings + VectorStore ----
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=os.environ["GEMINI_API_KEY"]
    )

    valid_shots = [ex for ex in few_shots if all(v.strip() for v in ex.values())]
    to_vectorize = [" ".join(ex.values()) for ex in valid_shots]
    vectorstore = Chroma.from_texts(to_vectorize, embeddings, metadatas=valid_shots)

    example_selector = SemanticSimilarityExampleSelector(
        vectorstore=vectorstore,
        k=2
    )

    # ---- Few Shot Prompt (for SQL generation only) ----
    example_prompt = PromptTemplate(
        input_variables=["Question", "SQLQuery", "SQLResult", "Answer"],
        template="Question: {Question}\nSQLQuery: {SQLQuery}\nSQLResult: {SQLResult}\nAnswer: {Answer}"
    )

    few_shot_prompt = FewShotPromptTemplate(
        example_selector=example_selector,
        example_prompt=example_prompt,
        prefix="""You are a MySQL expert. Given a question, return ONLY a valid MySQL query with absolutely no explanation, no markdown, no backtick code fences, and no preamble. Just the raw SQL query.

Table info:
{table_info}

Here are some similar examples:
""",
        suffix="\nQuestion: {input}\nSQLQuery:",
        input_variables=["input", "table_info"]
    )

    return db, llm, few_shot_prompt


def run_query(question: str, db, llm, few_shot_prompt) -> dict:
    # Step 1: Generate SQL
    table_info = db.get_table_info()
    prompt_text = few_shot_prompt.format(input=question, table_info=table_info)

    sql_response = llm.invoke([HumanMessage(content=prompt_text)])
    sql_query = sql_response.content.strip()

    # Clean up any accidental markdown fences
    if "```" in sql_query:
        sql_query = sql_query.split("```")[1]
        if sql_query.lower().startswith("sql"):
            sql_query = sql_query[3:]
    sql_query = sql_query.strip()

    print(f"\nGenerated SQL: {sql_query}\n")

    # Step 2: Execute SQL
    try:
        sql_result = db.run(sql_query)
    except Exception as e:
        sql_result = f"Error executing query: {str(e)}"

    print(f"SQL Result: {sql_result}\n")

    # Step 3: Generate natural language answer
    answer_prompt = f"""You are a helpful assistant for a t-shirt store database.

Question: {question}
SQL Query used: {sql_query}
Database Result: {sql_result}

Give a clear, concise natural language answer. No SQL, no technical jargon. Just answer the question directly."""

    final_answer = llm.invoke([HumanMessage(content=answer_prompt)])

    return {
        "question": question,
        "sql_query": sql_query,
        "sql_result": sql_result,
        "answer": final_answer.content
    }