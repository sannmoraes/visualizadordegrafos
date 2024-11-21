import networkx as nx
import dash
import sys
import os
import dash_cytoscape as cyt
from dash import html, dcc
from dash.dependencies import Input, Output, State
from scipy.optimize import linear_sum_assignment
import dash_bootstrap_components as dbc

# Criar um grafo vazio
G = nx.Graph()

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
            
                        
            html.Div([
                html.Label('Peso da Aresta:'),
                dcc.Input(id='peso-aresta-input', type='number', value=1),
                html.Button('Aplicar Peso', id='aplicar-peso', n_clicks=0),
            ], style={'marginBottom': '20px'}),


            html.Div(id='grafo-info', style={'marginTop': '20px'})

        ], width=3),
        
        dbc.Col([
            cyt.Cytoscape(
                id='grafo',
                layout={'name': 'cose'},
                style={'width': '100%', 'height': '800px'},
                elements=[],
                minZoom=0.5,
                maxZoom=2,
                
            ),
        ], width=9),
    ]),
], fluid=True)


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

def salvar_grafo(arquivo):
    with open(arquivo, 'w') as f:
        for edge in G.edges():
            f.write(f"{edge[0]},{edge[1]}\n")

def calcular_informacoes_grafo():
    num_vertices = len(G.nodes())
    num_arestas = len(G.edges())
    orientado = 'Sim' if isinstance(G, nx.DiGraph) else 'Não'
    ponderado = 'Sim' if any('weight' in G[u][v] for u, v in G.edges()) else 'Não'
    return f"Número de Vértices: {num_vertices} Número de Arestas: {num_arestas} É Orientado: {orientado} É Ponderado: {ponderado}"

# trocar a funcao para 2 seminario
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

def busca_bfs(grafo, start):
    visited = []
    queue = [start]
    edges_visited = set()
    while queue:
        vertex = queue.pop(0)
        if vertex not in visited:
            visited.append(vertex)
            neighbors = grafo.successors(vertex) if isinstance(grafo, nx.DiGraph) else grafo.neighbors(vertex)
            for neighbor in neighbors:
                if neighbor not in visited:
                    queue.append(neighbor)
                    if isinstance(grafo, nx.DiGraph):
                        edges_visited.add((vertex, neighbor))
                    else:
                        edges_visited.add((vertex, neighbor))
                        edges_visited.add((neighbor, vertex))  
    return visited, edges_visited


def busca_dfs(grafo, start):
    visited = []
    stack = [start]
    edges_visited = set()
    while stack:
        vertex = stack.pop()
        if vertex not in visited:
            visited.append(vertex)
        neighbors = grafo.successors(vertex) if isinstance(grafo, nx.DiGraph) else grafo.neighbors(vertex)
        for neighbor in neighbors:
            if neighbor not in visited:
                stack.append(neighbor)
                if isinstance(grafo, nx.DiGraph):
                    edges_visited.add((vertex, neighbor))
                else:
                    edges_visited.add((vertex, neighbor))
                    edges_visited.add((neighbor, vertex))
        for i in grafo.neighbors(vertex):  
            if i not in visited:
                visited.append(i)     
        print(edges_visited)
    return visited, edges_visited

@app.callback(
    [Output('grafo', 'elements'),
    Output('grafo', 'stylesheet'),
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
     Input('grafo', 'selectedEdgeData'),
     Input('bfs', 'n_clicks'),
     Input('dfs', 'n_clicks'),
     Input('aplicar-peso', 'n_clicks')],
     [State('peso-aresta-input', 'value')]    
)



def atualizar_grafo(n_clicks_carregar_grafo, salvar_grafo_clicks, adicionar_vertice, remover_vertice, adicionar_aresta, remover_aresta, selectedNodeData, tipo_grafo, peso_aresta, selectedEdgeData,  n_clicks_bfs, n_clicks_dfs, n_clicks_aplicar_peso, peso_entrada):
    global G
    pesos_originais = {}
    pesos_atualizados = {}  
    ctx = dash.callback_context
    informacoes_grafo = calcular_informacoes_grafo()
    stylesheet = [
        {
            'selector': 'edge',
            'style': {
                'width': 8,
                'target-arrow-shape': 'triangle' if tipo_grafo == 'directed' else 'none',
                'curve-style': 'bezier',
                'label': 'data(label)',
                'font-size': '16px',
                'text-background-color': '#fff',
                'text-background-opacity': 0.7,
                'color': '#000'
            }
        },
        {
            'selector': 'node',
            'style': {
                'label': 'data(label)',
                'color': '#000',
                'width': '60px',
                'height': '60px'
            }
        }
    ]
    if ctx.triggered:
        prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

                # Atualiza o tipo de grafo
        if prop_id == 'tipo-grafo':
            novos_nos = G.nodes(data=True)
            novas_arestas = G.edges(data=True)
            if tipo_grafo == 'directed':
                novo_G = nx.DiGraph()
            else:
                 novo_G = nx.Graph()
    
            novo_G.add_nodes_from(novos_nos)
            novo_G.add_edges_from(novas_arestas)
    
            G = novo_G
            informacoes_grafo = calcular_informacoes_grafo()        

        # Atualiza o peso das arestas
        if prop_id == 'peso-aresta':
            if peso_aresta == 'none':
                for u, v in G.edges():  
                    if 'weight' in G[u][v]:
                        pesos_originais[(u, v)] = G[u][v]['weight']
                for u, v in G.edges():
                    if 'weight' in G[u][v]:
                        del G[u][v]['weight']

            elif peso_aresta == 'weighted':
                for u, v in G.edges():
                    if (u, v) in pesos_originais:
                        G[u][v]['weight'] = pesos_originais[(u, v)]
                    elif (v, u) in pesos_originais:
                        G[u][v]['weight'] = pesos_originais[(v, u)]
                    else:
                        G[u][v]['weight'] = 1

        if prop_id == 'carregar-grafo':
            G.clear()
            carregar_grafo('grafo.txt')
            for u, v in G.edges():
                if 'weight' in G[u][v]:
                    pesos_originais[(u, v)] = G[u][v]['weight']        

        elif prop_id == 'salvar-grafo':
            salvar_grafo('grafo.txt')
            for u, v in G.edges():
                if 'weight' in G[u][v]:
                    pesos_originais[(u, v)] = G[u][v]['weight']

        elif prop_id == 'adicionar-vertice':
            vertices_ordenados = sorted(list(G.nodes()))
            proximo_vertice = chr(ord(vertices_ordenados[-1])+1) if vertices_ordenados else 'A'
            G.add_node(proximo_vertice)
            informacoes_grafo = calcular_informacoes_grafo()

        elif prop_id == 'remover-vertice':
            if selectedNodeData:
                for node in selectedNodeData:
                   vertice_selecionado = node['id']
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
               for edge_selecionada in selectedEdgeData:
                source = edge_selecionada['source']          
                target = edge_selecionada['target']
                if G.has_edge(source, target):
                    G.remove_edge(source, target)

        elif prop_id == 'aplicar-peso':
            if selectedEdgeData:                
               for edge_selecionada in selectedEdgeData:
                source = edge_selecionada['source']
                target = edge_selecionada['target']
                
                if isinstance(G, nx.DiGraph):
                    edge = (source, target)
                else:
                    edge = (min(source, target), max(source, target))
                
                if edge in G.edges():
                    G[edge[0]][edge[1]]['weight'] = peso_entrada                    
                    for u, v in G.edges():
                        if (u, v) != edge:
                            if 'weight' not in G[u][v]:
                                G[u][v]['weight'] = 1



        elif prop_id == 'bfs':
            if selectedNodeData:
                start_node = selectedNodeData[0]['id']
                visitados, bfs_edges = busca_bfs(G, start_node)
                stylesheet += [
                    {
                        'selector': f'node[id="{node}"]',
                        'style': {
                            'background-color': 'lightblue'
                        }
                    } for node in visitados
                ]
                if isinstance(G, nx.DiGraph):                
                    stylesheet += [
                    {
                        'selector': f'edge[id="{edge[0]}-{edge[1]}"]',
                        'style': {
                            'line-color': 'red',
                            'width': 3
                        }
                    } for edge in bfs_edges
                ]
                else:
                   stylesheet += [
                    {
                        'selector': f'edge[id="{edge[0]}-{edge[1]}"]',
                        'style': {
                            'line-color': 'red',
                            'width': 3
                        }
                    } for edge in bfs_edges                    
                 ]
                informacoes_grafo = f"{calcular_informacoes_grafo()}  BFS Iniciado no Vértice: {start_node}  Vértices Visitados: {', '.join(visitados)}" 

        elif prop_id == 'dfs':
            if selectedNodeData:
                start_node = selectedNodeData[0]['id']
                visitados, dfs_edges = busca_dfs(G, start_node)                
                stylesheet += [
                    {
                        'selector': f'node[id="{node}"]',
                        'style': {
                            'background-color': 'lightcoral'
                        }
                    } for node in visitados
                ]
                if isinstance(G, nx.DiGraph):    
                    stylesheet += [
                        {
                            'selector': f'edge[id="{edge[0]}-{edge[1]}"]',
                            'style': {
                                'line-color': 'red',
                                'width': 3
                             }
                    } for edge in dfs_edges
                ]
                else:
                   stylesheet += [
                    {
                        'selector': f'edge[id="{edge[0]}-{edge[1]}"]',
                        'style': {
                            'line-color': 'red',
                            'width': 3
                        }
                    } for edge in dfs_edges                    
                 ]               
                informacoes_grafo = f"{calcular_informacoes_grafo()}  DFS Iniciado no Vértice: {start_node}  Vértices Visitados: {', '.join(visitados)}"

    elementos_grafo = [{'data': {'id': node, 'label': node}} for node in G.nodes()] + \
                   [{'data': {'id': f"{edge[0]}-{edge[1]}", 'source': edge[0], 'target': edge[1], 'label': str(G[edge[0]].get(edge[1], {}).get('weight', ''))}} for edge in G.edges()]
    
    


    return elementos_grafo, stylesheet, informacoes_grafo 
    
# Executar a aplicação
if __name__ == '__main__':
    app.run_server(debug=True, port=6979)