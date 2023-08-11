import json, csv

### BENCHMARK parameters
num_cores = 6

### SAMPLING parameters
sampling_algorithms = ["random"]#,"random", "bfs","dfs"]
num_samples = 50
collision_control = 5 #number of tuples to consider for average collisions
steering_types = ["none","steer"]


### NETWORK SETTING parameters
nhosts = [10]
nvulns = [10]
topologies = ["tree"] #mesh,random,star,ring,tree,powerlaw,lan0,lan25,lan50,
distro = ["uniform"] #uniform,bernoulli,poisson,binomial
diversity = [0.5] #0,0.25,0.5,0.75,1
num_experiments = 3

### NETWORK FILES parameters
ROOT_FOLDER = "dataset/"
stat_folder = "stats/"
plot_folder = "plot/"
samples_folder = "/samples/"
gt_folder = "ground_truth/"
gt_paths = gt_folder+"GT_paths.json"
gt_base = gt_folder+"base_gt.csv"
stats_steering = stat_folder+"steering.csv"

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
                         "collision_rate_other","time_generation","time_steering"])

# ### base features settings
# def get_base_stats_file(ind): return "/stats/base_stats_"+str(ind)+".csv"
# def get_base_sample_file(ind): return "/stats/base_samples_"+str(ind)+".csv"

# ### derivative features settings
# def get_derivative_sample(ind): return "/stats/derivative_samples_"+str(ind)+".csv"
# def get_derivative_gt(ind): return "/stats/derivative_gt_"+str(ind)+".csv"

# ## steering performance setting
# def get_steering_stats(ind): return "/stats/steering_performance_"+str(ind)+".csv" 

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
