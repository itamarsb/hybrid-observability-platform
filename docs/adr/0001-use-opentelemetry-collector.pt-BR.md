# ADR 0001: Utilizar o OpenTelemetry Collector

**Idioma:** [English (US)](0001-use-opentelemetry-collector.md) | **Português (Brasil)**

- **Status:** Aceito
- **Data:** 2026-08-21

## Contexto

A aplicação deve emitir métricas, logs e traces para os back-ends locais e, quando explicitamente habilitados, para serviços selecionados da AWS. A integração direta com cada destino acoplaria o código da aplicação aos fornecedores de armazenamento e duplicaria as regras de processamento.

## Decisão

Utilizar o OpenTelemetry Collector como gateway de telemetria. As aplicações enviam dados via OTLP ao Collector, que aplica processamento em lotes (batching), proteção de memória, filtragem, enriquecimento e amostragem antes de exportar cada sinal.

A instrumentação da aplicação permanece independente de Prometheus, Loki, Tempo, CloudWatch e X-Ray. Os conjuntos de exporters dos modos local e híbrido utilizam configurações separadas e validadas.

## Consequências

**Benefícios**

- uma única camada de processamento para todos os sinais;
- mudanças de back-end não exigem reescrever a aplicação;
- falhas de exportação podem ser isoladas da aplicação;
- filtragem e amostragem são aplicadas de forma centralizada.

**Contrapartidas**

- o Collector passa a ser mais um componente a configurar e monitorar;
- pipelines inválidos podem descartar ou duplicar telemetria;
- cada componente habilitado deve ser compatível com a distribuição selecionada do Collector.

## Validação

- a validação da configuração é bem-sucedida antes da inicialização;
- o Collector disponibiliza telemetria interna que indica seu funcionamento adequado;
- as requisições da aplicação aparecem em todos os back-ends locais habilitados;
- a indisponibilidade de um exporter não interrompe o pipeline local;
- atributos que contêm segredos e atributos de alta cardinalidade são removidos conforme previsto no projeto.

## Alternativas consideradas

- **Exportação direta pela aplicação:** rejeitada por acoplar o código a cada back-end.
- **Agentes separados, específicos para cada sinal:** rejeitada por aumentar a sobrecarga operacional.
- **Coleta exclusivamente voltada à AWS:** rejeitada porque a operação local, independente de fornecedor, é um requisito fundamental.
