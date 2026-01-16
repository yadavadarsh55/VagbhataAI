import streamlit as st
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    try:
        # Database
        DB_USERNAME: str = st.secrets["database"]["username"]
        DB_PASSWORD: str = st.secrets["database"]["password"]
        DB_NAME:     str = st.secrets["database"]["name"]
        DB_HOST:     str = st.secrets["database"]["host"]
        DB_PORT:     str = st.secrets["database"]["port"]
        
        # AI Services
        GOOGLE_API_KEY:      str = st.secrets["google"]["api_key"]
        PINECONE_INDEX_NAME: str = "vagbhata-index"
        EMBEDDING_MODEL:     str = "models/text-embedding-004"
        LLM_MODEL:           str = "gemini-2.5-flash-lite"
    except AttributeError as e:
            st.error("Missing secret in .streamlit/secrets.toml. Check the logs.")
            raise e

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?sslmode=require&channel_binding=require"

settings = Settings()