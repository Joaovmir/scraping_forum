import streamlit as st

import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

@st.cache
def scraping_dados():
    url_api = 'https://cursos.alura.com.br/api/categorias'
    req = requests.get(url_api)
    if req.status_code == 200:
        dados_api = req.json()
    else:
        print('Sem resposta!')

    url_alura = 'https://cursos.alura.com.br/forum'

    def acessar_url(url):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36'}
        req = Request(url, headers = headers)
        response = urlopen(req)
        html = response.read().decode('utf-8')
        soup = BeautifulSoup(html, 'html.parser')
        return soup

    def contagem_topicos(tipo):
        try:
            ult_pag = soup.find('nav', {'class' :'busca-paginacao-links'}).get_text().split()[-1]
            if tipo == 'Subcategoria':
                url = f"{url_alura}/subcategoria-{subcategoria['slug']}/sem-resposta/{ult_pag}"
            elif tipo == 'Área de estudo':
                url = f"{url_alura}/categoria-{categoria['slug']}/sem-resposta/{ult_pag}"
            soupcatult = acessar_url(url)
            num_top = len(soupcatult.find_all('div', {'class': {'forumList-item-subject'}}))
            num_ult_pag = int(ult_pag)
            qtd_topicos = (num_top + (num_ult_pag-1)*20)
            if tipo == 'Subcategoria':
                linha['qtd_topicos'] = qtd_topicos
            elif tipo == 'Área de estudo':
                soma_sub = int(tabela_areas_estudo.query(f"area_estudo =='{categoria['nome']}'")['qtd_topicos'])
                linha['qtd_topicos'] = qtd_topicos - soma_sub
        except:
            qtd_topicos = len(soup.find_all('div', {'class': {'forumList-item-subject'}}))
            if tipo == 'Subcategoria':
                linha['qtd_topicos'] = qtd_topicos
            elif tipo == 'Área de estudo':
                soma_sub = int(tabela_areas_estudo.query(f"area_estudo =='{categoria['nome']}'")['qtd_topicos'])
                linha['qtd_topicos'] = qtd_topicos - soma_sub

    dados = []
    for categoria in dados_api:
        dataframe = []
        for subcategoria in categoria['subcategorias']:
            linha = {}
            linha['categoria'] = subcategoria['nome']
            linha['area_estudo'] = categoria['nome']
            url = f"{url_alura}/subcategoria-{subcategoria['slug']}/sem-resposta"
            soup = acessar_url(url)
            contagem_topicos('Subcategoria')
            dataframe.append(linha)
            dados.append(linha)
        tabela_areas_estudo = pd.DataFrame(dataframe)
        tabela_areas_estudo = tabela_areas_estudo.groupby('area_estudo').sum().sort_values(by='qtd_topicos',ascending=False)
        linha = {}
        linha['categoria'] = f"Sem subcategoria - {categoria['nome']}"
        linha['area_estudo'] = categoria['nome']
        url = f"{url_alura}/categoria-{categoria['slug']}/sem-resposta"
        soup = acessar_url(url)
        contagem_topicos('Área de estudo')
        dados.append(linha)
        
    dados = pd.DataFrame(dados)
    return dados

@st.cache 
def carrega_csv():
    dados = pd.read_csv('dados/topicos_sem_resposta.csv', encoding='utf-8-sig')
    return dados

def mostra_top(qtd):
    dados.sort_values(by= 'Tópicos sem resposta', ascending=False, inplace=True)

    sns.set_style('darkgrid')
    sns.set_context("notebook", font_scale=1.2)
    ax = sns.barplot(x='Tópicos sem resposta',y= 'Categoria', data = dados.head(qtd))
    ax.figure.set_size_inches(14,6)
    ax.set_title('Subcategorias com mais tópicos sem resposta', fontsize = 18)
    ax.set_xlabel('Quantidade', fontsize = 14)
    ax.set_ylabel('Categoria', fontsize = 14)
    return ax.figure

def mostra_top_qtd(qtd):
    st.dataframe(dados.head(qtd))


def mostra_areas_estudo():
    sns.set_style('darkgrid')
    sns.set_context("notebook", font_scale=1.2)
    ax = sns.barplot(x='Tópicos sem resposta', y= tabela_areas_estudo.index,  data = tabela_areas_estudo)
    ax.figure.set_size_inches(14,6)
    ax.set_title('Tópicos sem resposta por área de estudo', fontsize = 18)
    ax.set_xlabel('Quantidade', fontsize = 14)
    ax.set_ylabel('Categoria', fontsize = 14)
    return ax.figure

def mostra_areas_estudo_tabela():
    st.dataframe(tabela_areas_estudo)

def mostra_dados(filtro):
    if filtro == 'Geral':
        st.dataframe(dados)
    else:
        st.dataframe(dados[dados['Área de estudo'] == filtro])

st.title('Scraping Fórum Alura')
base_dados = st.selectbox('De onde deseja carregar os dados?', ['Usar última base de dados','Realizar novo scraping (2 min carregamento)'])

if base_dados == 'Realizar novo scraping (2 min carregamento)':
    dados = scraping_dados()
    dados.columns = ['Categoria', 'Área de estudo', 'Tópicos sem resposta']
    tabela_areas_estudo = dados.groupby('Área de estudo').sum().sort_values(by='Tópicos sem resposta',ascending=False)
elif base_dados == 'Usar última base de dados':
    dados = carrega_csv()
    dados.columns = ['Categoria', 'Área de estudo', 'Tópicos sem resposta']
    tabela_areas_estudo = dados.groupby('Área de estudo').sum().sort_values(by='Tópicos sem resposta',ascending=False)

opcao = st.sidebar.selectbox('O que deseja ver?', ['Áreas de estudo', 'Subcategorias','Todos os dados'])

if opcao == 'Subcategorias':
    quantidade = st.sidebar.slider('Escolha a quantidade de subcategorias', 5, 20, 5)
    st.subheader(f'Tópicos sem resposta por subcategoria - Top {quantidade}')
    figura1 = mostra_top(quantidade)
    st.pyplot(figura1)
    mostra_top_qtd(quantidade)
elif opcao == 'Áreas de estudo':
    st.subheader('Tópicos sem resposta por área de estudo')
    figura2 = mostra_areas_estudo()
    st.pyplot(figura2)
    mostra_areas_estudo_tabela()
elif opcao == 'Todos os dados':
    st.subheader('Tópicos sem resposta por subcategoria')
    filtros = list(dados['Área de estudo'].unique())
    filtros.insert(0, 'Geral')
    filtragem = st.selectbox('Filtros', filtros)
    mostra_dados(filtragem)

if st.sidebar.button("Limpar cache"):
    st.caching.clear_cache()
