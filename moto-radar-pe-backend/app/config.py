from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://radar:radar@db:5432/radar"
    refresh_minutes: int = 30
    redis_url: str = "redis://redis:6379/0"
    cache_ttl: int = 300            # segundos: dashboard/oportunidades
    fipe_ttl: int = 86400           # FIPE muda 1x/mês; 24h é seguro
    jwt_secret: str = "change-me"   # DEFINA via variável de ambiente JWT_SECRET
    jwt_expire_minutes: int = 60 * 12
    require_auth: bool = True       # False = modo pessoal, sem login
    allow_registration: bool = True # desligue após criar seu usuário
    class Config:
        env_file = ".env"

settings = Settings()

# Modelos monitorados: termo de busca -> (marca FIPE, chave de liquidez)
MODELS = {
    "CG 160": ("Honda", "cg"), "Biz 110": ("Honda", "biz"), "Biz 125": ("Honda", "biz"),
    "Pop 110": ("Honda", "pop"), "Fazer 150": ("Yamaha", "fazer"),
    "Bros 160": ("Honda", "bros"), "XRE 190": ("Honda", "xre"), "Crosser 150": ("Yamaha", "crosser"),
}
LIQUIDEZ = {"cg": 10, "biz": 10, "pop": 9, "bros": 9, "fazer": 8, "crosser": 8, "xre": 7}
