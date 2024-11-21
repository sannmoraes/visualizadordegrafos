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
                html.Div(id='mensagem-aviso', style={'color': 'red', 'fontWeight': 'bold'}),
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
                dcc.Upload(
                     id='upload-data',
                    children=html.Button('Upload Arquivo'),
                    multiple=False
             ),
            html.Div(id='output-upload')
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
                html.Button('Emparelhamento Máximo', id='emparelhamento-maximo', n_clicks=0),
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
            if linha.strip() and not linha.startswith('#'):
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

# Algoritmo 8.1: Emparelhamento cardinalidade máxima – Grafos bipartidos - Jayme Luiz Szwarcfier
def calcular_emparelhamento_maximo(G):
    
    M = {}
    
    def construir_grafo_residual(M):
        D = nx.Graph()
        for u, v in G.edges():
            
            if u not in M or v != M[u]:  
                D.add_edge(u, v)
        return D
    
    
    def caminho_aumentante(u, D, M, visitados):
        
        if u in visitados or u not in D.nodes:
            return False
        visitados.add(u)
        
        
        for v in D.neighbors(u):
            if v not in M or caminho_aumentante(M[v], D, M, visitados):
                M[u] = v 
                M[v] = u  
                return True
        return False    
    
    D = construir_grafo_residual(M)
    
    while True:
        
        visitados = set()
        caminho_encontrado = False        
        
        for u in G.nodes():
            if u not in M and len(list(G.neighbors(u))) > 1:
                if caminho_aumentante(u, D, M, visitados):
                    caminho_encontrado = True        
        
        if not caminho_encontrado:
            break        
        
        D = construir_grafo_residual(M)
    
    return M




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
        
    return visited, edges_visited

@app.callback(
    [Output('grafo', 'elements'),
    Output('grafo', 'stylesheet'),
    Output('mensagem-aviso', 'children'),
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
     Input('emparelhamento-maximo', 'n_clicks'),
     Input('aplicar-peso', 'n_clicks')],
     [State('peso-aresta-input', 'value')]    
)



def atualizar_grafo(n_clicks_carregar_grafo, salvar_grafo_clicks, adicionar_vertice, remover_vertice, adicionar_aresta, remover_aresta, selectedNodeData, tipo_grafo, peso_aresta, selectedEdgeData,  n_clicks_bfs, n_clicks_dfs, n_clicks_aplicar_peso, peso_entrada, n_clicks_emparelhamento_maximo):
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

    mensagem_aviso = ""

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



        if prop_id == 'emparelhamento-maximo' and n_clicks_emparelhamento_maximo > 0:

           if isinstance(G, nx.DiGraph):
                 mensagem_aviso = "Este Emparelhamento não é aplicável a grafos orientados."
           else:

            emparelhamento_maximo = calcular_emparelhamento_maximo(G)    

            for u, v in emparelhamento_maximo.items():
                 G.add_edge(u, v, weight=1)


                 stylesheet.append({
                    'selector': f'edge[id="{u}-{v}"]',
                    'style': {
                        'line-color': 'red',
                        'width': 8,
                        'line-style': 'solid'
                     }
                 })



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

        informacoes_grafo = calcular_informacoes_grafo()



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
    
    


    return elementos_grafo, stylesheet, mensagem_aviso, informacoes_grafo 
    
# Executar a aplicação
if __name__ == '__main__':
    app.run_server(debug=True, port=6999)