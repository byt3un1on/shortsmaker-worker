# 🚀 Setup e Configuração - Shortsmaker Worker

**Guia completo para configurar o ambiente de desenvolvimento e produção.**

---

## 📋 Pré-requisitos

### Sistema
- **Python 3.11+** com pip
- **Docker & Docker Compose** (para desenvolvimento)
- **Git** para versionamento

### APIs Externas (Obrigatórias)
- **Google Gemini API** (gratuito para começar) OU **OpenAI API** (pago)
- **ElevenLabs API** (para áudio de alta qualidade)
- **Supabase** OU **MinIO** (para armazenamento)

### APIs Externas (Opcionais)
- **Google Vertex AI** (para geração real de vídeo)
- **AWS S3** (alternativa ao MinIO)

---

## 🛠️ Instalação e Configuração

### Passo 1: Clone o Repositório

```bash
git clone <repository-url>
cd shortsmaker-worker
```

### Passo 2: Configure o Ambiente Python

```bash
# Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r app/requirements.txt

# Instalar dependências de desenvolvimento
pip install -r app/requirements-dev.txt
```

### Passo 3: Configure as APIs

#### 3.1 Google Gemini (Recomendado)

```bash
# 1. Acesse https://makersuite.google.com/app/apikey
# 2. Crie uma API Key
# 3. Configure no .env
echo "GEMINI_API_KEY=AIzaSy..." > .env
```

#### 3.2 OpenAI (Alternativo)

```bash
# 1. Acesse https://platform.openai.com/api-keys
# 2. Crie uma API Key
# 3. Configure no .env
echo "OPENAI_API_KEY=sk-..." >> .env
```

#### 3.3 ElevenLabs (Áudio)

```bash
# 1. Acesse https://elevenlabs.io/
# 2. Crie conta e obtenha API Key
# 3. Escolha uma voz e copie o Voice ID
echo "ELEVENLABS_API_KEY=your-key" >> .env
echo "ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM" >> .env
```

#### 3.4 Supabase (Storage)

```bash
# 1. Acesse https://supabase.com/
# 2. Crie projeto e obtenha URL + Key
echo "SUPABASE_URL=https://..." >> .env
echo "SUPABASE_KEY=ey..." >> .env
```

### Passo 4: Configure o Banco de Dados

#### Opção A: Docker Compose (Recomendado)

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: shortsmaker
      POSTGRES_PASSWORD: password
      POSTGRES_DB: shortsmaker
    volumes:
      - postgres_data:/var/lib/postgresql/data

  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  minio_data:
```

```bash
# Iniciar serviços
docker-compose up -d

# Configurar .env
echo "DATABASE_URL=postgresql+asyncpg://shortsmaker:password@localhost:5432/shortsmaker" >> .env
echo "MINIO_ENDPOINT=localhost:9000" >> .env
echo "MINIO_ACCESS_KEY=minioadmin" >> .env
echo "MINIO_SECRET_KEY=minioadmin" >> .env
```

#### Opção B: PostgreSQL Local

```bash
# Instalar PostgreSQL localmente
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql

# Criar banco
createdb shortsmaker
createuser shortsmaker
psql -c "ALTER USER shortsmaker PASSWORD 'password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE shortsmaker TO shortsmaker;"
```

### Passo 5: Execute as Migrações

```bash
cd app
alembic upgrade head
cd ..
```

### Passo 6: Configure as Settings Finais

```bash
# Arquivo .env completo
cat > .env << EOF
# Database
DATABASE_URL=postgresql+asyncpg://shortsmaker:password@localhost:5432/shortsmaker

# LLM Provider
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-key

# Audio Provider
AUDIO_PROVIDER=elevenlabs
ELEVENLABS_API_KEY=your-elevenlabs-key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Storage Provider
STORAGE_PROVIDER=supabase
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# Worker Settings
WORKER_POLL_INTERVAL=5
WORKER_MAX_RETRIES=3
WORKER_RETRY_BACKOFF=60
EOF
```

---

## 🏃‍♂️ Executando o Worker

### Desenvolvimento

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Executar worker
cd app
python main.py

# Ou com debug
python -m debugpy --listen 5678 main.py
```

### Produção

```bash
# Usar Docker
docker build -t shortsmaker-worker .
docker run -d --env-file .env shortsmaker-worker

# Ou usar docker-compose
echo "
version: '3.8'
services:
  worker:
    build: .
    env_file: .env
    depends_on:
      - postgres
" > docker-compose.worker.yml

docker-compose -f docker-compose.worker.yml up -d
```

---

## 🔧 Configurações Avançadas

### Settings do Pydantic

```python
# app/infra/config/settings.py
class Settings(BaseSettings):
    # Database
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Worker
    worker_poll_interval: int = 5  # segundos
    worker_max_retries: int = 3
    worker_retry_backoff: int = 60  # segundos

    # LLM
    llm_provider: Literal["gemini", "openai", "both"] = "gemini"
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None

    # Audio
    audio_provider: Literal["elevenlabs", "placeholder"] = "elevenlabs"
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: str = "21m00Tcm4TlvDq8ikWAM"

    # Video
    video_provider: Literal["gemini", "placeholder"] = "gemini"
    gemini_model_video: str = "veo-003"

    # Storage
    storage_provider: Literal["supabase", "minio"] = "supabase"
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    minio_endpoint: Optional[str] = None
    minio_access_key: Optional[str] = None
    minio_secret_key: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False
```

### Dependency Injection Container

```python
# app/infra/config/container.py
class Container(DeclarativeContainer):
    config = providers.Singleton(Settings)

    # Database
    session_factory = providers.Singleton(async_session_factory, url=config.provided.database_url)

    # Repositories
    ticket_repository = providers.Singleton(
        PostgresTicketRepository,
        session_factory=session_factory
    )

    # Services
    llm_service = providers.Selector(
        config.provided.llm_provider,
        gemini=providers.Singleton(
            GeminiLLMService,
            api_key=config.provided.gemini_api_key,
            model=config.provided.gemini_model
        ),
        openai=providers.Singleton(
            OpenAILLMService,
            api_key=config.provided.openai_api_key,
            model=config.provided.openai_model
        )
    )

    # Use Cases
    process_script_step = providers.Factory(
        ProcessScriptStep,
        ticket_repository=ticket_repository,
        llm_service=llm_service,
        storage_service=storage_service
    )
```

---

## 🐛 Troubleshooting

### Problemas Comuns

#### Erro de Conexão com Banco
```bash
# Verificar se PostgreSQL está rodando
docker ps | grep postgres

# Testar conexão
python -c "import asyncpg; asyncpg.connect('postgresql://user:pass@localhost/db')"
```

#### API Keys Inválidas
```bash
# Testar Gemini
curl -H "x-goog-api-key: YOUR_KEY" \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?alt=json" \
  -d '{"contents": [{"parts": [{"text": "Hello"}]}]}'

# Testar ElevenLabs
curl -H "xi-api-key: YOUR_KEY" \
  "https://api.elevenlabs.io/v1/voices"
```

#### Storage Não Funciona
```bash
# Testar MinIO
curl http://localhost:9000/minio/health/live

# Testar Supabase
curl -H "Authorization: Bearer YOUR_KEY" \
  "https://your-project.supabase.co/rest/v1/"
```

### Logs de Debug

```bash
# Executar com logs detalhados
PYTHONPATH=app python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from infra.config.container import container
print('Container OK')
"
```

---

## 📊 Monitoramento

### Health Checks Básicos

```bash
# Verificar se worker está respondendo
curl http://localhost:8000/health  # TODO: implementar

# Verificar banco
python -c "
import asyncio
from infra.database.session import async_session_factory

async def test():
    async with async_session_factory() as session:
        result = await session.execute('SELECT 1')
        print('DB OK')

asyncio.run(test())
"
```

### Métricas (TODO)

- Tempo médio de processamento por etapa
- Taxa de sucesso/falha
- Uso de recursos (CPU, memória)
- Latência das APIs externas

---

## 🚀 Próximos Passos

Após configurar:

1. **Leia** [ARCHITECTURE.md](ARCHITECTURE.md) para entender o sistema
2. **Execute** `make validate` para verificar se tudo está OK
3. **Teste** criando um ticket via API
4. **Monitore** os logs durante o processamento

---

*Última atualização: Janeiro 2026*