import os, logging, json, random, csv, traceback, time
import networkx as nx
from pebble import ProcessPool

from reachability_graph import build_dataset
import attack_paths as ap
import sampling
import steering
import config

def sample_paths_reachability(G,rg_nodes,num_samples,method):
    sampled_paths=[]
    for i in range(0,num_samples):
        start_node = random.choice(rg_nodes)
        sampled_len = random.randint(2,len(rg_nodes))
        if method=="dfs":
            sampled_paths.append(sampling.DFSampling(G,start_node,sampled_len))
        elif method=="bfs":
            sampled_paths.append(sampling.BFSampling(G,start_node,sampled_len))
        else:
            sampled_paths.append(sampling.random_sampling(G,start_node,sampled_len))
    # remove duplicate and empty sampled paths
    return [list(tupl) for tupl in {tuple(item) for item in sampled_paths} if list(tupl) != []]

def run_experiment(params):
    logging.basicConfig(filename='logging/experiments.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s')
    subfolder,sampling_method,query,steer_type = params

    network_file = config.ROOT_FOLDER+subfolder+"/"+subfolder+".json"
    filename_sample_query = config.ROOT_FOLDER+subfolder+"/"+sampling_method+config.get_query_samples_filename(steer_type)
    filename_sample_other = config.ROOT_FOLDER+subfolder+"/"+sampling_method+config.get_samples_filename(steer_type)
    cc = config.collision_control
    filename_steering_stats = config.ROOT_FOLDER+subfolder+"/"+sampling_method+"/"+config.stats_steering

    with open(network_file) as net_f: file_content = json.load(net_f)
    edges_reachability = file_content["edges"]
    devices = file_content["devices"]
    vulnerabilities = file_content["vulnerabilities"]

    if not os.path.exists(filename_steering_stats):
        config.write_header_steering_performance(filename_steering_stats)

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
    steering_vulnerabilities=[]
    count_iteration=0
    start_generation = time.perf_counter()
    try:
        while(collision_condition<=0.8):
            sampled_paths = sample_paths_reachability(RG,rg_nodes,config.num_samples,sampling_method)
            
            attack_paths_query = []
            attack_paths_other = []
            for path in sampled_paths:
                single_attack_path = ap.reachability_to_attack(path,devices,vulnerabilities,steering_vulnerabilities)
                if steering.isQuery(query,single_attack_path): attack_paths_query.append(single_attack_path)
                else: attack_paths_other.append(single_attack_path)
            
            num_query_paths, coll_query = sampling.commit_paths_to_file(attack_paths_query,filename_sample_query)
            collisions_query.append(coll_query)
            num_other_paths, coll_other = sampling.commit_paths_to_file(attack_paths_other,filename_sample_other)
            collisions_other.append(coll_other)
            collision_condition = sum(collisions_query[-cc:])/len(collisions_query[-cc:])
            
            if collision_condition >= 0.5: isSteering=True
            start_steering = time.perf_counter()
            if isSteering and steer_type=="steering":
                steering_vulnerabilities=steering.get_steering_vulns(filename_sample_query,filename_sample_other,vulnerabilities)

            end_time = time.perf_counter()
            count_iteration+=1
            with open(filename_steering_stats, "a", newline='') as f_steer:
                writer = csv.writer(f_steer)
                writer.writerow([count_iteration,config.num_samples,num_query_paths,
                                 num_other_paths,steer_type,isSteering,collision_condition,
                                 sum(collisions_other[-cc:])/len(collisions_other[-cc:]),
                                 end_time-start_generation,end_time-start_steering])
                
            if count_iteration%25 == 0: 
                logging.info("Iteration %d of experiment %s: retrieved %d paths",
                             count_iteration,subfolder,num_query_paths+num_other_paths)

    except Exception as e:
        traceback.print_exc()
        logging.error("[ERROR] %s", e)
    

if __name__ == "__main__":
    """
    Build dataset reachability graphs according to network settings 
    hosts,vulnerabilities,topology,diversity,distribution (see config file)
    """
    build_dataset(clean_data=True)
    QUERY = {
        # 'length': [2,4],
        'impact': [2,5],
        'likelihood': [0,4]
    }

    params=[]
    for network in os.listdir(config.ROOT_FOLDER):
        for method in config.sampling_algorithms:
            for steer_type in config.steering_types:
                params.append([network,method,QUERY,steer_type])

    with ProcessPool(max_workers=config.num_cores) as pool:
        process = pool.map(run_experiment, params)
        

