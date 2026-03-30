from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_name: str = "qwen3.5:0.8b"
    ollama_base_url: str = "http://localhost:11434"
    enable_reasoning: bool = False
    agent_verbose: bool = False
    agent_max_iterations: int = 10  # maps to LangGraph recursion_limit
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "info"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
