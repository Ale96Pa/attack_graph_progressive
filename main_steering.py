import os, logging, json, random, csv, traceback, time, statistics
import networkx as nx
from pebble import ProcessPool

from reachability_graph import build_dataset
import attack_paths as ap
import features_management as fm
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
    logging.basicConfig(filename='logging/experiments.log', level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s: %(message)s')
    subfolder,sampling_method,query,steer_type,num_exp = params

    network_file = config.ROOT_FOLDER+subfolder+"/"+config.gt_folder+subfolder+".json"
    filename_sample_query = config.ROOT_FOLDER+subfolder+"/"+sampling_method+\
                "/exp"+str(num_exp)+config.get_query_samples_filename(steer_type)
    filename_sample_other = config.ROOT_FOLDER+subfolder+"/"+sampling_method+\
                "/exp"+str(num_exp)+config.get_samples_filename(steer_type)
    filename_sampling_stats = config.ROOT_FOLDER+subfolder+"/"+sampling_method+\
                "/exp"+str(num_exp)+"/"+config.stats_sampling
    filename_steering_stats = config.ROOT_FOLDER+subfolder+"/"+sampling_method+\
                "/exp"+str(num_exp)+"/"+config.stats_steering

    cc = config.collision_control

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

    logging.info("[START] folder %s, experiment %d, sampling: %s, steering: %s", 
                 subfolder,num_exp,sampling_method,steer_type)

    """
    Ground truth of base features distribution
    """
    base_features_gt_filename = config.ROOT_FOLDER+subfolder+"/"+config.gt_base
    GT_base_stats = fm.base_features_distro(vulnerabilities)
    if not os.path.exists(base_features_gt_filename):
        with open(base_features_gt_filename, "w") as outfile:
            json_base_gt = json.dumps(GT_base_stats, default=lambda o: o.__dict__, indent=2)
            outfile.write(json_base_gt)

    """
    Sampling the reachability paths
    """
    collisions_query=[0]
    collisions_other=[0]
    collision_condition_other=0
    collision_condition_query=0
    isSteering=False
    stopSteering=False
    steering_vulnerabilities=[]
    count_iteration=0
    sampled_vulnerabilities=[]
    start_generation = time.perf_counter()
    track_precisions=[]
    try:
        while(collision_condition_query<=0.9 or collision_condition_other<=0.9):
        # while((collision_condition_query<=0.995 or steer_type=="steering") and (collision_condition_query<=0.98 or collision_condition_other<=0.98 or steer_type=="none")):
        # while((collision_condition_other+collision_condition_query)/2<=0.8):
            count_iteration+=1
            sampled_paths = sample_paths_reachability(RG,rg_nodes,config.num_samples,sampling_method)
            
            attack_paths_query = []
            attack_paths_other = []
            for path in sampled_paths:
                single_attack_path, path_vulns = ap.reachability_to_attack(path,devices,vulnerabilities,steering_vulnerabilities)
                if steering.isQuery(query,single_attack_path): attack_paths_query.append(single_attack_path)
                else: attack_paths_other.append(single_attack_path)
                
                for new_vuln in path_vulns:
                    existing_ids = [val['id'] for val in sampled_vulnerabilities]
                    if new_vuln["id"] not in existing_ids:
                        sampled_vulnerabilities.append(new_vuln)
            
            num_query_paths, coll_query = sampling.commit_paths_to_file(attack_paths_query,filename_sample_query,count_iteration)
            collisions_query.append(coll_query)
            num_other_paths, coll_other = sampling.commit_paths_to_file(attack_paths_other,filename_sample_other,count_iteration)
            collisions_other.append(coll_other)

            collision_condition_query = sum(collisions_query[-cc:])/cc
            collision_condition_other = sum(collisions_other[-cc:])/cc
            
            current_precision = len(attack_paths_query)/config.num_samples
            track_precisions.append(current_precision)

            if collision_condition_query >= config.start_steering_collision and steer_type=="steering": isSteering=True
            start_steering = time.perf_counter()
            if isSteering and steer_type=="steering" and not stopSteering:
                steering_vulnerabilities=steering.get_steering_vulns(filename_sample_query,filename_sample_other,vulnerabilities)
                stopSteering=True

                median_precision = statistics.median(track_precisions[-config.precision_window:]) #sum(track_precisions[-config.precision_window:])/config.precision_window
                if median_precision >= current_precision:
                    stopSteering=False
                    print("restart steering at iteration: ", count_iteration)
                    logging.info("[RESTART STEERING] of setting %s experiment %d steering %s at iteration %d",
                            subfolder,num_exp,steer_type,count_iteration)
                    print(current_precision, track_precisions[-config.precision_window:])
            
            if steer_type=="none":
                distro_sampled_vuln = fm.base_features_distro(sampled_vulnerabilities)
                stats_compare_vuln = fm.compare_stats(GT_base_stats, distro_sampled_vuln)

                stats_compare_vuln["type"] = "stats"
                stats_compare_vuln["collision_rate"] = (collision_condition_other+collision_condition_query)/2
                stats_compare_vuln["iteration"] = count_iteration
                stats_compare_vuln["sample_size"] = config.num_samples

                distro_sampled_vuln["type"] = "sample"
                distro_sampled_vuln["collision_rate"] = (collision_condition_other+collision_condition_query)/2
                distro_sampled_vuln["iteration"] = count_iteration
                distro_sampled_vuln["sample_size"] = config.num_samples

                sampling.write_base_sample_iteration(filename_sampling_stats,[distro_sampled_vuln,stats_compare_vuln])

            end_time = time.perf_counter()
            with open(filename_steering_stats, "a", newline='') as f_steer:
                writer = csv.writer(f_steer)
                writer.writerow([count_iteration,config.num_samples,num_query_paths,
                                 num_other_paths,steer_type,isSteering,collision_condition_query,
                                 collision_condition_other,
                                 end_time-start_generation,end_time-start_steering])
                
            if count_iteration%25 == 0: 
                logging.info("Iteration %d of setting %s experiment %d steering %s: collision query %f, collision other %f",
                             count_iteration,subfolder,num_exp,steer_type,collision_condition_query,collision_condition_other)
        logging.info("[END] folder %s, experiment %d, sampling: %s, steering: %s, collisions (query,other): %f - %f", subfolder,num_exp,sampling_method,steer_type,collision_condition_query,collision_condition_other)
    except Exception as e:
        traceback.print_exc()
        logging.error("[ERROR] %s on experiment %s, sampling: %s, steering: %s", e,subfolder,sampling_method,steer_type)
    

if __name__ == "__main__":
    """
    Build dataset reachability graphs according to network settings 
    hosts,vulnerabilities,topology,diversity,distribution (see config file)
    """
    build_dataset(clean_data=True)
    QUERY = {
        # 'length': [2,4],
        'impact': [1,5],
        'likelihood': [0,4]
    }

    params=[]
    for network in os.listdir(config.ROOT_FOLDER):
        for method in config.sampling_algorithms:
            for steer_type in config.steering_types:
                for experiment in range(1,config.num_experiments+1):
                    params.append([network,method,QUERY,steer_type,experiment])

    with ProcessPool(max_workers=config.num_cores) as pool:
        process = pool.map(run_experiment, params)
        

