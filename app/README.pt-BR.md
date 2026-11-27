# Hybrid Observability API

**Idioma:** [English (US)](README.md) | **Português (Brasil)**

Carga de trabalho FastAPI instrumentada, utilizada pelo [Hybrid Observability Platform](../README.pt-BR.md) para gerar requisições normais, latência, erros, falhas de dependências, métricas e traces do OpenTelemetry e logs estruturados em JSON.

## Requisitos

- Python 3.12
- Docker, opcional para execução local em contêiner
- OpenTelemetry Collector, necessário apenas quando a exportação de telemetria está habilitada

## Configuração local

A partir do diretório `app`:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install --editable ".[dev]"
```

Ative o ambiente virtual.

No Linux ou macOS:

```bash
source .venv/bin/activate
```

No Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

## Execução local

Para executar localmente sem um OpenTelemetry Collector, desabilite a exportação de telemetria.

No Linux ou macOS:

```bash
export OTEL_SDK_DISABLED=true
uvicorn hybrid_observability.main:app --host 127.0.0.1 --port 8000
```

No Windows PowerShell:

```powershell
$env:OTEL_SDK_DISABLED = "true"
uvicorn hybrid_observability.main:app --host 127.0.0.1 --port 8000
```

A API estará disponível nos seguintes endereços:

- URL base da API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- Especificação OpenAPI: `http://127.0.0.1:8000/openapi.json`

## Endpoints

| Método | Endpoint | Finalidade | Status esperado |
|:---:|---|---|:---:|
| `GET` | `/health/live` | Confirma que o processo da aplicação está em execução | `200` |
| `GET` | `/health/ready` | Confirma que a aplicação está pronta para receber requisições | `200` |
| `GET` | `/api/v1/items/{item_id}` | Retorna um item de referência determinístico | `200` |
| `GET` | `/api/v1/scenarios/latency?delay_ms=250` | Introduz um atraso controlado na resposta | `200` |
| `GET` | `/api/v1/scenarios/error` | Gera uma falha controlada do serviço | `503` |
| `GET` | `/api/v1/scenarios/dependency?outcome=success` | Simula uma chamada bem-sucedida a uma dependência | `200` |
| `GET` | `/api/v1/scenarios/dependency?outcome=failure` | Simula uma dependência indisponível | `502` |
| `GET` | `/api/v1/scenarios/dependency?outcome=timeout` | Simula um timeout de dependência | `504` |

Exemplos de requisições:

```bash
curl http://127.0.0.1:8000/health/live
curl http://127.0.0.1:8000/health/ready
curl http://127.0.0.1:8000/api/v1/items/42
curl "http://127.0.0.1:8000/api/v1/scenarios/latency?delay_ms=500"
curl http://127.0.0.1:8000/api/v1/scenarios/error
curl "http://127.0.0.1:8000/api/v1/scenarios/dependency?outcome=success"
curl "http://127.0.0.1:8000/api/v1/scenarios/dependency?outcome=failure"
curl "http://127.0.0.1:8000/api/v1/scenarios/dependency?outcome=timeout"
```

Os endpoints de cenários produzem intencionalmente condições observáveis de sucesso, latência, erros de validação do cliente, erros de serviço, falhas de dependências e timeouts.

## Sinais de telemetria

### Métricas

A instrumentação do FastAPI pelo OpenTelemetry produz métricas HTTP padrão do servidor. A aplicação também cria métricas controladas de baixa cardinalidade para seus cenários de demonstração.

| Métrica | Tipo | Unidade | Finalidade |
|---|---|---|---|
| `app.scenario.requests` | Contador | `{request}` | Contabiliza cenários controlados por tipo e resultado |
| `app.scenario.duration` | Histograma | `ms` | Registra a duração do cenário de latência controlada |
| `app.dependency.requests` | Contador | `{request}` | Contabiliza chamadas simuladas a dependências por resultado |
| `app.dependency.duration` | Histograma | `ms` | Registra a duração das chamadas simuladas a dependências |

Os atributos controlados das métricas incluem:

| Atributo | Valores |
|---|---|
| `scenario.type` | `latency`, `error` |
| `scenario.outcome` | `success`, `rejected`, `failure` |
| `dependency.outcome` | `success`, `failure`, `timeout` |

Os valores dos atributos são intencionalmente limitados. Identificadores de requisições, URLs arbitrárias, mensagens de exceção e outros valores sem um conjunto limitado de possibilidades não são utilizados como atributos de métricas.

### Logs

Os logs da aplicação e do Uvicorn são escritos em JSON estruturado na saída padrão. Cada registro inclui:

- data e hora (timestamp);
- severidade;
- nome do logger;
- nome do serviço;
- versão do serviço;
- ambiente de implantação;
- ID de trace, quando há um trace ativo;
- ID de span, quando há um span ativo.

A aplicação não envia logs diretamente ao Loki. A plataforma local coletará a saída dos contêineres por meio do OpenTelemetry Collector e a encaminhará ao Loki.

### Traces

As requisições do FastAPI são instrumentadas automaticamente. Os cenários controlados de latência e dependências também criam spans explícitos com atributos específicos de cada cenário.

Os traces são exportados via OTLP gRPC. Os endpoints de verificação de saúde são excluídos da instrumentação para evitar ruído operacional repetitivo.

As métricas e os traces compartilham a mesma identidade de recurso do OpenTelemetry, incluindo nome do serviço, versão, namespace, ID da instância e ambiente de implantação.

## Verificações de qualidade

Execute todos os comandos a partir do diretório `app`, após instalar as dependências de desenvolvimento.

Execute os testes automatizados com cobertura:

```bash
pytest
```

Execute o linter:

```bash
ruff check src tests
```

Verifique a formatação:

```bash
ruff format --check src tests
```

Execute a verificação estática de tipos:

```bash
mypy src tests
```

Aplique a formatação automática quando necessário:

```bash
ruff format src tests
```

A configuração dos testes exige cobertura mínima de 85% das instruções e habilita a cobertura de ramificações (branch coverage). Os testes de métricas utilizam um leitor OpenTelemetry em memória e não exigem um Collector em execução.

## Execução em contêiner

Construa a imagem do contêiner a partir do diretório `app`:

```bash
docker build --tag hybrid-observability-api:local .
```

Execute o contêiner sem exportação de telemetria:

```bash
docker run --rm \
  --name hybrid-observability-api \
  --publish 8000:8000 \
  --env OTEL_SDK_DISABLED=true \
  hybrid-observability-api:local
```

No Windows PowerShell, o mesmo contêiner pode ser iniciado com:

```powershell
docker run --rm `
  --name hybrid-observability-api `
  --publish 8000:8000 `
  --env OTEL_SDK_DISABLED=true `
  hybrid-observability-api:local
```

Verifique o contêiner em execução:

```bash
curl http://127.0.0.1:8000/health/live
```

A imagem utiliza uma construção em múltiplas etapas (multi-stage build), instala a aplicação empacotada em um ambiente virtual dedicado, é executada com o usuário sem privilégios `appuser` e inclui uma verificação de saúde para `/health/live`.

## Configuração

A configuração é carregada a partir de variáveis de ambiente. Também pode ser utilizado um arquivo `.env` local, que não deve ser versionado quando contiver valores específicos do ambiente ou informações sensíveis.

| Variável | Valor padrão | Descrição |
|---|---|---|
| `OTEL_SERVICE_NAME` | `hybrid-observability-api` | Nome do serviço no OpenTelemetry |
| `APP_SERVICE_VERSION` | `0.1.0` | Versão da aplicação e da API |
| `APP_ENVIRONMENT` | `development` | Ambiente de implantação: `development`, `test`, `staging` ou `production` |
| `APP_HOST` | `127.0.0.1` | Endereço de vinculação local da aplicação |
| `APP_PORT` | `8000` | Porta de escuta da aplicação |
| `APP_LOG_LEVEL` | `INFO` | Nível dos logs estruturados |
| `OTEL_SDK_DISABLED` | `false` | Desabilita a inicialização do SDK do OpenTelemetry quando definido como `true` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | Endpoint OTLP gRPC do Collector |
| `OTEL_EXPORTER_OTLP_INSECURE` | `true` | Habilita uma conexão OTLP gRPC sem segurança de transporte |
| `OTEL_METRIC_EXPORT_INTERVAL` | `60000` | Intervalo periódico de exportação de métricas em milissegundos |
| `OTEL_TRACES_SAMPLER` | `parentbased_traceidratio` | Amostrador de traces do OpenTelemetry |
| `OTEL_TRACES_SAMPLER_ARG` | `1.0` | Proporção de amostragem de traces entre `0.0` e `1.0` |
| `APP_MAXIMUM_SCENARIO_DELAY_MS` | `5000` | Atraso máximo permitido no cenário de latência |
| `APP_DEPENDENCY_TIMEOUT_SECONDS` | `2.0` | Timeout aplicado à dependência simulada |

Exemplo de configuração para execução local com telemetria habilitada:

```bash
export OTEL_SDK_DISABLED=false
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_EXPORTER_OTLP_INSECURE=true
export OTEL_METRIC_EXPORT_INTERVAL=10000
uvicorn hybrid_observability.main:app --host 127.0.0.1 --port 8000
```

No Windows PowerShell:

```powershell
$env:OTEL_SDK_DISABLED = "false"
$env:OTEL_EXPORTER_OTLP_ENDPOINT = "http://localhost:4317"
$env:OTEL_EXPORTER_OTLP_INSECURE = "true"
$env:OTEL_METRIC_EXPORT_INTERVAL = "10000"
uvicorn hybrid_observability.main:app --host 127.0.0.1 --port 8000
```

O Docker Compose configurará o endpoint do Collector como `http://otel-collector:4317` e utilizará um intervalo de exportação de métricas mais curto para demonstrações locais.
