import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Umucyo")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    PASSWORD_SETUP_EXPIRE_HOURS: int = int(os.getenv("PASSWORD_SETUP_EXPIRE_HOURS", "24"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    FRONTEND_URL: str = os.getenv(
        "FRONTEND_URL",
        "http://localhost:3000",
    )

    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001",
        ).split(",")
        if origin.strip()
    ]

    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_EMAIL: str = os.getenv("SMTP_EMAIL", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")

    OTP_EXPIRE_MINUTES: int = int(os.getenv("OTP_EXPIRE_MINUTES", "10"))

    SMS_LEOPARD_API_KEY: str = os.getenv("SMS_LEOPARD_API_KEY", "")
    SMS_LEOPARD_API_SECRET: str = os.getenv(
        "SMS_LEOPARD_API_SECRET",
        "",
    )
    SMS_LEOPARD_SENDER_ID: str = os.getenv(
        "SMS_LEOPARD_SENDER_ID",
        "",
    )

    BOOTSTRAP_SECRET: str = os.getenv("BOOTSTRAP_SECRET", "")

    @property
    def jwt_secret_key(self) -> str:
        return self.JWT_SECRET_KEY

    @property
    def access_token_expire_minutes(self) -> int:
        return self.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def bootstrap_secret(self) -> str:
        return self.BOOTSTRAP_SECRET

    @property
    def password_setup_expire_hours(self) -> int:
        return self.PASSWORD_SETUP_EXPIRE_HOURS

    @property
    def frontend_url(self) -> str:
        return self.FRONTEND_URL


settings = Settings()
