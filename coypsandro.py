import networkx as nx
import dash
import sys
import os
import dash_cytoscape as cyto
from dash import html, dcc
from dash.dependencies import Input, Output, State
from scipy.optimize import linear_sum_assignment
import dash_bootstrap_components as dbc

# Criar um grafo vazio
G = nx.Graph()
graph_type = {'directed': False, 'weighted': False}

# Criar a página web com Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


def parse_graph_data(contents, directed=False, weighted=False):
    """Parse the graph data from the .txt file and create the NetworkX graph."""
    lines = contents.strip().splitlines()
    edges = []
    
    for line in lines:
        vertices = line.split(',')
        vertices = [v.strip() for v in vertices]
        if len(vertices) == 2:
            edges.append((vertices[0], vertices[1]))
    
    G = nx.DiGraph() if directed else nx.Graph()
    if weighted:
        for edge in edges:
            G.add_edge(edge[0], edge[1], weight=1.0)  # Adiciona peso default de 1.0
    else:
        G.add_edges_from(edges)
    
    return G

# Layout da página web
app.layout = dbc.Container([
    dbc.Row(
        dbc.Col([
            html.Header(
                children=[
                    html.Div(
                        children=[
                            html.Img(src='/assets/diagram-3-fill.svg', alt='Ícone de Grafo', style={'height': '60px', 'margin-right': '10px'}),
                            html.H1("REPRESENTAÇÃO DE GRAFOS", style={'margin': '0', 'font-size': '2rem'})
                        ],
                        style={
                            'display': 'flex',
                            'align-items': 'center',
                            'justify-content': 'center'
                        }
                    )
                ],
                style={
                    'display': 'flex',
                    'align-items': 'center',
                    'justify-content': 'center',
                    'padding': '20px',
                    'background-color': '#f8f9fa'
                }
            )
        ])
    ),

    #botões centralizados com flexbox
    dbc.Row([
        dbc.Col([
            html.Div(
                dbc.ButtonGroup(
                    [

                        #dropdown para o botão "Grafo" com imagem
                        dbc.DropdownMenu(
                            label=[
                                html.Img(src='/assets/gear.svg', style={'height': '20px', 'margin-right': '5px'}),
                                "Grafo"
                            ],
                            children=[
                                dcc.Upload(
                                    id='upload-data',
                                    children=dbc.DropdownMenuItem([
                                        html.Img(src='/assets/upload.svg', style={'height': '20px', 'margin-right': '5px'}),
                                        "Carregar Grafo"
                                    ]),
                                    multiple=False,
                                ),

                                dbc.Col(dbc.Switch(id='directed-switch', label='Orientado', value=graph_type['directed']), width=4),
                                dbc.Col(dbc.Switch(id='weighted-switch', label='Ponderado', value=graph_type['weighted']), width=4),

                                html.Div(id='output-data-upload'),

                                dcc.Download(id="download-file"),
                                dbc.DropdownMenuItem([
                                    html.Img(src='/assets/save.svg', style={'height': '20px', 'margin-right': '5px'}),
                                    "Baixar Grafo"
                                ], id="btn-download")

                            ],
                            toggle_style={'margin': '0 10px', 'border-radius': '15px'},
                            style={'margin-right': '10px'}
                        ),
                        
                        # Outros botões
                        dbc.Button([html.Img(src='/assets/plus-lg.svg', style={'height': '20px', 'margin-right': '5px'}), "Adicionar Vértice"], color="success", style={'margin': '0 10px', 'border-radius': '15px'}, id='adicionar-vertice', n_clicks=0),
                        dbc.Button([html.Img(src='/assets/plus-lg.svg', style={'height': '20px', 'margin-right': '5px'}), "Remover Vértice"], color="danger", style={'margin': '0 10px', 'border-radius': '15px'}, id='remover-vertice', n_clicks=0),
                        dbc.Button([html.Img(src='/assets/arrows-vertical.svg', style={'height': '20px', 'margin-right': '5px'}), "Conectar Vértices"], color="success", style={'margin': '0 10px', 'border-radius': '15px'}, id='adicionar-aresta', n_clicks=0),
                        dbc.Button([html.Img(src='/assets/arrows-vertical.svg', style={'height': '20px', 'margin-right': '5px'}), "Remover Arestas"], color="danger", style={'margin': '0 10px', 'border-radius': '15px'}, id='remover-aresta', n_clicks=0),
                        
                        # Dropdown para o botão "Algoritmo" com imagem
                        dbc.DropdownMenu(
                            label=[
                                html.Img(src='/assets/gear.svg', style={'height': '20px', 'margin-right': '5px'}),
                                "Algoritmo"
                            ],
                            children=[
                                dbc.DropdownMenuItem("BFS", href="#", id='bfs', n_clicks=0),
                                dbc.DropdownMenuItem("DFS", href="#", id='dfs', n_clicks=0),
                            ],
                            toggle_style={'margin': '0 10px', 'border-radius': '15px'},
                            style={'margin-right': '10px'}
                        ),
                    ],
                    style={'display': 'flex', 'justify-content': 'center'}  # Centraliza os botões
                ),
                style={'display': 'flex', 'justify-content': 'center', 'margin-top': '20px'}
            ),

            html.Div([
                html.Label('Peso da Aresta:'),
                dcc.Input(id='peso-aresta-input', type='number', value=1),
                html.Button('Aplicar Peso', id='aplicar-peso', n_clicks=0),
            ], style={'marginBottom': '20px'}),
            
        ]),

    ]),

    dbc.Row(
        dbc.Col([
            html.Div(id="grafo-info")
        ], width="auto"),  # Ajusta o tamanho da coluna automaticamente
        justify="center"
    ),

    # Quadro para representação do grafo
    dbc.Row(
        dbc.Col(
            cyto.Cytoscape(
                id='grafo',
                layout={'name': 'cose', 'animate': True},  # Usando o layout "cose" com animação
                style={
                    'width': '100%',
                    'height': '500px',
                    'border': '2px solid black',  # Adicionando a borda ao redor do gráfico
                    'margin-top': '30px'  # Adicionando uma distância entre os botões e a visualização
                },
                elements=[],
                stylesheet=[
                    {
                        'selector': '[label]',
                        'style': {
                            'label': 'data(label)',
                            'text-rotation': 'autorotate',
                            'font-size': '12',
                            'text-background-shape': 'roundrectangle'
                        }
                    },
                    {
                        'selector': 'node',
                        'style': {
                            'content': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'font-size': '14px',
                            'width': '30px',
                            'height': '30px'
                        }
                    }
                ],
                minZoom = 1.0,
                maxZoom = 4.0,
            ),
            width={"size": 10, "offset": 1}  # Centraliza o quadro
        )
    )
], fluid= True)



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
    return visited, edges_visited

@app.callback(
    [Output('grafo', 'elements'),
    Output('grafo', 'stylesheet'),
    Output('grafo-info', 'children')], 
    [Input('upload-data', 'contents'),
     #Input('btn-download', 'n_clicks'),
     Input('adicionar-vertice', 'n_clicks'),
     Input('remover-vertice', 'n_clicks'),
     Input('adicionar-aresta', 'n_clicks'),
     Input('remover-aresta', 'n_clicks'),
     Input('grafo', 'selectedNodeData'),
     Input('directed-switch', 'value'),
     Input('weighted-switch', 'value'),
     Input('grafo', 'selectedEdgeData'),
     Input('bfs', 'n_clicks'),
     Input('dfs', 'n_clicks'),
     Input('aplicar-peso', 'n_clicks')],
     [State('peso-aresta-input', 'value')]    
)



def atualizar_grafo(n_clicks_carregar_grafo, adicionar_vertice, remover_vertice, adicionar_aresta, remover_aresta, selectedNodeData, tipo_grafo, peso_aresta, selectedEdgeData,  n_clicks_bfs, n_clicks_dfs, n_clicks_aplicar_peso, peso_entrada):
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
                'line-color': '#888',
                'target-arrow-color': '#888',
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
                'background-color': '#0d0d0d',
                'color': '#000',
                'width': '60px',
                'height': '60px'
            }
        }
    ]
    if ctx.triggered:
        prop_id = ctx.triggered[0]['prop_id'].split('.')[0]

                # Atualiza o tipo de grafo
        if prop_id == 'directed-switch':
            novos_nos = G.nodes(data=True)
            novas_arestas = G.edges(data=True)
    
            if value:  # Se o switch está ligado, o grafo deve ser orientado
                novo_G = nx.DiGraph()
            else:  # Se o switch está desligado, o grafo é não orientado
                novo_G = nx.Graph()
    
            novo_G.add_nodes_from(novos_nos)
            novo_G.add_edges_from(novas_arestas)

            G = novo_G

        # Atualiza o peso das arestas
        if prop_id == 'weighted-switch':  # Verifica se o switch foi acionado
            if not is_weighted:  # Se o switch está desligado, remover pesos das arestas
                for u, v in G.edges():
                    if 'weight' in G[u][v]:
                        del G[u][v]['weight']

        else:  # Se o switch está ligado, restaurar pesos das arestas
            for u, v in G.edges():
                if (u, v) in pesos_originais:
                    G[u][v]['weight'] = pesos_originais[(u, v)]
                elif (v, u) in pesos_originais:
                    G[u][v]['weight'] = pesos_originais[(v, u)]

        if prop_id == 'carregar-grafo':
            G.clear()
            parse_graph_data(G, graph_type['directed'], graph_type['weighted'])
            for u, v in G.edges():
                if 'weight' in G[u][v]:
                    pesos_originais[(u, v)] = G[u][v]['weight']          

        # elif prop_id == 'salvar-grafo':
        #     salvar_grafo('grafo.txt')

        elif prop_id == 'adicionar-vertice':
            vertices_ordenados = sorted(list(G.nodes()))
            proximo_vertice = chr(ord(vertices_ordenados[-1])+1) if vertices_ordenados else 'A'
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

        elif prop_id == 'aplicar-peso':
            if selectedEdgeData:                
                edge_selecionada = selectedEdgeData[0]
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
    app.run_server(debug=True, port=2080)