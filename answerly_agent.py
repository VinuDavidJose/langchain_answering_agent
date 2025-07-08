
import streamlit as st
from langchain_hub import pull
from langchain.agents import load_tools, create_react_agent, AgentExecutor

# 🔹 OpenAI
from langchain_openai import ChatOpenAI
from openai import AuthenticationError, RateLimitError, OpenAIError

# 🔹 Google Gemini
from langchain_google_genai import ChatGoogleGenerativeAI
from google.api_core.exceptions import ResourceExhausted, InvalidArgument, NotFound

# --------------- UI Sidebar: Model & API Keys ------------------

with st.sidebar:
    st.title("🔑 API Settings")

    provider = st.selectbox("Select Provider", ["OpenAI", "Gemini"])

    if provider == "OpenAI":
        openai_key = st.text_input("OpenAI API Key", type="password")
        model_name = st.selectbox("Model", ["gpt-3.5-turbo", "gpt-4", "gpt-4o"], index=2)
    else:
        gemini_key = st.text_input("Gemini API Key", type="password")
        model_name = st.selectbox("Model", ["models/gemini-1.5-flash", "models/gemini-1.5-pro"], index=0)

# --------------- API Key Validation ------------------

if provider == "OpenAI":
    if not openai_key:
        st.info("Enter your OpenAI API key to continue.")
        st.stop()

    try:
        test_llm = ChatOpenAI(model=model_name, api_key=openai_key)
        test_llm.invoke("Hello")
    except AuthenticationError:
        st.error("❌ Invalid OpenAI API key.")
        st.stop()
    except RateLimitError as e:
        st.error("🚫 Quota exceeded or rate-limited.")
        st.code(str(e))
        st.stop()
    except OpenAIError as e:
        st.error("⚠️ OpenAI error occurred.")
        st.code(str(e))
        st.stop()
    except Exception as e:
        st.error("❌ Unknown error.")
        st.code(str(e))
        st.stop()

else:
    if not gemini_key:
        st.info("Enter your Gemini API key to continue.")
        st.stop()

    try:
        test_llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=gemini_key)
        test_llm.invoke("Hello Gemini")
    except ResourceExhausted as e:
        st.error("🚫 Gemini quota exceeded.")
        st.code(str(e))
        st.stop()
    except InvalidArgument:
        st.error("❌ Invalid Gemini API key or model name.")
        st.stop()
    except NotFound:
        st.error("❌ Gemini model not found.")
        st.stop()
    except Exception as e:
        st.error("❌ Gemini error.")
        st.code(str(e))
        st.stop()

# --------------- Build Agent ------------------

# Use validated key + model
llm = (
    ChatOpenAI(model=model_name, api_key=openai_key)
    if provider == "OpenAI"
    else ChatGoogleGenerativeAI(model=model_name, google_api_key=gemini_key)
)

prompt = pull("hwchase17/react")
tools = load_tools(["ddg-search"])
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# --------------- Main App ------------------

st.title("🧠 AI Agent – Chat with the Web")
task = st.text_input("Ask anything...")

if task:
    with st.spinner("Working on it..."):
        try:
            response = agent_executor.invoke({"input": task})
            st.success("✅ Done")
            st.write(response["output"])
        except Exception as e:
            st.error("❌ Agent failed")
            st.code(str(e))
