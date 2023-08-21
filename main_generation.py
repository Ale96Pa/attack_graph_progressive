import json, itertools, os, logging
import networkx as nx
from pebble import ProcessPool

from models import AttackGraph as AG
from attack_paths import retrieve_privileges, get_vulns_by_hostname
import config

"""
This function generates the reachability graph from the network used as the base
to generate samples
"""
def build_reachability_graph(edges_reachability, devices):   
    G = nx.DiGraph()
    nodesId = []
    for edge_r in edges_reachability:
        src_id = edge_r["host_link"][0]
        dst_id = edge_r["host_link"][1]
        cve_list_dst = []

        for dev in devices:
            if dev["hostname"] == src_id:
                src_node = dev
            if dev["hostname"] == dst_id:
                dst_node = dev
                cve_list_dst = get_vulns_by_hostname(dst_id,devices)
        
        if src_node["hostname"] not in nodesId:
            nodesId.append(src_node["hostname"])
            G.add_node(edge_r["host_link"][0])
        if dst_node["hostname"] not in nodesId:
            nodesId.append(dst_node["hostname"])
            G.add_node(edge_r["host_link"][1])
        G.add_edge(edge_r["host_link"][0],edge_r["host_link"][1],vulns=cve_list_dst)
    return G

"""
This function generate all the attack paths (ground truth) for a given network
"""
def generate_all_paths(subfolder):
    logging.basicConfig(filename='logging/generation.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s: %(message)s')

    network_file = config.ROOT_FOLDER+subfolder+"/"+subfolder+".json"
    gt_paths_file = config.ROOT_FOLDER+subfolder+"/"+config.gt_paths
    if os.path.exists(gt_paths_file):
        logging.warning("Ground Truth %s already GENERATED.", gt_paths_file)
        return
    
    logging.info("[START] generation of ground truth: %s", gt_paths_file)

    with open(network_file) as net_f:
            file_content = json.load(net_f)
    edges_reachability = file_content["edges"]
    devices = file_content["devices"]
    vulnerabilities = file_content["vulnerabilities"]
    
    G = build_reachability_graph(edges_reachability, devices)
    vulns = nx.get_edge_attributes(G,'vulns')

    permutations = list(itertools.permutations(G.nodes(), 2))
    reach_paths = []
    for couple in permutations:
        src = couple[0]
        dst = couple[1]
        curr_paths = nx.all_simple_edge_paths(G, source=src, target=dst)
        for p in curr_paths:
            reach_paths.append(p)
    
    all_paths=[]
    all_traces=[]
    for path in reach_paths:
        one_hop_paths = []
        for edge in path:
            for v in vulns[edge]:
                vuln,req,gain = retrieve_privileges(v,vulnerabilities)            
                for dev in devices:
                    if dev["hostname"] == edge[1]: dst_dev = dev
                    elif dev["hostname"] == edge[0]: src_dev = dev
                src_node = AG.Node(req,src_dev)
                dst_node = AG.Node(gain,dst_dev)
                e = AG.Edge(src_node,dst_node,vuln)
                one_hop_paths.append(e)

        list_combinations = []
        for n in range(len(one_hop_paths) + 1):
            list_combinations += list(itertools.combinations(one_hop_paths, n))

        for comb in list_combinations:
            if len(comb) > 0:
                AttackPath = AG.AttackGraph([],[])
                prev_edge = comb[0]
                AttackPath.edges.append(prev_edge)
                AttackPath.nodes.append(prev_edge.src)
                AttackPath.nodes.append(prev_edge.dst)
                for i in range(1,len(comb)):
                    next_edge = comb[i]
                    if prev_edge.dst.host['hostname'] == next_edge.src.host["hostname"]:
                        if not AttackPath.check_if_edge_exist(next_edge):
                            AttackPath.edges.append(next_edge)
                        if not AttackPath.check_if_node_exist(next_edge.src):
                            AttackPath.nodes.append(next_edge.src)
                        if not AttackPath.check_if_node_exist(next_edge.dst):
                            AttackPath.nodes.append(next_edge.dst)
                    else:
                        AttackPath = AG.AttackGraph([],[])
                        break
                    prev_edge = next_edge
                if len(AttackPath.edges) > 0:
                    AP = AG.AttackPath(AttackPath.nodes,AttackPath.edges)
                    if AP.trace not in all_traces:
                        all_paths.append(AP.get_features())
                        all_traces.append(AP.trace)
        
    with open(gt_paths_file, "w") as outfile:
        json_data = json.dumps(all_paths, default=lambda o: o.__dict__, indent=2)
        outfile.write(json_data)
    
    logging.info("[CONCLUSION] generation of %s with %d paths.", gt_paths_file, len(all_paths))
    return len(all_paths)

if __name__ == "__main__":
    """
    Build ground truths (all paths generation)
    """
    parameters_gt = []
    for subfolder in os.listdir(config.ROOT_FOLDER):
        if "random" in subfolder: parameters_gt.append(subfolder)
        else: 
            if "0.5_1" in subfolder: parameters_gt.append(subfolder)
    with ProcessPool(max_workers=config.num_cores) as pool:
        process = pool.map(generate_all_paths, parameters_gt)