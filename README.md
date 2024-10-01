# google-searcher
Realiza buscas usando o Google Custom Search API.

## Configuração
Para utilizar este script, é necessário criar uma chave de API e um mecanismo de pesquisa personalizado.
1. Crie um projeto no [Google Cloud Platform](https://console.cloud.google.com/).
2. Ative a [API Custom Search API](https://console.cloud.google.com/marketplace/product/google/customsearch.googleapis.com).
3. Crie uma chave de API.
4. Crie um [mecanismo de pesquisa personalizado](https://cse.google.com/cse/all).

## Instalação
1. Clone o repositório.
2. Instale as dependências:
```bash
pip install -r requirements.txt
```
3. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```
4. Edite o arquivo `.env` e adicione a chave de API e o ID do mecanismo de pesquisa.
```bash	
API_KEY=SUA_CHAVE_DE_API
CSE_ID=SEU_ID_DE_MECANISMO_DE_PESQUISA
```

## Uso
```bash
python3 main.py
```
Sigas as instruções exibidas no terminal.