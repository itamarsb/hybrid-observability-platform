# Política de segurança

**Idioma:** [English (US)](SECURITY.md) | **Português (Brasil)**

## Versões com suporte

O projeto está em desenvolvimento ativo e ainda não possui uma versão estável. Apenas o commit mais recente da branch `main` recebe suporte, na medida do possível e sem garantia de atendimento.

## Comunicação de vulnerabilidades

Não divulgue suspeitas de vulnerabilidades em issues, discussions ou pull requests públicos. Utilize o [canal privado de comunicação de vulnerabilidades do GitHub](https://github.com/itamarsb/hybrid-observability-platform/security/advisories/new).

Inclua o componente ou commit afetado, as etapas de reprodução, o comportamento esperado e o observado, além de uma avaliação concisa do impacto. Remova credenciais, tokens, identificadores de contas, dados pessoais, telemetria de produção e arquivos de estado do Terraform de todos os relatórios.

## Requisitos básicos de segurança do projeto

- Nunca versione credenciais, segredos, chaves privadas, arquivos `.env` reais, arquivos `.tfvars` ou arquivos de estado do Terraform.
- Dê preferência a credenciais temporárias da AWS e a funções IAM com o menor privilégio necessário.
- Mantenha privados, por padrão, o Grafana, o Prometheus, o Loki, o Tempo, os endpoints administrativos do Collector e as interfaces do Docker.
- Não registre cabeçalhos de autenticação, tokens, senhas, corpos de requisições ou dados pessoais desnecessários na telemetria.
- Execute os contêineres com versões fixadas, verificações de saúde, limites de recursos e usuários sem privilégios de root, quando houver suporte.
- Trate painéis, logs, traces, capturas de tela e resultados de testes exportados como informações potencialmente sensíveis.
- Utilize o k6 apenas em sistemas de sua propriedade ou para os quais tenha autorização explícita de teste.
- Revise os planos do Terraform antes de aplicá-los e verifique se os recursos da infraestrutura híbrida são removidos após o uso.
- Substitua imediatamente qualquer credencial exposta e, quando necessário, remova-a do histórico do Git.

## Escopo e limitações

Este repositório é uma implementação de referência, não um serviço gerenciado. Ele não oferece garantias de tempo de resposta, reforço de segurança para produção (hardening), conformidade regulatória ou certificação de segurança. As dependências e as configurações de exemplo devem ser revisadas antes de serem reutilizadas em outro ambiente.
