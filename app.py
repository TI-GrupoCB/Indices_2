import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import base64
import datetime
from io import StringIO

#Configuração para armazenamento de log.
logging.basicConfig(level=logging.INFO,filename="log_execucao_python_PS4-300.log", format="%(asctime)s - %(levelname)s - %(message)s ")

# URLs índice
urls = [
    "https://www.portalbrasil.net/ipca",
    "https://www.portalbrasil.net/igpm",
    "https://www.portalbrasil.net/igp",
    "https://www.portalbrasil.net/ipc",
    "https://www.portalbrasil.net/inpc"
]

# Informações para fazer get como browser
header = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36",
}

# Service_key - DS4
#username = 'sb-e5ca4a76-c150-4dab-a06a-e4e9c71c6cb1!b1223|it-rt-poc-ipca4-te2e9i9w!b106'
#password = '93364cfe-7a00-4bc5-9754-f8b1de065f9c$MwvFavZzJVRMgyrN_MOft3zufxV0sSimn2IAfTj40E4='

# Service_key - PS4
username = 'sb-84834982-0f6a-49b7-816f-955c7abeb3d0!b2807|it-rt-ps4-300-4810amfq!b106'
password = '12b61bf2-8674-41ca-87cc-0bd3ab13a6f5$tmnEXiljCHwjxbF8mnHvC6kEo6-89LRty8kLL0kmCMM='

# Define a URL da API do SAP BTP para enviar os dados
# DS4-400
#api_url = "https://poc-ipca4-te2e9i9w.it-cpi008-rt.cfapps.br10.hana.ondemand.com/http/portalbrasil/indices2"

# PS4-300
api_url = "https://ps4-300-4810amfq.it-cpi008-rt.cfapps.br10.hana.ondemand.com/http/portalbrasil/indices"

# Obter o ano atual
ano_atual = datetime.datetime.now().year
# Converter o ano atual para uma string
ano_str = str(ano_atual)
for url in urls:    
    # Obtém os dados do site
    response = requests.get(url, headers=header)

    # Verifica se a requisição foi bem sucedida (código 200)
    if response.status_code == 200:
        # Extrai o conteúdo HTML da página
        html_content = response.text

        # Cria um objeto BeautifulSoup para analisar o HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Encontra a tag <h1> com a classe "entry-title" e o atributo "itemprop" com o valor "headline"
        h1_tag = soup.find('h1', class_='entry-title', itemprop='headline')

        # Verifica se a tag foi encontrada
        if h1_tag:
            # Obtém o conteúdo da tag
            indice = h1_tag.text.strip()

            # Procura palavras-chave específicas no conteúdo do título
            if "IPCA" in indice.upper():
                indice = "IPCA"
                # Lê as tabelas HTML do response
                #dfs = pd.read_html(response.text, thousands='.', decimal=',')
                dfs = pd.read_html(StringIO(response.text), thousands='.', decimal=',')
                df = dfs[0]  # Obtém apenas a primeira tabela
            elif "IPC" in indice.upper():
                indice = "IPC"
                # Lê as tabelas HTML do response
                dfs = pd.read_html(StringIO(response.text), thousands='.', decimal=',')
                df = dfs[2]  # Obtém a terceira tabela
            elif "IGP-DI" in indice.upper():
                indice = "IGP"
                # Lê as tabelas HTML do response
                dfs = pd.read_html(StringIO(response.text), thousands='.', decimal=',')
                df = dfs[0]  # Obtém a primeira tabela
            elif "IGP-M" in indice.upper():
                indice = "IGPM"
                # Lê as tabelas HTML do response
                dfs = pd.read_html(StringIO(response.text), thousands='.', decimal=',')
                df = dfs[2]  # Obtém a terceira tabela
            elif "INPC" in indice.upper():
                indice = "INPC"
                # Lê as tabelas HTML do response
                dfs = pd.read_html(StringIO(response.text), thousands='.', decimal=',')
                df = dfs[1]  # Obtém a quinta tabela
            else:
                indice = "Índice não encontrado"
                logging.error("Índice não encontrado") #Log armazenado no fileserver
                df = None
        else:
            print("Tag não encontrada.")
            logging.error("Tag não encontrada.") #Log armazenado no fileserver
    else:
        print('Falha na requisição. Código de status:', response.status_code)
        logging.error(f"Falha na requisição. Código de status:", {response.status_code}) #Log armazenado no fileserver
        
    # Verifica se o dataframe foi atribuído corretamente
    if df is not None:
        # Obtém os valores desejados da tabela
        primeiro_item = df.iloc[0, 4]
        segundo_item = df.iloc[0, 0]

        # Obtém o mês e ano
        month_dict = {
             "Jan/"+ano_str : 1, "Fev/"+ano_str: 2, "Mar/"+ano_str: 3, "Abr/"+ano_str: 4, "Mai/"+ano_str: 5, "Jun/"+ano_str: 6,
             "Jul/"+ano_str: 7, "Ago/"+ano_str: 8, "Set/"+ano_str: 9, "Out/"+ano_str: 10, "Nov/"+ano_str: 11, "Dez/"+ano_str: 12
        }
        Month = month_dict.get(segundo_item[:8], 13) + 1 #Pegar o número do mês com base nos oito primeiros caracteres do segundo_item, caso não encontre o mês será fixado o valor 13 + 1
        year = segundo_item[4:9]
        if Month == 14:
             logging.error("Mês não identificado!!! verificar tabela no site.") #Log armazenado no fileserver
        else:
            # Obtém base ano
            if indice == "IPCA":
                base_year = "1980"
            elif indice == "IPC":
                base_year = "1990"
            elif indice == "IGP":
                base_year = "1980"
            elif indice == "IGPM":
                base_year = "1993"
            elif indice == "INPC": 
                base_year = "1990"
            else: base_year = "9999"
            # Cria o dicionário com os dados
            dados = {
                "taxValue": str(primeiro_item),
                "year": year,
                "month": Month,
                "index": indice,
                "base_year": base_year
                }
            logging.info(dados) #Log armazenado no fileserver
            print(dados)

            # Converte o dicionário para JSON
            dados_json = json.dumps(dados)

            # Codifica o username e password em Base64 (Token)
            credentials = f"{username}:{password}"
            encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

            # Define os headers para a requisição de envio dos dados
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                "Content-Type": "application/json"
                }

            # Envia os dados para o SAP BTP
            response = requests.post(api_url, headers=headers, data=dados_json)

            if response.status_code == 201:
                print("Dados enviados com sucesso para o SAP BTP - PS4-300.") #Print em tempo de execução
                logging.info("Dados enviados com sucesso para o SAP BTP - PS4-300.") #Log armazenado no fileserver
                
            else:
                print(f"Status code de resposta:", {response.status_code})
                logging.error(f"Status code de resposta:", {response.status_code})
    else:
        print("Nenhum dataframe disponível para o índice encontrado.") #Print em tempo de execução
        logging.error("Nenhum dataframe disponível para o índice encontrado.") #Log armazenado no fileserver