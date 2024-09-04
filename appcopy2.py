import networkx as nx
import dash
import os
import dash_cytoscape as cyt
from dash import html, dcc
from dash.dependencies import Input, Output
from scipy.optimize import linear_sum_assignment

# Criar um grafo vazio
G = nx.Graph()

# Função para carregar o grafo de um arquivo de texto
def carregar_grafo(arquivo):
    diretorio_atual = os.path.dirname(__file__)
    caminho_arquivo = os.path.join(diretorio_atual, arquivo)
    with open(caminho_arquivo, 'r') as f:
        for linha in f:
            vertice1, vertice2 = linha.strip().split(',')
            # Adiciona vértices com o atributo bipartite
            if vertice1.isalpha():
                G.add_node(vertice1, bipartite=0)
            else:
                G.add_node(vertice1, bipartite=1)
            if vertice2.isalpha():
                G.add_node(vertice2, bipartite=0)
            else:
                G.add_node(vertice2, bipartite=1)
            G.add_edge(vertice1, vertice2)

# Função para salvar o grafo em um arquivo de texto
def salvar_grafo(arquivo):
    with open(arquivo, 'w') as f:
        for edge in G.edges():
            f.write(f"{edge[0]},{edge[1]}\n")

# Criar a página web com Dash
app = dash.Dash(__name__)

# Layout da página web
app.layout = html.Div([
    html.H1('Visualização de Grafos'),
    cyt.Cytoscape(
        id='grafo',
        layout={'name': 'cose'},
        style={'width': '100%', 'height': '800px'},
        elements=[],
 
    ),
    html.Button('Carregar Grafo', id='carregar-grafo', n_clicks=0),
    html.Button('Salvar Grafo', id='salvar-grafo', n_clicks=0),
    html.Button('Adicionar Vértice', id='adicionar-vertice', n_clicks=0),
    html.Button('Remover Vértice', id='remover-vertice', n_clicks=0),       
    html.Button('Adicionar Aresta', id='adicionar-aresta', n_clicks=0),
    html.Button('Remover Aresta', id='remover-aresta', n_clicks=0),

    # Seção para exibir informações do grafo
    html.Div(id='grafo-info', style={'marginTop': 20}),
])

# Função para calcular e exibir as informações do grafo
def calcular_informacoes_grafo(G):
    num_vertices = G.number_of_nodes()
    num_arestas = G.number_of_edges()
    orientado = "Sim" if G.is_directed() else "Não"
    ponderado = "Sim" if nx.is_weighted(G) else "Não"

    info = f"Número de Vértices: {num_vertices}<br>" \
           f"Número de Arestas: {num_arestas}<br>" \
           f"É Orientado: {orientado}<br>" \
           f"É Ponderado: {ponderado}"

    return info

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
     Input('grafo', 'selectedEdgeData')]             
     
)
def atualizar_grafo(n_clicks_carregar_grafo, salvar_grafo, adicionar_vertice, remover_vertice, adicionar_aresta, remover_aresta, selectedNodeData, selectedEdgeData):
    ctx = dash.callback_context
    if ctx.triggered:
        prop_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if prop_id == 'carregar-grafo':
            G.clear()
            carregar_grafo('grafo.txt')
            matching = maximum_matching(G)
            for edge in matching:
                G.add_edge(*edge)
        elif prop_id == 'salvar-grafo':
            salvar_grafo('grafo.txt')
        elif prop_id == 'adicionar-vertice':
            adicionar_vertice_bipartido(G)
        elif prop_id == 'remover-vertice':
            if selectedNodeData:
                vertice_selecionado = selectedNodeData[0]['id']
                if vertice_selecionado in G.nodes():
                    G.remove_node(vertice_selecionado)
        elif prop_id == 'adicionar-aresta':
            if selectedNodeData and len(selectedNodeData) == 2:
                source = selectedNodeData[0]['id']
                target = selectedNodeData[1]['id']
                if G.nodes[source].get('bipartite') != G.nodes[target].get('bipartite'):
                    # Adiciona a aresta se ainda não existir
                    if not G.has_edge(source, target):
                        G.add_edge(source, target)
        elif prop_id == 'remover-aresta':
            if selectedEdgeData:
                edge_selecionada = selectedEdgeData[0]
                source = edge_selecionada['source']          
                target = edge_selecionada['target']
                if G.has_edge(source, target):
                    G.remove_edge(source, target)

    return [{'data': {'id': node, 'label': node}} for node in G.nodes()] + \
           [{'data': {'id': edge[0] + edge[1], 'source': edge[0], 'target': edge[1]}} for edge in G.edges()]

# Executar a aplicação
if __name__ == '__main__':
    app.run_server(debug=True, port=8125)