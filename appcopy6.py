import networkx as nx
import dash
import sys
import os
import dash_cytoscape as cyt
from dash import html, dcc
from dash.dependencies import Input, Output
from scipy.optimize import linear_sum_assignment
import dash_bootstrap_components as dbc

# Criar um grafo vazio
G = nx.Graph()

# Função para carregar o grafo de um arquivo de texto
def carregar_grafo(arquivo):
    diretorio_atual = os.path.dirname(__file__)
    caminho_arquivo = os.path.join(diretorio_atual, arquivo)
    with open(caminho_arquivo, 'r') as f:
        for linha in f:
            dados = linha.strip().split(',')
            vertice1, vertice2 = dados[0], dados[1]
            
            # Verifica se há um peso especificado
            if len(dados) == 3:
                peso = int(dados[2])
                G.add_edge(vertice1, vertice2, weight=peso)
            else:
                G.add_edge(vertice1, vertice2)

# Função para salvar o grafo em um arquivo de texto
def salvar_grafo(arquivo):
    with open(arquivo, 'w') as f:
        for edge in G.edges():
            f.write(f"{edge[0]},{edge[1]}\n")

# Criar a página web com Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout da página web
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1('Visualização de Grafos'),
            html.Div([
                html.Label('Tipo de Grafo:'),
                dcc.RadioItems(
                    id='tipo-grafo',
                    options=[
                        {'label': 'Não Orientado', 'value': 'undirected'},
                        {'label': 'Orientado', 'value': 'directed'}
                    ],
                    value='undirected'
                ),
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.Label('Peso nas Arestas:'),
                dcc.RadioItems(
                    id='peso-aresta',
                    options=[
                        {'label': 'Sem Peso', 'value': 'none'},
                        {'label': 'Com Peso', 'value': 'weighted'}
                    ],
                    value='none'
                ),
            ], style={'marginBottom': '20px'}),
            
            html.Div([
                html.Button('Carregar Grafo', id='carregar-grafo', n_clicks=0),
                html.Button('Salvar Grafo', id='salvar-grafo', n_clicks=0),
                html.Button('Adicionar Vértice', id='adicionar-vertice', n_clicks=0),
                html.Button('Remover Vértice', id='remover-vertice', n_clicks=0),
                html.Button('Adicionar Aresta', id='adicionar-aresta', n_clicks=0),
                html.Button('Remover Aresta', id='remover-aresta', n_clicks=0),
                html.Button('Executar BFS', id='bfs', n_clicks=0),
                html.Button('Executar DFS', id='dfs', n_clicks=0),
            ], style={'marginBottom': '20px'}),
            
            html.Div(id='grafo-info', style={'marginTop': '20px'})

        ], width=3),
        
        dbc.Col([
            cyt.Cytoscape(
                id='grafo',
                layout={'name': 'cose'},
                style={'width': '100%', 'height': '800px'},
                elements=[],
            ),
        ], width=9),
    ]),
], fluid=True)

def calcular_informacoes_grafo():
    num_vertices = len(G.nodes())
    num_arestas = len(G.edges())
    orientado = 'Sim' if isinstance(G, nx.DiGraph) else 'Não'
    ponderado = 'Sim' if any('weight' in G[u][v] for u, v in G.edges()) else 'Não'
    return [
        html.Div(f"Número de Vértices: {num_vertices}"),
        html.Div(f"Número de Arestas: {num_arestas}"),
        html.Div(f"É Orientado: {orientado}"),
        html.Div(f"É Ponderado: {ponderado}")
    ]


# Função do emparelhamento max
def maximum_matching(G):    
    matching = nx.max_weight_matching(G, maxcardinality=True)
    return matching

def adicionar_vertice_bipartido(G):
    # Identificar os conjuntos existentes
    conjunto1 = sorted([n for n, d in G.nodes(data=True) if d.get('bipartite') == 0])
    conjunto2 = sorted([n for n, d in G.nodes(data=True) if d.get('bipartite') == 1])

    # Verificar o próximo vértice para cada conjunto
    if len(conjunto1) <= len(conjunto2):
        # Adicionar um vértice com uma letra para o conjunto1 (alfabético)
        if conjunto1:
            proximo_vertice = chr(ord(conjunto1[-1]) + 1)
        else:
            proximo_vertice = 'A'
        G.add_node(proximo_vertice, bipartite=0)
    else:
        # Adicionar um vértice numérico para o conjunto2
        if conjunto2:
            proximo_vertice = str(len(conjunto2) + 1)
        else:
            proximo_vertice = '1'
        G.add_node(proximo_vertice, bipartite=1)
    
    return proximo_vertice

# Função para atualizar o grafo quando um botão é clicado
@app.callback(
    [Output('grafo', 'elements'),
    Output('grafo-info', 'children')], 
    [Input('carregar-grafo', 'n_clicks'),
     Input('salvar-grafo', 'n_clicks'),
     Input('adicionar-vertice', 'n_clicks'),
     Input('remover-vertice', 'n_clicks'),
     Input('adicionar-aresta', 'n_clicks'),
     Input('remover-aresta', 'n_clicks'),
     Input('grafo', 'selectedNodeData'),
     Input('tipo-grafo', 'value'),
     Input('peso-aresta', 'value'),
     Input('grafo', 'selectedEdgeData')]             
     
)
def atualizar_grafo(n_clicks_carregar_grafo, salvar_grafo, adicionar_vertice, remover_vertice, adicionar_aresta, remover_aresta, selectedNodeData,  tipo_grafo, peso_aresta, selectedEdgeData):
    global G
    ctx = dash.callback_context
    if ctx.triggered:
        prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

                # Atualiza o tipo de grafo
        if prop_id == 'tipo-grafo':
            if tipo_grafo == 'directed':
                G = nx.DiGraph()  
            else:
                G = nx.Graph()    

        # Atualiza o peso das arestas
        if prop_id == 'peso-aresta':
            if peso_aresta == 'weighted':
                for u, v in G.edges():
                    G[u][v]['weight'] = 1  
            else:
                for u, v in G.edges():
                    if 'weight' in G[u][v]:
                        del G[u][v]['weight']  


        if prop_id == 'carregar-grafo':
            G.clear()
            carregar_grafo('grafo.txt')
        elif prop_id == 'salvar-grafo':
            salvar_grafo('grafo.txt')
        elif prop_id == 'adicionar-vertice':
            vertices_ordenados = sorted(list(G.nodes()))
            proximo_vertice = chr(ord(vertices_ordenados[-1])+1)
            G.add_node(proximo_vertice)
        elif prop_id == 'remover-vertice':
            if selectedNodeData:
                vertice_selecionado = selectedNodeData[0]['id']
                if vertice_selecionado in G.nodes():
                    G.remove_node(vertice_selecionado)
        elif prop_id == 'adicionar-aresta':
            if selectedNodeData and len(selectedNodeData) == 2:
                vertice1 = selectedNodeData[0]['id']
                vertice2 = selectedNodeData[1]['id']
                if not G.has_edge(vertice1, vertice2):
                    if peso_aresta == 'weighted':
                        G.add_edge(vertice1, vertice2, weight=1)  
                    else:
                        G.add_edge(vertice1, vertice2)
        elif prop_id == 'remover-aresta':
            if selectedEdgeData:
                edge_selecionada = selectedEdgeData[0]
                source = edge_selecionada['source']          
                target = edge_selecionada['target']
                if G.has_edge(source, target):
                    G.remove_edge(source, target)

    elementos_grafo = [{'data': {'id': node, 'label': node}} for node in G.nodes()] + \
                      [{'data': {'id': edge[0] + edge[1], 'source': edge[0], 'target': edge[1], 'weight': G[edge[0]][edge[1]].get('weight', '')}} for edge in G.edges()]
    
    informacoes_grafo = calcular_informacoes_grafo()


    return elementos_grafo, informacoes_grafo
    
# Executar a aplicação
if __name__ == '__main__':
    app.run_server(debug=True, port=8130)