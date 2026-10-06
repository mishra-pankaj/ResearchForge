from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
import os
from dotenv import load_dotenv

load_dotenv()

#model setup
llm = ChatGoogleGenerativeAI(model = "gemini-3.5-flash",temperature=0)

