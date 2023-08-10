import uuid
import json

from base_features import base_features_distro

class Node:
    def __init__(self, privilege, host):
        self.privilege = privilege
        self.host = host

class Edge:
    def __init__(self,src,dst,vuln):
        self.src = src
        self.dst = dst
        self.vulnerability = vuln

class CompactedNode:
    def __init__(self, host):
        self.host = host

class CompactedEdge:
    def __init__(self,src,dst,vuln_list):
        self.src = src
        self.dst = dst
        self.vulnList = vuln_list

def base_features(edges):
    vulns = []
    for edge in edges:
        vulns.append(edge.vulnerability)
    return base_features_distro(vulns)

def monotonicity(src, trace):
    if src in trace: return True
    else: return False

def derivative_features(edges):
    impact_p = []
    likelihood_p = []
    trace=""
    for edge in edges:
        v = edge.vulnerability
        if not monotonicity(str(edge.src.host["hostname"])+"@"+edge.src.privilege,trace):
            trace+=str(edge.src.host["hostname"])+"@"+edge.src.privilege+"#"+\
                edge.vulnerability["id"]+"#"+\
                str(edge.dst.host["hostname"])+"@"+edge.dst.privilege+"##"
            
            if "cvssMetricV2" in v["metrics"]:
                metricV2 = v["metrics"]["cvssMetricV2"][0]
                impact = metricV2["impactScore"]
                likelihood = metricV2["exploitabilityScore"]
            elif "cvssMetricV30" in v["metrics"]:
                metricV3 = v["metrics"]["cvssMetricV30"][0]
                impact = metricV3["impactScore"]
                likelihood = metricV3["exploitabilityScore"]
            elif "cvssMetricV31" in v["metrics"]:
                metricV3 = v["metrics"]["cvssMetricV31"][0]
                impact = metricV3["impactScore"]
                likelihood = metricV3["exploitabilityScore"]
            else: #default values
                impact = 5 
                likelihood = 5

            impact_p.append(impact)
            likelihood_p.append(likelihood)
    
    length = trace.count("##")
    return { "trace": trace,
        "impact": sum(impact_p)/length,
        "likelihood": sum(likelihood_p)/length}

class AttackPath:
    def __init__(self,nodes,edges):
        self.id = str(uuid.uuid4())
        self.nodes = nodes
        self.edges = edges
        features = derivative_features(edges)
        self.length = features["trace"].count("##")
        self.trace = features["trace"]
        self.impact = features["impact"]
        self.likelihood = features["likelihood"]
        self.base_features = base_features(edges)

    def get_features(self):
        return {"id": self.id,
                "length": self.length,
                "trace": self.trace,
                "impact": self.impact,
                "likelihood": self.likelihood,
                "base_features": self.base_features}
    
    def exists(self, paths_file):
        with open(paths_file) as pf:
            paths = json.load(pf)
        for path in paths:
            if path["trace"] == self.trace: return True
        return False

class AttackGraph:
    def __init__(self,nodes,edges):
        self.nodes = nodes
        self.edges = edges

    def get_node_by_id(self,id):
        for n in self.nodes:
            if n.host["id"] == id:
                return n
    
    def get_node_by_hostname(self,hostname):
        for n in self.nodes:
            if n.host["hostname"] == hostname:
                return n
            
    def check_if_node_exist(self,node):
        for existing_node in self.nodes:
            if existing_node.host["id"] == node.host["id"] and \
            existing_node.privilege == node.privilege:
                return True
        return False
    
    def check_if_edge_exist(self,edge):
        for existing_edges in self.edges:
            if existing_edges.src.host["id"] == edge.src.host["id"] and \
            existing_edges.dst.host["id"] == edge.dst.host["id"] and \
            existing_edges.vulnerability["id"] == edge.vulnerability["id"]:
                return True
        return False