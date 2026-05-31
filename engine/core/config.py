from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5432/trendletter"
    openai_api_key: str = ""
    telegram_bot_token: str = ""
    engine_api_key: str = "dev-engine-key-change-in-production"
    naver_id: str = ""
    naver_pw: str = ""
    kakao_client_id: str = ""
    kakao_client_secret: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
