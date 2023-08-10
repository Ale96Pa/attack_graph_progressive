import os, logging, json, random
import networkx as nx
import config

from reachability_graph import build_dataset
import sampling

def main_sampling(RG,num_samples):
    logging.basicConfig(filename='logging/sampling.log', level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s: %(message)s')
    sampled_paths_dfs=[]
    sampled_paths_bfs=[]
    sampled_paths_random=[]
    for i in range(0,num_samples):
        start_node = random.choice(rg_nodes)
        sampled_len = random.randint(2,len(rg_nodes))
        
        sampled_paths_dfs.append(sampling.DFSampling(RG,start_node,sampled_len))
        sampled_paths_bfs.append(sampling.BFSampling(RG,start_node,sampled_len))
        sampled_paths_random.append(sampling.random_sampling(RG,start_node,sampled_len))
    print(len(sampled_paths_dfs),len(sampled_paths_bfs),len(sampled_paths_random))
    

if __name__ == "__main__":
    """
    Build dataset reachability graphs according to network settings 
    hosts,vulnerabilities,topology,diversity,distribution (see config file)
    """
    build_dataset(clean_data=True)

    for subfolder in os.listdir(config.ROOT_FOLDER):
        network_file = config.ROOT_FOLDER+subfolder+"/"+subfolder+".json"
        with open(network_file) as net_f: file_content = json.load(net_f)
        edges_reachability = file_content["edges"]
        devices = file_content["devices"]
        vulnerabilities = file_content["vulnerabilities"]

        RG=nx.DiGraph()
        for net_edge in edges_reachability: 
            RG.add_edge(net_edge["host_link"][0],net_edge["host_link"][1])
        
        rg_nodes = list(RG.nodes())

        """
        Sampling the attack paths
        """
        main_sampling(RG,config.num_samples)