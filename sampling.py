import networkx as nx
import walker

def DFSampling(G,start_node,len_paths):
    return list(nx.dfs_edges(G, source=start_node, depth_limit=len_paths))

def BFSampling(G,start_node,len_paths):
    return list(nx.bfs_edges(G, source=start_node, depth_limit=len_paths))

def random_sampling(G,start_node,len_paths):
    ordered_nodes = walker.random_walks(G, n_walks=1, walk_len=len_paths+1, 
                    start_nodes=[start_node],verbose=False)[0]
    edges_path = []
    for i in range(1,len(ordered_nodes)):
        edges_path.append((ordered_nodes[i-1],ordered_nodes[i]))
    return edges_path