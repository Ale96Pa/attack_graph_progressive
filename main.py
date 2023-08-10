import os, logging, json, random
import networkx as nx
from pebble import ProcessPool

from reachability_graph import build_dataset
import attack_paths as ap
import sampling
import steering
import config

def sample_paths_reachability(RG,rg_nodes,num_samples,method):
    sampled_paths=[]
    for i in range(0,num_samples):
        start_node = random.choice(rg_nodes)
        sampled_len = random.randint(2,len(rg_nodes))
        if method=="dfs":
            sampled_paths.append(sampling.DFSampling(RG,start_node,sampled_len))
        elif method=="bfs":
            sampled_paths.append(sampling.BFSampling(RG,start_node,sampled_len))
        else:
            sampled_paths.append(sampling.random_sampling(RG,start_node,sampled_len))
    # remove duplicate and empty sampled paths
    return [list(tupl) for tupl in {tuple(item) for item in sampled_paths} if list(tupl) != []]

def run_experiment(params):
    subfolder,sampling_method,query = params

    network_file = config.ROOT_FOLDER+subfolder+"/"+subfolder+".json"
    filename_sample_query = config.ROOT_FOLDER+subfolder+"/"+sampling_method+config.get_query_samples_filename()
    filename_sample_other = config.ROOT_FOLDER+subfolder+"/"+sampling_method+config.get_samples_filename()
    cc = config.collision_control

    with open(network_file) as net_f: file_content = json.load(net_f)
    edges_reachability = file_content["edges"]
    devices = file_content["devices"]
    vulnerabilities = file_content["vulnerabilities"]


    RG=nx.DiGraph()
    for net_edge in edges_reachability: 
        RG.add_edge(net_edge["host_link"][0],net_edge["host_link"][1])
    rg_nodes = list(RG.nodes())

    """
    Sampling the reachability paths
    """
    collisions_query=[0]
    collisions_other=[0]
    collision_condition=0
    isSteering=False
    try:
        while(collision_condition<=0.5):
            sampled_paths = sample_paths_reachability(RG,rg_nodes,config.num_samples,sampling_method)
            
            attack_paths_query = []
            attack_paths_other = []
            for path in sampled_paths:
                single_attack_path = ap.reachability_to_attack(path,devices,vulnerabilities)
                if steering.isQuery(query,single_attack_path): attack_paths_query.append(single_attack_path)
                else: attack_paths_other.append(single_attack_path)
            
            collisions_query.append(sampling.commit_paths_to_file(attack_paths_query,filename_sample_query))
            collisions_other.append(sampling.commit_paths_to_file(attack_paths_other,filename_sample_other))
            collision_condition = sum(collisions_query[-cc:])/len(collisions_query[-cc:])
            
            if collision_condition >= 0.2: isSteering=True
            if isSteering:
                print("steering procedure")
                break
    except Exception as e:
        print(e)
    

if __name__ == "__main__":
    """
    Build dataset reachability graphs according to network settings 
    hosts,vulnerabilities,topology,diversity,distribution (see config file)
    """
    build_dataset(clean_data=True)
    QUERY = {
        # 'length': [2,4],
        'impact': [2,5],
        # 'likelihood': [0,4]
    }

    params=[]
    for network in os.listdir(config.ROOT_FOLDER):
        for method in config.sampling_algorithms:
            params.append([network,method,QUERY])

    with ProcessPool(max_workers=config.num_cores) as pool:
        process = pool.map(run_experiment, params, timeout=500)
        

