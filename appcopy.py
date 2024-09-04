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
            vértice1, vértice2 = linha.strip().split(',')
            G.add_edge(vértice1, vértice2)

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

])

def maximum_matching(G):
    # Compute the maximum matching using the Hopcroft-Karp algorithm
    matching = nx.max_weight_matching(G, maxcardinality=True)
    return [(u, v) if u < v else (v, u) for u, v in matching]


# Função para atualizar o grafo quando um botão é clicado
@app.callback(
    Output('grafo', 'elements'),
    [Input('carregar-grafo', 'n_clicks'),
     Input('salvar-grafo', 'n_clicks'),
     Input('adicionar-vertice', 'n_clicks'),
     Input('remover-vertice', 'n_clicks'),
     Input('adicionar-aresta', 'n_clicks'),
     Input('remover-aresta', 'n_clicks'),
     Input('grafo', 'selectedNodeData')]     
     
)
def atualizar_grafo(n_clicks_carregar_grafo, salvar_grafo, adicionar_vertice, remover_vertice, adicionar_aresta, remover_aresta, selectedNodeData):
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
            vertices_ordenados = sorted(list(G.nodes()))
            proximo_vertice = chr(ord(vertices_ordenados[-1])+1)
            G.add_node(proximo_vertice)
        elif prop_id == 'remover-vertice':
            if selectedNodeData:
                vertice_selecionado = selectedNodeData[0]['id']
                if vertice_selecionado in G.nodes():
                    G.remove_node(vertice_selecionado)
        elif prop_id == 'adicionar-aresta':
            if selectedNodeData:
                vertice_selecionado = selectedNodeData[0]['id']
                for edge in matching:
                    if vertice_selecionado in edge:
                        G.add_edge(*edge)
        elif prop_id == 'remover-aresta':
            if selectedNodeData:
                aresta_selecionada = [(edge['data']['source'], edge['data']['target']) for edge in selectedNodeData]
                for edge in aresta_selecionada:
                    if edge in G.edges():
                        G.remove_edge(*edge)
    return [{'data': {'id': node, 'label': node}} for node in G.nodes()] + [{'data': {'id': edge[0] + edge[1], 'source': edge[0], 'target': edge[1]}} for edge in G.edges()]

# Executar a aplicação
if __name__ == '__main__':
    app.run_server(debug=True, port=8112)