# Shortsmaker Worker

Worker assíncrono para processamento de vídeos curtos usando Clean Architecture.

## 📋 Visão Geral

O Shortsmaker Worker é um sistema de processamento assíncrono que:

- 🎬 Gera roteiros para vídeos curtos usando IA (OpenAI GPT ou Google Gemini) ✅
- 🎵 Processa e adiciona áudio/música via ElevenLabs TTS ✅
- 🎥 Gera vídeos usando Gemini Veo 3 ou Stability Video ⚠️ (estrutura pronta, integração mock)
- 🔊 Geração de voz (TTS) via ElevenLabs ✅
- ☁️ Armazena todos os assets no Supabase, MinIO ou S3 ✅

### ⚠️ Limitações Conhecidas

- **Gemini Video (Veo 3)**: Estrutura implementada mas retorna mock data. Requer integração com Vertex AI.
- **Placeholder Audio**: Se ElevenLabs não configurado, retorna bytes vazios.
- **Sem Health Check**: Não há endpoint HTTP para monitoramento do worker.
- **Observabilidade Limitada**: Métricas e alertas não implementados.

### Arquitetura

O projeto segue **Clean Architecture** com separação clara de responsabilidades:

```
app/
├── core/              # Lógica de negócio pura
│   ├── domain/        # Entidades e enums
│   ├── application/   # Casos de uso
│   └── interfaces/    # Contratos (ports)
├── adapter/           # Implementações externas
│   ├── repositories/  # Acesso a dados
│   ├── ai/           # Serviços de IA
│   ├── video/        # Processamento de vídeo
│   ├── audio/        # Processamento de áudio
│   └── storage/      # Armazenamento de arquivos
├── infra/            # Infraestrutura
│   ├── config/       # Configuração e DI
│   ├── database/     # Sessões de banco
│   └── logging/      # Sistema de logs
└── services/         # Orquestração
    ├── worker_loop.py     # Loops de processamento
    └── worker_manager.py  # Gerenciamento de workers
```

## 🚀 Quick Start

### 1. Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- Chave de API do Google Gemini ou OpenAI

### 2. Clone e Configure

```bash
cd /workspaces/shortsmaker/shortsmaker-worker

# Copie o arquivo de configuração
cp .env.example .env

# Edite o .env e adicione suas chaves de API
nano .env
```

### 3. Inicie a Infraestrutura

```bash
# Inicia PostgreSQL e MinIO
docker-compose up -d

# Verifique se os serviços estão rodando
docker-compose ps
```

### 4. Instale Dependências

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 5. Execute o Worker

```bash
python main.py
```

## 📚 Documentação

### 📖 🆕 Documentação Completa - Leia Primeiro!

#### 📊 **Visão Geral & Referência Rápida**
- **[COMPLETE_OVERVIEW.md](COMPLETE_OVERVIEW.md)** ⭐ **START HERE** - Resumo completo do projeto com diagramas
- **[QUICK_START.md](docs/QUICK_START.md)** - Comece em 5 minutos

#### 🏗️ **Arquitetura e Design**
- **[Architecture & Flow](docs/ARCHITECTURE_AND_FLOW.md)** ⭐ **NOVO** - Arquitetura em camadas com diagramas Mermaid
- **[Data Flow](docs/DATA_FLOW.md)** ⭐ **NOVO** - Fluxo de dados, estado e concorrência
- **[Implementation Details](docs/IMPLEMENTATION_DETAILS.md)** ⭐ **NOVO** - Detalhes de implementação e código

#### ⚙️ **Configuração & Setup**
- **[Environment Setup](docs/ENVIRONMENT_SETUP.md)** - Guia passo-a-passo
- **[Configuration](docs/CONFIGURATION.md)** - Referência completa de env vars

#### 🔌 **Integrações**
- **[AI Providers](docs/AI_PROVIDERS.md)** - Gemini, OpenAI e outros
- **[MinIO Storage](docs/MINIO_STORAGE.md)** - Configuração de armazenamento

#### 📊 **Status & Roadmap**
- **[TODO_SUMMARY.md](docs/TODO_SUMMARY.md)** - Status atual e limitações conhecidas

## 🔧 Configuração

### Providers de LLM

Configure no `.env`:

```bash
# Usar Gemini (gratuito para começar)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-1.5-flash

# Ou usar OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-3.5-turbo

# Ou ambos com fallback
LLM_PROVIDER=both
LLM_PRIMARY=gemini
LLM_FALLBACK=openai
```

### Storage

```bash
# MinIO (local/desenvolvimento)
STORAGE_PROVIDER=minio
MINIO_ENDPOINT=localhost:9000
MINIO_BUCKET=shortsmaker-media

# Ou Supabase
STORAGE_PROVIDER=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key

# Ou AWS S3
STORAGE_PROVIDER=s3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET=shortsmaker-media
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Com cobertura
pytest --cov=app --cov-report=html

# Testes específicos
pytest test_main.py -v
```

## 🔍 Estrutura de Dados

### Ticket (Estado da Máquina)

```
PENDING → PENDING_SCRIPT → PENDING_AUDIO → PENDING_VIDEO → PENDING_VTT → COMPLETED
                ↓               ↓               ↓               ↓
              ERROR           ERROR           ERROR           ERROR
```

### Atributos do Ticket

Armazenados em `TICKET_ATTRIBUTES`:

- `theme`: Tema do vídeo
- `description`: Descrição detalhada
- `script`: Roteiro gerado
- `audio_url`: URL do áudio no storage
- `video_url`: URL do vídeo final
- `vtt_url`: URL das legendas

## 🛠️ Desenvolvimento

### Código

```bash
# Formatar código
black app/
isort app/

# Verificar qualidade
flake8 app/
mypy app/
```

### Estrutura de Workers

O sistema usa "Database as a Queue" com workers especializados:

- **Script Worker**: Gera roteiros usando LLM
- **Audio Worker**: Processa áudio/música
- **Video Worker**: Gera vídeos com IA
- **VTT Worker**: Extrai legendas

Cada worker:
1. Busca tickets com status apropriado (`SELECT ... FOR UPDATE SKIP LOCKED`)
2. Processa o ticket
3. Atualiza status e atributos
4. Repete

## 📊 Monitoring

```bash
# Logs em tempo real
tail -f logs/worker.log

# Status dos workers
docker-compose logs -f worker
```

## 🐛 Troubleshooting

### Worker não inicia

```bash
# Verifique configuração
python -c "from infra.config.settings import get_settings; s = get_settings(); s.validate_required_configs()"
```

### Erros de conexão

```bash
# Verifique se os serviços estão rodando
docker-compose ps

# Logs do PostgreSQL
docker-compose logs postgres

# Logs do MinIO
docker-compose logs minio
```

### Performance

- Use `gemini-1.5-flash` em vez de `gemini-1.5-pro` para respostas mais rápidas
- Ajuste `WORKER_*_CONCURRENCY` baseado nos recursos disponíveis
- Configure `WORKER_POLL_INTERVAL` para balancear latência vs carga no DB

## 🤝 Contribuindo

1. Mantenha a Clean Architecture
2. Adicione testes para novas funcionalidades
3. Siga o style guide (Black + isort)
4. Documente mudanças no código
5. Atualize a documentação em `docs/`

## 📝 TODO

- [ ] Implementar integração real com Gemini
- [ ] Implementar integração real com Runway ML
- [ ] Adicionar serviço de áudio real (ElevenLabs)
- [ ] Implementar Supabase Storage adapter
- [x] Adicionar retry logic com backoff exponencial
- [ ] Implementar multi-provider LLM com fallback
- [ ] Adicionar métricas e monitoring (Prometheus)
- [ ] Criar dashboard de status dos workers
- [ ] Implementar circuit breaker para APIs externas
- [ ] Adicionar testes de integração
- [x] Implementar Alembic Migrations no Worker

## 📄 Licença

[Defina sua licença aqui]

## 💬 Suporte

Para questões e suporte:
- Consulte a documentação em `docs/`
- Abra uma issue no repositório
- Entre em contato com a equipe

---

**Status**: 🚧 Em desenvolvimento (Skeleton implementation)
