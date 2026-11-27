# Arquitetura

**Idioma:** [English (US)](architecture.md) | **Português (Brasil)**

## Escopo

O Hybrid Observability Platform é um ambiente de referência de nó único que prioriza
a execução local para instrumentar uma carga de trabalho FastAPI, processar sua
telemetria com OpenTelemetry e investigar métricas, logs e traces no Grafana.

O escopo implementado compreende uma stack Docker Compose de seis serviços, painéis
provisionados, uma carga de trabalho instrumentada, a CI da aplicação e um validador
local de ponta a ponta. Uma integração opcional para exportação à AWS está planejada,
mas não faz parte da implantação atual. O ambiente prioriza a reprodutibilidade e
modos de falha explícitos em vez de escala de produção ou disponibilidade contínua.

## Componentes implementados

| Componente | Responsabilidade |
|---|---|
| Serviço FastAPI | Disponibiliza endpoints determinísticos e cenários controlados de HTTP 503, 502, 504 e latência |
| OpenTelemetry SDK | Produz métricas e traces da aplicação e fornece o contexto de trace para logs estruturados |
| OpenTelemetry Collector | Recebe métricas e traces via OTLP e logs da aplicação via Fluent Forward, aplica os processadores configurados e encaminha cada sinal |
| Prometheus | Coleta e armazena as métricas exportadas por até 48 horas |
| Loki | Armazena logs locais da aplicação com retenção de 24 horas |
| Tempo | Armazena traces locais com retenção de 24 horas |
| Grafana | Disponibiliza fontes de dados provisionadas, painéis e navegação entre Loki e Tempo |
| Docker Compose | Gerencia serviços locais, vinculação de portas, verificações de saúde, redes e volumes |
| Validador local | Inicia a stack e verifica de forma independente a saúde dos serviços e a entrega de métricas, logs e traces |

Cargas de trabalho do k6, regras de gravação (recording rules) e de alerta, CI da
plataforma completa e integração com a AWS gerenciada pelo Terraform são itens do
roadmap, não componentes implantados.

## Fluxo de dados atual

1. Um cliente ou o validador local envia requisições à aplicação FastAPI.
2. A instrumentação do FastAPI exporta métricas e traces via OTLP/gRPC para o Collector.
3. Os logs JSON da aplicação são escritos na saída padrão (stdout), encaminhados pelo
   driver de logging Fluentd do Docker ao receptor Fluent Forward do Collector e
   enriquecidos com atributos de recurso da aplicação.
4. Os processadores de limitação de memória e de processamento em lotes (batch)
   configurados no Collector atuam em cada pipeline de telemetria. Os logs são
   encaminhados ao Loki via OTLP/HTTP; os traces são encaminhados ao Tempo via
   OTLP/gRPC; as métricas exportadas são coletadas pelo Prometheus.
5. O Grafana consulta os back-ends, e o campo derivado provisionado do Loki e as
   configurações de navegação de traces para logs do Tempo permitem investigar
   requisições específicas.

A aplicação configura a amostragem de traces. A configuração atual do Collector
não declara amostragem de traces ao final do fluxo (tail sampling), processador de
mascaramento de dados do payload nem políticas adicionais de filas ou novas
tentativas de exportação. Não se deve presumir a existência desses controles.

## Limites da implantação

Os seis serviços são executados em uma rede bridge dedicada do Compose. Na configuração
versionada, as portas dos serviços publicadas no host estão vinculadas a 127.0.0.1.
Prometheus, Loki, Tempo e Grafana mantêm seus dados em volumes Docker nomeados;
as janelas de retenção documentadas limitam o histórico de telemetria, mas não
eliminam a necessidade de remover explicitamente os volumes quando se deseja
excluir os dados.

O modo local implementado não exige credenciais da AWS. Atualmente, nenhum recurso
da AWS é provisionado por este repositório.

## Controles existentes de confiabilidade e recursos

- Verificações de saúde dos contêineres e dependências entre serviços no Compose.
- Limitação de memória e processamento em lotes no Collector.
- Amostragem de traces configurável na aplicação; o Compose local utiliza atualmente amostragem de 100%.
- Políticas locais de retenção do Prometheus, Loki e Tempo.
- Limites de CPU e memória dos contêineres no Compose.
- Validador local com 16 verificações, incluindo uma nova verificação de métricas HTTP 503
  agregadas por rota e da correlação de uma requisição específica entre Loki e Tempo.
  Essa verificação conta com 11 testes unitários offline aprovados e uma execução de
  integração local bem-sucedida, com 16/16 verificações aprovadas, documentada em
  20/11/2026 (2026-11-20).
- Cenários controlados de falhas e atrasos na aplicação.

Medidas adicionais de reforço da segurança e da resiliência (por exemplo, testes de
resiliência dos exporters, filtragem de atributos que contenham segredos, testes de
carga e verificações de segurança da plataforma completa) ainda precisam ser
implementadas e validadas. A verificação de correlação por requisição foi executada
com a stack local em funcionamento; a CI automatizada da plataforma permanece como
uma atividade separada.

## Cenário de investigação

O principal fluxo de investigação documentado gera intencionalmente um HTTP 503,
observa suas métricas por rota e código de status no Prometheus, localiza um log
estruturado no Loki e abre o trace correspondente no Tempo utilizando o ID exato
do trace retornado pela resposta HTTP. Os cenários de dependências com HTTP 502/504
permitem, opcionalmente, investigar spans aninhados.

Os painéis atuais não exigem um exemplar de métrica para iniciar esse processo:
as métricas identificam o sintoma no nível da rota, enquanto o ID do trace retornado
na resposta e os logs estruturados identificam a requisição individual. O runbook
documenta o fluxo de investigação manual. A nova verificação do validador também
exige o mesmo ID de trace na resposta HTTP, no log estruturado de erro do Loki e
em um span de servidor correspondente no Tempo. As métricas do Prometheus
permanecem como evidências agregadas por rota, e não como um vínculo individual
por requisição. Uma execução local bem-sucedida da stack completa está documentada
no [Registro de validação da correlação HTTP](operations/http-correlation-validation-2026-11-20.md).

Consulte o [Runbook de investigação de erros HTTP](operations/http-error-investigation.md)
e a [Validação da stack local](operations/local-stack-validation.md).
