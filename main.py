import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGCHAIN_TRACING"] = "false"

import streamlit as st
from langchain_helper import get_chain_components, run_query
from dotenv import load_dotenv
load_dotenv()

st.title("TShirts Showroom: Database Q&A 👕")

@st.cache_resource
def load_components():
    return get_chain_components()

db, llm, few_shot_prompt = load_components()

question = st.text_input("Question:")

if question:
    with st.spinner("Thinking..."):
        result = run_query(question, db, llm, few_shot_prompt)

    st.header("Answer")
    st.write(result["answer"])

    with st.expander("See SQL Query"):
        st.code(result["sql_query"], language="sql")

    with st.expander("See Raw DB Result"):
        st.write(result["sql_result"])

