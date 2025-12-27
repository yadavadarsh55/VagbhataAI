import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    DB_USERNAME: str = "postgres"
    DB_PASSWORD: str = os.environ['DB_PASSWORD']
    DB_NAME: str = os.environ['DB_NAME']
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    
    # AI Services
    GOOGLE_API_KEY: str = os.environ['GOOGLE_API_KEY']
    PINECONE_API_KEY: str = os.environ['PINECONE_API_KEY']
    PINECONE_INDEX_NAME: str = "vagbhata-index"
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    LLM_MODEL: str = "gemini-2.5-flash-lite"

    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?sslmode=disable"

settings = Settings()