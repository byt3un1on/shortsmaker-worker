# 📋 TODO - Reestruturação da Documentação e Implementação de Funcionalidades

**Data:** Janeiro 14, 2026  
**Contexto:** Análise completa do repositório identificou TODOs pendentes no código e problemas na documentação (referências quebradas, redundância excessiva, informações desatualizadas).

---

## 🎯 Objetivo Geral
Reestruturar a documentação do projeto Shortsmaker Worker, consolidando informações redundantes, corrigindo referências falsas e implementando funcionalidades críticas identificadas nos TODOs do código.

---

## 📁 Fase 1: Reestruturação da Documentação (Prioridade: Alta)

### 1.1 Criar Nova Estrutura de Documentos
- [ ] Criar `docs/README.md` atualizado com navegação limpa (remover referências a arquivos inexistentes)
- [ ] Criar `docs/ARCHITECTURE.md` consolidando arquitetura + fluxo
- [ ] Criar `docs/SETUP.md` consolidando setup + configuração  
- [ ] Criar `docs/IMPLEMENTATION.md` consolidando detalhes técnicos
- [ ] Criar `docs/STATUS.md` atualizado com todos TODOs encontrados
- [ ] Criar `docs/API_REFERENCE.md` com referência de interfaces

### 1.2 Migrar e Consolidar Conteúdo
- [ ] Migrar diagramas Mermaid de `ARCHITECTURE_AND_FLOW.md` e `DATA_FLOW.md` para `ARCHITECTURE.md`
- [ ] Consolidar informações de setup de `ENVIRONMENT_SETUP.md` e `IMPLEMENTATION_DETAILS.md` em `SETUP.md`
- [ ] Migrar padrões de código e dependências para `IMPLEMENTATION.md`
- [ ] Atualizar `STATUS.md` com lista completa de TODOs do código
- [ ] Documentar todas as interfaces em `API_REFERENCE.md`

### 1.3 Otimizar Diagramas Mermaid
- [ ] Criar diagrama consolidado de arquitetura em `ARCHITECTURE.md`
- [ ] Otimizar diagrama de fluxo de processamento
- [ ] Adicionar diagrama de status atual (pie chart)
- [ ] Garantir compatibilidade com VS Code preview

### 1.4 Limpeza e Validação
- [ ] Remover arquivos antigos: `ARCHITECTURE_AND_FLOW.md`, `DATA_FLOW.md`, `ENVIRONMENT_SETUP.md`, `IMPLEMENTATION_DETAILS.md`, `AI_PROVIDERS.md`, `TODO_SUMMARY.md`
- [ ] Verificar todos os links internos nos novos documentos
- [ ] Validar que não há referências quebradas

---

## 🔧 Fase 2: Implementação de TODOs Críticos (Prioridade: Alta)

### 2.1 Placeholder Audio Service
- [ ] **Implementar extração de metadados reais** (`placeholder_audio_service.py`)
  - [ ] Adicionar dependência `mutagen` ou `ffprobe` no `requirements.txt`
  - [ ] Implementar método `get_audio_metadata()` com extração real
  - [ ] Adicionar tratamento de erros para arquivos corrompidos
  - [ ] Atualizar docstrings com exemplos reais

- [ ] **Implementar recuperação de áudio real**
  - [ ] Criar fallback para geração de áudio background
  - [ ] Adicionar configuração para bibliotecas de áudio
  - [ ] Implementar validação de arquivos de áudio

### 2.2 Gemini Video Service
- [ ] **Inicializar cliente VertexAI** (`gemini_video_service.py`)
  - [ ] Configurar autenticação VertexAI no container de DI
  - [ ] Adicionar variáveis de ambiente para VertexAI
  - [ ] Implementar inicialização assíncrona do cliente

- [ ] **Implementar chamada real à API Gemini Veo**
  - [ ] Integrar com Vertex AI Video Generation API
  - [ ] Implementar upload de mídia e geração de vídeo
  - [ ] Adicionar tratamento de rate limits e erros
  - [ ] Atualizar configurações de modelo (veo-003)

### 2.3 MinIO Storage Service
- [ ] **Implementar limpeza de arquivos antigos** (`minio_storage_service.py`)
  - [ ] Usar `list_objects` com filtro `LastModified`
  - [ ] Implementar lógica de retenção baseada em dias
  - [ ] Adicionar configuração `cleanup_days` nas settings
  - [ ] Implementar em lote para performance

### 2.4 Testes
- [ ] **Adicionar testes para main()** (`test_main.py`)
  - [ ] Criar testes de integração para função main()
  - [ ] Mockar dependências de banco e APIs externas
  - [ ] Testar inicialização do container e worker manager
  - [ ] Adicionar testes de graceful shutdown

---

## 🧪 Fase 3: Validação e Testes (Prioridade: Média)

### 3.1 Validação da Documentação
- [ ] Executar `make validate` após cada mudança
- [ ] Verificar que todos os diagramas Mermaid renderizam no VS Code
- [ ] Testar navegação entre documentos
- [ ] Validar links externos (Google AI Studio, OpenAI, etc.)

### 3.2 Testes de Funcionalidade
- [ ] Testar implementação de áudio com arquivos reais
- [ ] Testar integração com VertexAI (se possível em dev)
- [ ] Validar limpeza de arquivos no MinIO
- [ ] Executar suite completa de testes

### 3.3 Atualização de Status
- [ ] Atualizar `STATUS.md` conforme implementações são concluídas
- [ ] Manter métricas de cobertura atualizadas
- [ ] Documentar limitações restantes

---

## 📊 Fase 4: Melhorias Adicionais (Prioridade: Baixa)

### 4.1 Observabilidade
- [ ] Adicionar métricas básicas (tempo de processamento, erros)
- [ ] Implementar health check endpoint
- [ ] Melhorar logging estruturado

### 4.2 Extensibilidade
- [ ] Documentar como adicionar novos providers de IA
- [ ] Criar interfaces para novos tipos de mídia
- [ ] Adicionar exemplos de extensão

### 4.3 Produção
- [ ] Implementar dead letter queue para tickets falhados
- [ ] Adicionar alertas para falhas críticas
- [ ] Otimizar performance para alta carga

---

## 📈 Métricas de Sucesso

- [ ] ✅ Documentação consolidada em 6 arquivos limpos
- [ ] ✅ Zero referências quebradas
- [ ] ✅ Todos os TODOs do código implementados
- [ ] ✅ Cobertura de testes > 80%
- [ ] ✅ `make validate` passando
- [ ] ✅ Diagramas Mermaid funcionais no VS Code

---

## 🚨 Dependências e Pré-requisitos

### Para Fase 1 (Documentação)
- Editor de texto (VS Code recomendado)
- Conhecimento básico de Markdown
- Familiaridade com Mermaid

### Para Fase 2 (Implementação)
- Acesso às APIs: Google VertexAI, ElevenLabs
- Ambiente de desenvolvimento configurado
- Conhecimento de Python async/await
- Familiaridade com bibliotecas: mutagen, boto3

### Para Fase 3 (Validação)
- Docker e Docker Compose funcionando
- Todas as chaves de API configuradas
- Ambiente de teste limpo

---

## 📅 Timeline Estimado

- **Fase 1 (Documentação)**: 2-3 dias
- **Fase 2 (Implementação)**: 5-7 dias  
- **Fase 3 (Validação)**: 1-2 dias
- **Fase 4 (Melhorias)**: 3-5 dias

**Total estimado**: 11-17 dias de trabalho focado.