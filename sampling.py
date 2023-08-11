import os, json
import walker
import networkx as nx

def DFSampling(G,start_node,len_paths):
    return list(dict.fromkeys(nx.dfs_edges(G, source=start_node, depth_limit=len_paths)))

def BFSampling(G,start_node,len_paths):
    return list(dict.fromkeys(nx.bfs_edges(G, source=start_node, depth_limit=len_paths)))

def random_sampling(G,start_node,len_paths):
    ordered_nodes = walker.random_walks(G, n_walks=1, walk_len=len_paths+1, 
                    start_nodes=[start_node],verbose=False)[0]
    edges_path = []
    for i in range(1,len(ordered_nodes)):
        edges_path.append((ordered_nodes[i-1],ordered_nodes[i]))
    return list(dict.fromkeys(edges_path))

def commit_paths_to_file(attack_paths,filename):
    existing_ids=[]
    count_duplicates=0
    all_paths=[]

    if os.path.exists(filename):
        with open(filename) as f: all_paths = json.load(f)
        existing_ids = [a_dict["id"] for a_dict in all_paths]
    
    for path in attack_paths:
        if path["id"] not in existing_ids: all_paths.append(path)
        else: count_duplicates+=1
    
    with open(filename, "w") as outfile:
        json_data = json.dumps(all_paths, default=lambda o: o.__dict__, indent=2)
        outfile.write(json_data)

    if len(attack_paths)<=0: return len(all_paths), 0
    return len(all_paths), count_duplicates/len(attack_paths)