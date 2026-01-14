# 🔗 Referência da API - Shortsmaker Worker

**Documentação técnica completa das interfaces e contratos do sistema.**

---

## 📋 Índice

- [Interfaces de Serviço](#interfaces-de-serviço)
- [Modelos de Dados](#modelos-de-dados)
- [Enums e Constantes](#enums-e-constantes)
- [Exceções](#exceções)
- [Configurações](#configurações)
- [Exemplos de Uso](#exemplos-de-uso)

---

## 🔌 Interfaces de Serviço

### ILLMService

Interface abstrata para serviços de Linguagem Natural.

```python
class ILLMService(ABC):
    @abstractmethod
    async def generate_script(self, prompt: str) -> str:
        """
        Gera um script de vídeo baseado no prompt fornecido.

        Args:
            prompt: Descrição do vídeo desejado

        Returns:
            Script formatado para vídeo curto

        Raises:
            LLMServiceError: Erro na geração do script
        """
        pass

    @abstractmethod
    async def generate_video_description(self, script: str) -> str:
        """
        Gera uma descrição detalhada para geração de vídeo baseada no script.

        Args:
            script: Script do vídeo

        Returns:
            Descrição otimizada para geração de vídeo

        Raises:
            LLMServiceError: Erro na geração da descrição
        """
        pass
```

### IAudioService

Interface para geração de áudio a partir de texto.

```python
class IAudioService(ABC):
    @abstractmethod
    async def generate_audio(self, text: str, voice_id: Optional[str] = None) -> bytes:
        """
        Gera arquivo de áudio a partir do texto fornecido.

        Args:
            text: Texto para converter em áudio
            voice_id: ID da voz a usar (opcional)

        Returns:
            Bytes do arquivo de áudio (MP3/WAV)

        Raises:
            AudioServiceError: Erro na geração do áudio
        """
        pass

    @abstractmethod
    async def get_audio_metadata(self, audio_bytes: bytes) -> AudioMetadata:
        """
        Extrai metadados do arquivo de áudio.

        Args:
            audio_bytes: Bytes do arquivo de áudio

        Returns:
            Metadados extraídos (duração, formato, etc.)

        Raises:
            AudioServiceError: Erro na extração de metadados
        """
        pass
```

### IVideoService

Interface para geração de vídeo.

```python
class IVideoService(ABC):
    @abstractmethod
    async def generate_video(
        self,
        description: str,
        duration_seconds: int = 30,
        aspect_ratio: str = "16:9"
    ) -> bytes:
        """
        Gera vídeo baseado na descrição fornecida.

        Args:
            description: Descrição detalhada do vídeo
            duration_seconds: Duração desejada em segundos
            aspect_ratio: Proporção do vídeo (16:9, 9:16, etc.)

        Returns:
            Bytes do arquivo de vídeo

        Raises:
            VideoServiceError: Erro na geração do vídeo
        """
        pass
```

### IStorageService

Interface para armazenamento de arquivos.

```python
class IStorageService(ABC):
    @abstractmethod
    async def upload_file(self, file_path: str, content: bytes) -> str:
        """
        Faz upload de arquivo e retorna URL pública.

        Args:
            file_path: Caminho/nome do arquivo
            content: Conteúdo do arquivo em bytes

        Returns:
            URL pública para acessar o arquivo

        Raises:
            StorageServiceError: Erro no upload
        """
        pass

    @abstractmethod
    async def download_file(self, url: str) -> bytes:
        """
        Faz download de arquivo pela URL.

        Args:
            url: URL do arquivo

        Returns:
            Conteúdo do arquivo em bytes

        Raises:
            StorageServiceError: Erro no download
        """
        pass

    @abstractmethod
    async def delete_file(self, url: str) -> None:
        """
        Remove arquivo do storage.

        Args:
            url: URL do arquivo a remover

        Raises:
            StorageServiceError: Erro na remoção
        """
        pass

    @abstractmethod
    async def cleanup_old_files(self, days_old: int = 7) -> int:
        """
        Remove arquivos antigos do storage.

        Args:
            days_old: Idade mínima dos arquivos a remover

        Returns:
            Número de arquivos removidos

        Raises:
            StorageServiceError: Erro no cleanup
        """
        pass
```

### ITicketRepository

Interface para persistência de tickets.

```python
class ITicketRepository(ABC):
    @abstractmethod
    async def get_by_id(self, ticket_id: UUID) -> Ticket:
        """
        Busca ticket pelo ID.

        Args:
            ticket_id: UUID do ticket

        Returns:
            Instância do ticket

        Raises:
            ValueError: Ticket não encontrado
        """
        pass

    @abstractmethod
    async def find_oldest_pending(self) -> Optional[Ticket]:
        """
        Encontra o ticket pendente mais antigo.

        Returns:
            Ticket pendente ou None se não houver
        """
        pass

    @abstractmethod
    async def create(self, ticket: Ticket) -> None:
        """
        Cria novo ticket.

        Args:
            ticket: Instância do ticket a criar
        """
        pass

    @abstractmethod
    async def update(self, ticket: Ticket) -> None:
        """
        Atualiza ticket existente.

        Args:
            ticket: Instância do ticket a atualizar
        """
        pass

    @abstractmethod
    async def delete(self, ticket_id: UUID) -> None:
        """
        Remove ticket.

        Args:
            ticket_id: UUID do ticket a remover
        """
        pass
```

---

## 📦 Modelos de Dados

### Ticket (Domain Entity)

```python
@dataclass
class Ticket:
    id: UUID
    status: TicketStatus
    script: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def can_process_script(self) -> bool:
        """Verifica se pode processar script."""
        return self.status == TicketStatus.PENDING

    def can_process_audio(self) -> bool:
        """Verifica se pode processar áudio."""
        return self.status == TicketStatus.SCRIPT_PROCESSED

    def can_process_video(self) -> bool:
        """Verifica se pode processar vídeo."""
        return self.status == TicketStatus.AUDIO_PROCESSED

    def mark_script_processed(self, script: str):
        """Marca script como processado."""
        self.script = script
        self.status = TicketStatus.SCRIPT_PROCESSED
        self.updated_at = datetime.utcnow()

    def mark_audio_processed(self, audio_url: str):
        """Marca áudio como processado."""
        self.audio_url = audio_url
        self.status = TicketStatus.AUDIO_PROCESSED
        self.updated_at = datetime.utcnow()

    def mark_video_processed(self, video_url: str):
        """Marca vídeo como processado."""
        self.video_url = video_url
        self.status = TicketStatus.VIDEO_PROCESSED
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str):
        """Marca ticket como falhado."""
        self.status = TicketStatus.FAILED
        self.updated_at = datetime.utcnow()
```

### AudioMetadata

```python
@dataclass
class AudioMetadata:
    duration_seconds: float
    format: str  # mp3, wav, etc.
    sample_rate: int
    channels: int  # 1 = mono, 2 = stereo
    bitrate: Optional[int] = None
    size_bytes: int = 0
```

---

## 🔢 Enums e Constantes

### TicketStatus

```python
class TicketStatus(Enum):
    PENDING = "pending"
    SCRIPT_PROCESSED = "script_processed"
    AUDIO_PROCESSED = "audio_processed"
    VIDEO_PROCESSED = "video_processed"
    FAILED = "failed"
```

### Provider Types

```python
LLMProvider = Literal["gemini", "openai", "both"]
AudioProvider = Literal["elevenlabs", "placeholder"]
VideoProvider = Literal["gemini", "placeholder"]
StorageProvider = Literal["supabase", "minio"]
```

### Constants

```python
# Worker
DEFAULT_WORKER_POLL_INTERVAL = 5  # segundos
DEFAULT_WORKER_MAX_RETRIES = 3
DEFAULT_WORKER_RETRY_BACKOFF = 60  # segundos

# Video
DEFAULT_VIDEO_DURATION = 30  # segundos
DEFAULT_VIDEO_ASPECT_RATIO = "16:9"

# Audio
DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs voice

# Storage
DEFAULT_BUCKET_NAME = "videos"
DEFAULT_FILE_RETENTION_DAYS = 7
```

---

## ⚠️ Exceções

### Base Exceptions

```python
class ShortsmakerError(Exception):
    """Base exception for all shortsmaker errors."""
    pass

class ServiceError(ShortsmakerError):
    """Base exception for service-related errors."""
    pass
```

### Service-Specific Exceptions

```python
class LLMServiceError(ServiceError):
    """Erro em serviço de LLM."""
    pass

class AudioServiceError(ServiceError):
    """Erro em serviço de áudio."""
    pass

class VideoServiceError(ServiceError):
    """Erro em serviço de vídeo."""
    pass

class StorageServiceError(ServiceError):
    """Erro em serviço de storage."""
    pass

class RepositoryError(ShortsmakerError):
    """Erro em repositório."""
    pass
```

### Configuration Exceptions

```python
class ConfigurationError(ShortsmakerError):
    """Erro de configuração."""
    pass

class ValidationError(ShortsmakerError):
    """Erro de validação de dados."""
    pass
```

---

## ⚙️ Configurações

### Settings (Pydantic BaseSettings)

```python
class Settings(BaseSettings):
    # Database
    database_url: str
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Worker
    worker_poll_interval: int = 5
    worker_max_retries: int = 3
    worker_retry_backoff: int = 60

    # Providers
    llm_provider: LLMProvider = "gemini"
    audio_provider: AudioProvider = "elevenlabs"
    storage_provider: StorageProvider = "supabase"
    video_provider: VideoProvider = "gemini"

    # API Keys
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    elevenlabs_voice_id: str = DEFAULT_VOICE_ID

    # Storage
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    minio_endpoint: Optional[str] = None
    minio_access_key: Optional[str] = None
    minio_secret_key: Optional[str] = None

    # Video
    gemini_model_video: str = "veo-003"
    default_video_duration: int = DEFAULT_VIDEO_DURATION

    class Config:
        env_file = ".env"
        case_sensitive = False

    def validate_provider_configs(self):
        """Valida configurações dos providers."""
        if self.llm_provider == "gemini" and not self.gemini_api_key:
            raise ConfigurationError("GEMINI_API_KEY required for gemini provider")
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ConfigurationError("OPENAI_API_KEY required for openai provider")
        if self.audio_provider == "elevenlabs" and not self.elevenlabs_api_key:
            raise ConfigurationError("ELEVENLABS_API_KEY required for elevenlabs provider")
        if self.storage_provider == "supabase" and (not self.supabase_url or not self.supabase_key):
            raise ConfigurationError("SUPABASE_URL and SUPABASE_KEY required for supabase provider")
        if self.storage_provider == "minio" and (not self.minio_endpoint or not self.minio_access_key or not self.minio_secret_key):
            raise ConfigurationError("MinIO configuration incomplete")
```

---

## 💡 Exemplos de Uso

### Criando um Ticket

```python
from core.domain.ticket import Ticket, TicketStatus
from datetime import datetime
import uuid

# Criar novo ticket
ticket = Ticket(
    id=uuid.uuid4(),
    status=TicketStatus.PENDING
)

# Verificar se pode processar
if ticket.can_process_script():
    print("Pronto para processar script")
```

### Usando o Container de DI

```python
from infra.config.container import Container

# Inicializar container
container = Container()
container.init_resources()

# Resolver dependências
llm_service = container.llm_service()
ticket_repo = container.ticket_repository()

# Usar serviços
script = await llm_service.generate_script("Vídeo sobre gatos")
ticket = await ticket_repo.find_oldest_pending()
```

### Processando um Ticket (Use Case)

```python
from core.application.use_cases.process_script_step import ProcessScriptStep

# Injetar dependências
use_case = ProcessScriptStep(
    ticket_repository=container.ticket_repository(),
    llm_service=container.llm_service(),
    storage_service=container.storage_service()
)

# Executar
ticket_id = uuid.uuid4()
await use_case.execute(ticket_id)
```

### Tratamento de Erros

```python
from core.interfaces.services import LLMServiceError, AudioServiceError

try:
    script = await llm_service.generate_script(prompt)
except LLMServiceError as e:
    logger.error(f"Erro na geração de script: {e}")
    # Implementar retry ou fallback
except AudioServiceError as e:
    logger.error(f"Erro na geração de áudio: {e}")
    # Usar serviço alternativo
```

### Configuração Programática

```python
from infra.config.settings import Settings

# Carregar settings
settings = Settings()

# Ou sobrescrever
settings = Settings(
    llm_provider="openai",
    openai_api_key="sk-...",
    database_url="postgresql://..."
)

# Validar
settings.validate_provider_configs()
```

---

## 🔍 Referências Cruzadas

### Dependências entre Interfaces

```
ITicketRepository
├── ProcessScriptStep
├── ProcessAudioStep
└── ProcessVideoStep

ILLMService
├── ProcessScriptStep
└── ProcessAudioStep (para descrições)

IAudioService
└── ProcessAudioStep

IVideoService
└── ProcessVideoStep

IStorageService
├── ProcessScriptStep (logs/debug)
├── ProcessAudioStep
└── ProcessVideoStep
```

### Fluxo Típico de Dados

```
Ticket (PENDING)
    ↓ ProcessScriptStep
Ticket (SCRIPT_PROCESSED) + script
    ↓ ProcessAudioStep
Ticket (AUDIO_PROCESSED) + audio_url
    ↓ ProcessVideoStep
Ticket (VIDEO_PROCESSED) + video_url
```

---

## 📚 Leituras Adicionais

- [ARCHITECTURE.md](ARCHITECTURE.md) - Visão geral da arquitetura
- [IMPLEMENTATION.md](IMPLEMENTATION.md) - Detalhes de implementação
- [SETUP.md](SETUP.md) - Guia de configuração
- [STATUS.md](STATUS.md) - Status atual do projeto

---

*Última atualização: Janeiro 2026*