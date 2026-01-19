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
* **Média Recente**: Seguindo as diretrizes do case, a média utilizada foca nos últimos 3 meses. Clientes com no mínimo uma leitura de consumo neste período terão a média cálculada com os dados existentes. Clientes sem nenhum consumo nesse período são automaticamente excluídos da análise, garantindo relevância e precisão na detecção de anomalias.
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
  git clone [https://github.com/nathan-luz/energy-analytics-report.git](https://github.com/nathan-luz/energy-analytics-report.git)

```
#### 2. Provisionamento do Ambiente de Execução

Utiliza-se o gerenciador de pacotes uv para a otimização do ecossistema de dependências. 

**Windows (PowerShell)**
```sh
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
```sh
  uv venv
```
```sh
  .\.venv\Scripts\activate
```
```sh
  uv sync
```
**MacOS / Linux**
```sh
  curl -LsSf https://astral.sh/uv/install.sh | sh
```
```sh
  uv venv
```
```sh
  source .venv/bin/activate
```
```sh
  uv sync
```

## 🚀 Inicialização do Ambiente

Após configurar o ambiente Python com o `uv`, siga os passos abaixo para preparar o banco de dados.

### 1. Provisionamento da Infraestrutura (Docker)
Certifique-se de que o Docker e o Docker Compose estão instalados. Este comando iniciará a instância do PostgreSQL em segundo plano:

```bash
  docker-compose up -d
```
### 🗄️ Camada de Persistência e Migrações

É imperativo que a instância do PostgreSQL esteja operacional e que as configurações no arquivo alembic.ini reflitam as 
credenciais do ambiente local.
Para isso garanta que as variáveis de ambiente estejam devidamente configuradas em um arquivo .env ou no shell de execução:

```env
# Database Credentials
POSTGRES_USER=energy_admin
POSTGRES_PASSWORD=db_strong_password_123
POSTGRES_DB=energy_db

# n8n Credentials
N8N_USER=energy_admin
N8N_PASSWORD=n8n_strong_password_123

DATABASE_URL=postgresql://energy_admin:db_strong_password_123@localhost:5432/energy_db
```
Após configuradas, execute as migrações de esquema:
```sh
  uv run alembic upgrade head
```
### Acesso à Interface n8n

Após subir o container, o n8n estará disponível no seu navegador:
```
    http://localhost:5678
```


O n8n solicitará a **criação de uma conta de proprietário**. Estes dados serão armazenados apenas no seu volume local do Docker.

#### Importação dos Fluxos (Workflows)
O projeto contém dois fluxos principais que precisam ser importados manualmente para o n8n:

1. No menu lateral esquerdo, clique em **Workflows**.
2. Clique no botão de opções (três pontos ou seta no canto superior direito) e selecione **Import from File**.
3. Importe os seguintes arquivos localizados na pasta `n8n/workflows` do repositório:
    * `Data_Load_Workflow.json`: Responsável por processar o `.zip` e popular o banco.
    * `Report_Generator.json`: Responsável pelo cálculo de Z-Score e geração de insights via LLM.
    * Recomenda-se importar os fluxos em workflows separados para evitar conflitos.

#### Configuração de Credenciais
Para que os nós (nodes) funcionem corretamente, você deve configurar suas credenciais locais dentro do n8n:

* **Postgres Connection:** Edite qualquer nó de banco de dados e insira os dados configurados no seu arquivo `.env` (Host: `postgres`, Database: `energy_db`, etc.).
* **AI Provider (Google Gemini ou OpenAI):** No workflow de geração de relatórios, configure a sua **API Key** no nó de IA para permitir que o modelo analise os outliers detectados.


#### 📊 Ingestão de Dados (Seed)

Para alimentação do banco utilize os dados de seed fornecidos(`data/Archive.zip`). Ou crie um arquivo .zip com os dados desejados, obedecendo
a mesma estrutura de colunas e tipos contida nos arquivos .csv em `data/`

* Abra o workflow `Data_Load_Workflow` no n8n e execute-o. 
* Na janela que se abrir, selecione o arquivo `.zip` com os dados e clique em **Insert Data**.

Dessa forma, os dados serão processados e inseridos no banco de dados.

### 📈 Acesso ao dados de Análise

Para acessar a análise dos dados:
* Abra o workflow `Report_Generator` no n8n e execute-o. Dessa forma o WebHook estará pronto para receber requisições.
* Utilize uma ferramenta como cURL, Postman ou Insomnia para enviar uma requisição `GET` ao endpoint do WebHook.
```  http://localhost:5678/webhook/energy-report```

#### Via Terminal (cURL)
```bash
curl -X GET http://localhost:5678/webhook-test/generate-usage-report
```

#### Via Postman / Insomnia

- Crie uma nova requisição do tipo GET.
- Cole a URL: http://localhost:5678/webhook-test/generate-usage-report.
- Clique em Send.

### 📊 Dashboard Interativo (Opcional)

Alternativamente, você pode visualizar os resultados através de um dashboard interativo.
- Acesse o dashboard via navegador:
``` http://localhost:5678/webhook-test/generate-usage-report. ```

### Funcionalidades do Dashboard

* Ordenação por campos: Organização dos dados por ordem crescente ou decrescente de qualquer campo.
* Quantificação de Outliers: Sumarização imediata para suporte à tomada de decisão executiva.
* Gestão de Contratos: Visualização dos contratos ativos.
* Filtragem Dinâmica: Mecanismo de busca instantânea por nome de cliente ou status.
* Visualização Detalhada: Acesso a informações gráficas detalhadas de cada contrato e cliente.
* Visualização Interativa: Para melhor visualização dos dados adicione ou remova itens do gráfico conforme necessário.
* Exportação de Relatórios: Geração de relatórios em formatos CSV e PDF para análises externas.
* Exportação de Gráficos: Cópia dos gráficos em imagem para apresentações.
* Dark/Light Mode: Alternância entre temas escuro e claro para melhor experiência visual.


