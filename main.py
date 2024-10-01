"""Extract URLs from social media posts and search for them on Google."""

from enum import Enum
import requests
import os
import sys
import pandas as pd
from dotenv import load_dotenv
import re
import time


MIN_TEXT_LENGTH = 200
API_URL = "https://www.googleapis.com/customsearch/v1"
API_KEY = None
CSE_ID = None

class SocialNetwork(Enum):
    """The social networks for which the URLs are extracted."""
    FACEBOOK = ("https://www.facebook.com/",  ["posts/", "videos/", "photos/", "groups/"], "Caption", "URL", "site: facebook.com")
    INSTAGRAM = ("https://www.instagram.com/", ["p/", "tv/", "reel/", "video/", "photo/"], "Caption", "URL", "site: instagram.com")
    
    def get_domain_url(self) -> str:
        return self.value[0]
    
    def get_valid_substrings(self) -> list:
        return self.value[1]
    
    def get_text_column(self) -> str:
        return self.value[2]
    
    def get_url_column(self) -> str:
        return self.value[3]
    
    def get_site_query(self) -> str:
        return self.value[4]
    

def select_social_network(sn: int) -> SocialNetwork:
    """Select the social network based on user input."""
    if sn == 1:
        return SocialNetwork.FACEBOOK
    elif sn == 2:
        return SocialNetwork.INSTAGRAM
    else:
        print("Escolha inválida. Tente novamente.")
        sys.exit(1)
            

def env_variable(var_name: str) -> str:
    """Gets an environment variable or raises an exception if it is not set."""    
    if not (var_value := os.getenv(var_name)):
        raise ValueError(f"Variável de ambiente {var_name} não definida. Verifique o arquivo .env.")
    return var_value

    
def validate_file_extension(file_name: str, extension: str):
    """Check if the file has the correct extension."""
    if not file_name.endswith(extension):
        print(f"Arquivo inválido. O arquivo deve ser um {extension}")
        sys.exit(1) 


def list_files_and_get_input() -> str:
    """List files and get user input for file selection."""
    files = [file for file in os.listdir('.') if os.path.isfile(file) and not file.startswith('.')]
    while True:
        user_input = input("Por favor, insira o nome do arquivo (ou '?' para listar): ")
        if user_input == '?':
            for i, file in enumerate(files, 1):
                print(f"{i}. {file}")
        elif user_input.isdigit():
            file_index = int(user_input) - 1
            if 0 <= file_index < len(files):
                return files[file_index]
            else:
                print("Nome de arquivo inválido. Por favor, tente novamente.")    
        else:
            if user_input in files:
                return user_input
            else:
                print("Nome de arquivo inválido. Por favor, tente novamente.")


def read_posts_from_extraction(file_path: str) -> pd.DataFrame:
    """Reads the CSV file with the posts and returns a DataFrame."""
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {file_path}")
        sys.exit(1)
    except pd.errors.ParserError:
        print(f"Erro ao ler o arquivo: {file_path}")
        sys.exit(1)
    except KeyError as e:
        print(f"Coluna não encontrada: {e}")
        sys.exit(1)    


def filter_bmp_characters(text: str) -> str:
    """Remove characters outside the Basic Multilingual Plane (BMP)."""
    return re.sub(r'[^\u0000-\uFFFF]', '', text)


def google_search(query: str, social_network: SocialNetwork, max_results: int = 5, retries: int = 5) -> str:
    """Searches Google for the query and returns the first relevant URL."""
    params = {
        'q': query,
        'key': API_KEY,
        'cx': CSE_ID,
        'num': max_results
    }
    
    for attempt in range(retries):
        try:
            response = requests.get(API_URL, params=params)
            response.raise_for_status()
            search_results = response.json()
            itens = search_results.get('items', [])
            
            for item in itens:
                link = item['link']
                if social_network.get_domain_url() in link and \
                    any(substring in link for substring in social_network.get_valid_substrings()):
                    return link
            return ""
        
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Erro 429: Muitas requisições. Aguardando {wait_time} segundos antes de tentar novamente...")
                time.sleep(wait_time)
            else:
                print(f"Erro na requisição: {e}")
                return ""
    
    return ""
    

def main():
    global API_KEY
    global CSE_ID
    load_dotenv()
    API_KEY = env_variable("API_KEY")
    CSE_ID = env_variable("CSE_ID")
    
    social_network = select_social_network(int(input("Escolha a rede social:\n1 - Facebook\n2 - Instagram\n")))
    print("Selecione o arquivo de extração (CSV) com os posts:")
    file_name = list_files_and_get_input()
    validate_file_extension(file_name, '.csv')
    
    data_posts = read_posts_from_extraction(file_name)
    data_posts[social_network.get_url_column()] = ''
    
    print("Inicializando busca de URLs...\n")
    search_success = 0
    insuficient_text = 0
    
    for index, row in data_posts.iterrows():
        text = row[social_network.get_text_column()]
        query = f"{social_network.get_site_query()}+{filter_bmp_characters(text)}"
        
        if len(query) < MIN_TEXT_LENGTH:
            print(f"Texto da linha {index + 1} ignorado (comprimento inválido: {len(query)} caracteres)")
            insuficient_text += 1
            continue
        
        url = google_search(query, social_network)
        if url:
            data_posts.at[index, social_network.get_url_column()] = url
            search_success += 1
            print(f"URL encontrada para a linha {index + 1}: {url}")
        else:
            print(f"URL não encontrada para a linha {index + 1}")
    
    print(f"\nBusca finalizada. URLs encontradas: {search_success}/{len(data_posts)}")
    print(f"Posts ignorados por texto insuficiente (menos de {MIN_TEXT_LENGTH} caracteres): {insuficient_text}")
    print(f"Posts pesquisados sem sucesso: {len(data_posts) - search_success - insuficient_text}")
    data_posts.to_csv(f'{file_name[:-4]}_with_urls.csv', index=False)


if __name__ == "__main__":
    main()