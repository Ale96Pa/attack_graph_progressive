import os, logging, json, random, csv, traceback, time
import networkx as nx
import pandas as pd
from pebble import ProcessPool
import matplotlib.pyplot as plt

from reachability_graph import build_dataset_performance
import attack_paths as ap
import sampling
import steering
import config
from main_generation import generate_all_paths

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
    logging.basicConfig(filename='logging/performance.log', level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s: %(message)s')
    subfolder,sampling_method,query,steer_type,num_exp = params

    network_file = config.ROOT_FOLDER_PERFORMANCE+subfolder+"/"+config.gt_folder+subfolder+".json"
    filename_sample_query = config.ROOT_FOLDER_PERFORMANCE+subfolder+"/"+sampling_method+\
                "/exp"+str(num_exp)+config.get_query_samples_filename(steer_type)
    filename_sample_other = config.ROOT_FOLDER_PERFORMANCE+subfolder+"/"+sampling_method+\
                "/exp"+str(num_exp)+config.get_samples_filename(steer_type)

    cc = config.collision_control

    with open(network_file) as net_f: file_content = json.load(net_f)
    edges_reachability = file_content["edges"]
    devices = file_content["devices"]
    vulnerabilities = file_content["vulnerabilities"]

    RG=nx.DiGraph()
    for net_edge in edges_reachability: 
        RG.add_edge(net_edge["host_link"][0],net_edge["host_link"][1])
    rg_nodes = list(RG.nodes())

    logging.info("[START] folder %s, experiment %d, sampling: %s, steering: %s", 
                 subfolder,num_exp,sampling_method,steer_type)

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
    if steer_type == "none":
        num_paths = generate_all_paths(subfolder)
    else:
        try:
            num_paths=0
            while(collision_condition_query<=0.8):
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
                
                if collision_condition_query >= config.start_steering_collision: isSteering=True
                start_steering = time.perf_counter()
                if isSteering and steer_type=="steering" and not stopSteering:
                    steering_vulnerabilities=steering.get_steering_vulns(filename_sample_query,filename_sample_other,vulnerabilities)
                    stopSteering=True

                if count_iteration%20 == 0: 
                    logging.info("%s %d iteration %d %s: num paths: %d collision %f",
                                subfolder,num_exp, count_iteration,steer_type,num_query_paths,collision_condition_query)
                    
                if count_iteration>900 and collision_condition_query<=0:
                    logging.error("[INTERRUPT] %s %s, collision: %f",subfolder,steer_type,collision_condition_query)
                    return
                
                num_paths=num_query_paths+num_other_paths
        except Exception as e:
            traceback.print_exc()
            logging.error("[ERROR] %s on experiment %s, sampling: %s, steering: %s", e,subfolder,sampling_method,steer_type)
    end_generation = time.perf_counter()
    with open(config.plot_folder+"performance_stats.csv", "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([steer_type,subfolder.split("_")[0],config.num_samples,
                         count_iteration,num_paths,end_generation-start_generation,"range_query"])

    logging.info("[END] folder %s, experiment %d, sampling: %s, steering: %s", subfolder,num_exp,sampling_method,steer_type)

def plot_performance(file_performance):
    plt.rcParams.update({'font.size': 24})
    fig, axs = plt.subplots()
    fig.set_figwidth(15)
    fig.set_figheight(10)

    df = pd.read_csv(file_performance)
    mean_df = df.groupby(['algorithm','num_host']).mean().reset_index()

    grouped_by_algo = mean_df.groupby(["algorithm"])
    labels_legend=[]
    for algo, item in grouped_by_algo:
        algo_df = grouped_by_algo.get_group(algo)
        x_vals = list(algo_df["num_host"])
        y_vals = list(algo_df["time"])
        labels_legend.append(algo)
        
        axs.plot(x_vals,y_vals,linewidth = '3')
    
    axs.set_xlabel("num. hosts")
    axs.set_ylabel("time")
    axs.legend(labels=labels_legend)
    axs.set_title("Paths computation time")
    
    plt.savefig(config.plot_folder+"performance.png", bbox_inches='tight')

if __name__ == "__main__":
    only_plot = False
    
    if only_plot:
        plot_performance(config.plot_folder+"performance_stats.csv")
    else:
        """
        Build dataset reachability graphs according to network settings 
        hosts,vulnerabilities,topology,diversity,distribution (see config file)
        """
        build_dataset_performance(clean_data=True)
        
        min_len = random.randint(1,8)
        max_len = random.randint(min_len+1,10)
        min_imp = random.randint(1,8)
        max_imp = random.randint(min_imp+1,10)
        min_lik = random.randint(1,8)
        max_lik = random.randint(min_lik+1,10)
        # QUERY = {
        #     # 'length': [min_len,max_len],
        #     'impact': [min_imp,max_imp],
        #     'likelihood': [min_lik,max_lik]
        # }
        QUERY = {
            # 'length': [2,4],
            'impact': [1,5],
            'likelihood': [0,5]
        }

        clean_performance=True
        if not os.path.exists(config.plot_folder+"performance_stats.csv") or clean_performance:
            with open(config.plot_folder+"performance_stats.csv", "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["algorithm","num_host","num_samples","iterations","num_paths","time","range_query"])

        params=[]
        for network in os.listdir(config.ROOT_FOLDER_PERFORMANCE):
            for method in config.sampling_algorithms:
                for steer_type in config.steering_types:
                    for experiment in range(1,config.num_experiments_per+1):
                        params.append([network,method,QUERY,steer_type,experiment])
        
        with ProcessPool(max_workers=config.num_cores) as pool:
            process = pool.map(run_experiment, params)
        
        plot_performance(config.plot_folder+"performance_stats.csv")

