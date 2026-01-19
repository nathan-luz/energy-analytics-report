## ⚡ EnergyDB Analytics - Monitoramento e Análise de Consumo Energético

O EnergyDB Analytics constitui uma solução integrada de monitoramento e análise de dados do setor elétrico, abrangendo até a síntese de indicadores estratégicos via Inteligência Artificial.


### 🚀 Escopo do Projeto

Este sistema foi projetado com o propósito de identificar anomalias no perfil de consumo de uma carteira de clientes. A arquitetura foi concebida em fluxos N8N que persistem os dados num banco PostgreSQL, e um modelo (LLM) para a extração de insights operacionais fundamentados em dados.

### 🧠 Fundamentação Técnica e Decisões de Arquitetura

### Detecção de Anomalias (Z-Score):
A metodologia empregada baseia-se no cálculo da estatística **Z-Score**, que quantifica quantos desvios padrão um dado está afastado da média. O cálculo, aqui, correlaciona o consumo dos três últimos meses com a média e o desvio padrão históricos:

$$Z = \frac{x - \mu}{\sigma}$$

Onde:
* $x$: Valor do consumo atual.
* $\mu$: Média aritmética do consumo nos últimos 3 meses.
* $\sigma$: Desvio padrão histórico do período.



### Critério de Outlier:

* **Regra de Identificação:** Um registro é classificado como outlier se o valor absoluto de seu Z-Score for maior que 
1.5 ($|Z| > 1.5$).
* **Lógica de Negócio:** Esta comparação de $1.5 \times \sigma$ permite identificar variações que fogem da sazonalidade 
comum do cliente, indicando um consumo entre os 6.7% mais alto ou mais baixo do que o padrão.
* **Decisão de Projeto:** A escolha da análise do Z-Score foi fundamentada na minimização de falsos positivos ou falsos 
negativos, assegurando que apenas desvios significativos, conforme o consumo daquele cliente, sejam reportados para análise. 
Uma análise percentual poderia capturar variações normais de clientes com perfil de baixo consumo enquanto negligenciaria desvios relevantes em perfis de alto consumo. Já uma análise baseada em desvios absolutos poderia não considerar a variabilidade inerente ao comportamento de consumo de cada cliente.

### Segurança via RLS (Row Level Security): 
A integridade e a restrição de acesso são asseguradas pela implementação de políticas de segurança em nível de linha no PostgreSQL. Tal mecanismo garante que as identidades de API visualizem estritamente os registros vinculados a contratos vigentes e ativos, impedindo o acesso não autorizado a dados de terceiros.

### Preservação de Integridade de Dados (Merge Strategy): 
Desenvolveu-se uma lógica de Merge customizada em JavaScript no n8n, separando a query no banco de dados em duas partes. 
Uma query, com parte dos dados úteis à análise, é enviada para o modelo de IA, enquanto outra parte dos dados relevantes 
é incorporada pós análise para sintetizar o relatório final.
Este procedimento assegura que o processamento por LLM enriqueça os dados com análises técnicas sem o uso de tokens excessivo 
e de forma ineficiente e também garante que a estrutura da série histórica (contract_series) permaneça consistente por não
ser gerada novamente pelo modelo de IA de forma desnecessária.


### 🚀 Entregas Adicionais 
Opcionalmente, o projeto contempla a geração de um dashboard interativo para a visualização dos resultados analíticos.


### 🛠️ Instalação e Configuração

#### 1. Clonagem do Repositório
```sh   
  $ git clone [https://github.com/nathan-luz/energy-analytics-report.git](https://github.com/nathan-luz/energy-analytics-report.git)
  $ cd energy-analytics-report
```
#### 2. Provisionamento do Ambiente de Execução

Utiliza-se o gerenciador de pacotes uv para a otimização do ecossistema de dependências. 

**Windows (PowerShell)**
```sh
  $ powershell -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"
  $ uv venv
  $ .\.venv\Scripts\activate
  $ uv sync
```
**MacOS / Linux**
```sh
  $ curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
  $ uv venv
  $ source .venv/bin/activate
  $ uv sync
```
### 🗄️ Camada de Persistência e Migrações

É imperativo que a instância do PostgreSQL esteja operacional e que as configurações no arquivo alembic.ini reflitam as credenciais do ambiente local.

Execução das migrações de esquema:
```sh
  $ uv run alembic upgrade head
```
📊 Ingestão de Dados (Seed)

Para a correta alimentação do banco com o histórico referente ao biênio 2025-2026:

Acesse o diretório data/ contendo: customers_seed.csv, contracts_seed.csv e readings_seed.csv.

Compactação: Consolide os referidos arquivos em um diretório comprimido intitulado Archive.zip.

Importe o fluxo Data_Load_Workflow.json no n8n e proceda com o disparo do gatilho de entrada através do upload do arquivo .zip.

🤖 Orquestração via n8n

Importação de Fluxo: Realize a importação do arquivo Report_Generator.json na plataforma n8n.

Parametrização de Credenciais:

Estabeleça a conexão no nó Postgres com os parâmetros da instância local.

Configure o provedor de IA (Google Gemini ou OpenAI) com as respectivas chaves de API.

Acesso ao Sistema: O fluxo disponibilizará um endpoint de Webhook. A renderização do relatório ocorrerá mediante o acesso a esta URL via navegador.

📈 Painel de Análise de Resultados

O artefato visual resultante apresenta funcionalidades avançadas de interface:

Filtragem Dinâmica: Mecanismo de busca instantânea por nomenclatura de cliente, operando sem a necessidade de novos ciclos de requisição da página.

Sincronização Sob Demanda: Implementação de botão de atualização funcional que reativa o Webhook, assegurando a paridade dos dados exibidos com o estado atual do banco de dados.

Quantificação de Anomalias: Sumarização imediata e categorização de desvios críticos para suporte à tomada de decisão executiva.

👥 Expediente e Governança

Este projeto foi concebido como um estudo de caso avançado voltado à engenharia de dados e à automação inteligente de processos industriais e comerciais.
