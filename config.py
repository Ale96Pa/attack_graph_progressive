import json, csv, itertools

### SAMPLING parameters
sampling_algorithms = ["random"]#,"random", "bfs","dfs"]
num_samples = 100
# steering_types = ["none","steering"]
steering_types = ["steering"]

### BENCHMARK parameters
num_cores = 3
num_experiments = 1
clean_dataset=True
collision_end_value_query = 0.95
collision_end_value_other = 0.85
collision_control = 50*round(1500/num_samples) #number of tuples to consider for average collisions


### STEERING parameters
precision_control=1.3
smoothing_window = 50*round(1500/num_samples)#20
decision_window = 50*round(1500/num_samples)#15
decision_num_restart = 0.25
max_iteration_same_query = 1000

### QUERIES parameters
sok_queries=[
    {'id': "r1",
    'impact': [3,5],
    'likelihood': [5,8]},
    {'id': "r2",
    'impact': [3,5],
    'likelihood': [5,8]},
    {'id': "r3",
    'impact': [3,5],
    'likelihood': [5,8]},
    {'id': "r4",
    'impact': [3,5],
    'likelihood': [5,8]},
    {'id': "r5",
    'impact': [3,5],
    'likelihood': [5,8]},
]
QUERY={
    'id': "0",
    'impact': [3,5],
    'likelihood': [5,8]
}
size_ranges=[[3,4],[3,6],[3,8]]
def all_combination_queries():
    queries=[]
    for L in range(len(size_ranges) + 1):
        for subset in itertools.product(size_ranges, repeat=L):
            if len(subset) == 1:
                queries.append({
                'id': "impact:"+str(subset[0]),
                "impact": subset[0]
                })
                queries.append({
                'id': "score:"+str(subset[0]),
                "score": subset[0]
                })
                queries.append({
                'id': "likelihood:"+str(subset[0]),
                "likelihood": subset[0]
                })
                # print("impact:"+str(subset[0]))
            elif len(subset) == 2:
                queries.append({
                'id': "impact:"+str(subset[0])+"#score:"+str(subset[1]),
                'impact': subset[0],
                'score': subset[1]
                })
                # print("impact:"+str(subset[0])+"#score:"+str(subset[1]))
            elif len(subset) == 3:
                queries.append({
                'id': "impact:"+str(subset[0])+"#score:"+str(subset[1])+"#likelihood:"+str(subset[2]),
                'impact': subset[0],
                'score': subset[1],
                'likelihood': subset[2]
                })
                # print("impact:"+str(subset[0])+"#score:"+str(subset[1])+"#likelihood:"+str(subset[2]))
    return queries

### NETWORK SETTING parameters
nhosts = [10]
nvulns = [10]
topologies = ["powerlaw"]#,"tree"] #mesh,random,star,ring,tree,powerlaw,lan0,lan25,lan50,
distro = ["uniform"] #uniform,bernoulli,poisson,binomial
diversity = [1] #0,0.25,0.5,0.75,1
start_steering_collision = 0.3

nhosts_per = [5,10,15,20,25,30,35]
nvulns_per = [3]
topologies_per = ["powerlaw"] #mesh,random,star,ring,tree,powerlaw,lan0,lan25,lan50,
distro_per = ["uniform"]
diversity_per = [0]
num_experiments_per = 10

### NETWORK FILES parameters
ROOT_FOLDER = "dataset/"
stat_folder = "stats/"
plot_folder = "plot/"
samples_folder = "/samples/"
gt_folder = "ground_truth/"
gt_paths = gt_folder+"GT_paths.json"
gt_base = gt_folder+"GT_base.json"

stats_sampling = stat_folder+"sampling.json"
stats_steering = stat_folder+"steering.csv"

ROOT_FOLDER_PERFORMANCE = "dataset_p/"

### SAMPLING settings
# def get_paths_file(ind, isSteering): 
#     if isSteering=="naive": return "/samples/npaths_"+str(ind)+".json"
#     elif isSteering=="embedded": return "/samples/epaths_"+str(ind)+".json"
#     else: return "/samples/paths_"+str(ind)+".json"
# def get_query_paths_file(ind, isSteering): 
#     if isSteering=="naive": return "/samples/nQpaths_"+str(ind)+".json"
#     elif isSteering=="embedded": return "/samples/eQpaths_"+str(ind)+".json"
#     else: return "/samples/Qpaths_"+str(ind)+".json"
def get_query_samples_filename(steerType):
    return samples_folder+steerType+"Query_paths.json"
def get_samples_filename(steerType):
    return samples_folder+steerType+"Paths.json"

"""
Define structure of the steering performance file
"""
def write_header_steering_performance(file_steering):
    with open(file_steering, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["iteration","num_samples","num_query_paths","num_other_paths",
                         "steering_type","isSteering","collision_rate_query",
                         "collision_rate_other","time_generation","time_steering","query"])

### Inventories
cpe_file = "inventory/services.json"
cve_file1 = "inventory/vulnerabilities1.json"
cve_file2 = "inventory/vulnerabilities2.json"
cve_file3 = "inventory/vulnerabilities3.json"

def get_pool_vulnerabilities(tot_vuln):
    if tot_vuln <= 14500:
        with open(cve_file1) as f1:
            return json.load(f1)["vulnerabilities"]
    elif 14500 < tot_vuln <= 29000:
        with open(cve_file1) as f1, open(cve_file2) as f2:
            vulns1 = json.load(f1)["vulnerabilities"]
            vulns2 = json.load(f2)["vulnerabilities"]
            return vulns1+vulns2
    else:
        with open(cve_file1) as f1, open(cve_file2) as f2, open(cve_file3) as f3:
            vulns1 = json.load(f1)["vulnerabilities"]
            vulns2 = json.load(f2)["vulnerabilities"]
            vulns3 = json.load(f3)["vulnerabilities"]
            return vulns1+vulns2+vulns3