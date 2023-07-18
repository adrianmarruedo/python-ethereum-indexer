from dotenv import load_dotenv
from pydantic import BaseSettings


class Config(BaseSettings):
    POSTGRES_HOST: str
    POSTGRES_USER: str
    POSTGRES_PASS: str
    POSTGRES_PORT: int
    POSTGRES_DATABASE: str

    PROVIDER_URL: str
    PROVIDER_WEBSOCKET: str
    PROVIDER_KEY: str


load_dotenv()
settings = Config()
