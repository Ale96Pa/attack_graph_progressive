import pandas as pd
import json
from sklearn import tree
from sklearn.tree import DecisionTreeClassifier
import matplotlib.pyplot as plt
import numpy as np

def isQuery(query,attack_path):
    for k in query.keys():
        min_v, max_v = query[k]
        if attack_path[k] < min_v or attack_path[k] > max_v: return False
    return True

def extract_cve_trace(traces):
    vulns_by_trace=[]
    for trace in traces:
        vulns=[]
        for step in trace.split("##"):
            for edge_str in step.split("#"):
                if "CVE" in edge_str: vulns.append(edge_str)
        vulns_by_trace.append(vulns)
    return vulns_by_trace

def convert_categorical_to_num(str_val):
    if str_val == "NONE": return 0
    elif str_val == "NETWORK" or str_val=="LOW" or str_val=="SINGLE" or str_val=="PARTIAL": return 1
    elif str_val == "ADJACENT_NETWORK" or str_val=="MEDIUM" or str_val=="MULTIPLE" or str_val=="COMPLETE": return 2
    elif str_val == "LOCAL" or str_val=="HIGH": return 3
    elif str_val == "PHYSICAL" or str_val=="CRITICAL": return 4
    else: return 0

def base_features_vulnID(vuln_id,vulnerabilities):
    for vuln in vulnerabilities:
        if vuln["id"] == vuln_id:
            dicFeatures={}
            if "cvssMetricV2" in vuln["metrics"]:
                metricV2 = vuln["metrics"]["cvssMetricV2"][0]
                metricCvssV2 = metricV2["cvssData"]

                dicFeatures["baseScore"] = metricCvssV2["baseScore"]
                dicFeatures["impactScore"] = metricV2["impactScore"]
                dicFeatures["exploitabilityScore"] = metricV2["exploitabilityScore"]
                dicFeatures["accessVector"]=convert_categorical_to_num(metricCvssV2["accessVector"])
                dicFeatures["accessComplexity"]=convert_categorical_to_num(metricCvssV2["accessComplexity"])
                dicFeatures["authentication"]=convert_categorical_to_num(metricCvssV2["authentication"])
                dicFeatures["confidentialityImpact"]=convert_categorical_to_num(metricCvssV2["confidentialityImpact"])
                dicFeatures["integrityImpact"]=convert_categorical_to_num(metricCvssV2["integrityImpact"])
                dicFeatures["availabilityImpact"]=convert_categorical_to_num(metricCvssV2["availabilityImpact"])
                dicFeatures["baseSeverity"]=convert_categorical_to_num(metricV2["baseSeverity"])

                return dicFeatures
            
            if "cvssMetricV30" in vuln["metrics"] or "cvssMetricV31" in vuln["metrics"]:
                if "cvssMetricV30" in vuln["metrics"]: metricV3 = vuln["metrics"]["cvssMetricV30"][0]
                else: metricV3 = vuln["metrics"]["cvssMetricV31"][0]
                metricCvssV3 = metricV3["cvssData"]

                dicFeatures["baseScore"]=metricCvssV3["baseScore"]
                dicFeatures["impactScore"]=metricV3["impactScore"]
                dicFeatures["exploitabilityScore"]=metricV3["exploitabilityScore"]
                # dicFeatures["attackVector"]=convert_categorical_to_num(metricCvssV3["attackVector"])
                dicFeatures["accessVector"]=convert_categorical_to_num(metricCvssV3["attackVector"])
                # dicFeatures["attackComplexity"]=convert_categorical_to_num(metricCvssV3["attackComplexity"])
                dicFeatures["accessComplexity"]=convert_categorical_to_num(metricCvssV3["attackComplexity"])
                # dicFeatures["privilegesRequired"]=convert_categorical_to_num(metricCvssV3["privilegesRequired"])
                dicFeatures["authentication"]=convert_categorical_to_num(metricCvssV3["privilegesRequired"])
                dicFeatures["confidentialityImpact"]=convert_categorical_to_num(metricCvssV3["confidentialityImpact"])
                dicFeatures["integrityImpact"]=convert_categorical_to_num(metricCvssV3["integrityImpact"])
                dicFeatures["availabilityImpact"]=convert_categorical_to_num(metricCvssV3["availabilityImpact"])
                dicFeatures["baseSeverity"]=convert_categorical_to_num(metricCvssV3["baseSeverity"])
                
                return dicFeatures

            return dicFeatures

def embed_function(cves_list,isQuery,vulnerabilities):
    subtraining=[]
    for cvetrace in cves_list:
        embedding = []
        for cve in cvetrace:
            embedding.append(base_features_vulnID(cve,vulnerabilities))
        cve_data_dict = dict(pd.DataFrame(embedding).median(axis=0)) # embedding based on median
        cve_data_dict["query"] = isQuery
        subtraining.append(cve_data_dict)
    return subtraining

def build_training_set(qfile,ofile,vulnerabilities):
    df_query = pd.read_json(qfile)
    df_other = pd.read_json(ofile)
    num_data = min(len(df_query),len(df_other))
    df_query=df_query[0:num_data]
    df_other=df_other[0:num_data]

    cves_query = extract_cve_trace(list(df_query["trace"]))
    cves_other = extract_cve_trace(list(df_other["trace"]))

    training_set_query=embed_function(cves_query,True,vulnerabilities)
    training_set_other=embed_function(cves_other,False,vulnerabilities)
    df_training = pd.DataFrame(training_set_query+training_set_other)
    
    return df_training

def _find_path(tree, node_numb, path, x):
    path.append(node_numb)

    children_left = tree.children_left
    children_right = tree.children_right

    if node_numb == x:
        return True

    left = False
    right = False

    if children_left[node_numb] != -1:
        left = _find_path(tree, children_left[node_numb], path, x)
    if children_right[node_numb] != -1:
        right = _find_path(tree, children_right[node_numb], path, x)
    if left or right:
        return True

    path.remove(node_numb)
    return False

def _extract_paths(X, model):
    tree = model.tree_
    paths = {}
    leave_id = model.apply(X)
    for leaf in np.unique(leave_id):
        if model.classes_[np.argmax(model.tree_.value[leaf])] == 1:
            path_leaf = []
            _find_path(tree, 0, path_leaf, leaf)
            paths[leaf] = list(np.unique(np.sort(path_leaf)))

    return paths

def _get_rule(tree, path, column_names, feature, threshold):
    children_left = tree.children_left

    mask = ""
    for index, node in enumerate(path):
        # We check if we are not in the leaf
        if index != len(path) - 1:
            # Do we go under or over the threshold ?
            if children_left[node] == path[index + 1]:
                mask += "(df['{}']<= {}) \t ".format(
                    column_names[feature[node]], threshold[node]
                )
            else:
                mask += "(df['{}']> {}) \t ".format(
                    column_names[feature[node]], threshold[node]
                )
    # We insert the & at the right places
    mask = mask.replace("\t", "&", mask.count("\t") - 1)
    mask = mask.replace("\t", "")
    return mask

def _extract_conjunction(rule, conjunction):
    condition = ""
    listconditions = rule.strip().split("&")
    i = 0
    for s in listconditions:
        listLabel = s.strip().split("'")
        condition = (
            condition + listLabel[1] + " " + listLabel[2][1 : len(listLabel[2]) - 1]
        )

        if i != len(listconditions) - 1:
            condition = condition + " " + conjunction + " "
        i += 1

    return condition

def _generate_expression(sample, tree, paths, feature, threshold):
    rules = {}
    expression = ""
    conjunctor = "and"
    disjunctor = "or"

    j = 0
    for key in paths:
        rules[key] = _get_rule(tree, paths[key], sample.columns, feature, threshold)
        new_conjunction = _extract_conjunction(rules[key], conjunctor)

        if j == 0:
            expression = "(" + new_conjunction + ")"
        else:
            expression = expression + " " + disjunctor + " (" + new_conjunction + ")"
        j += 1

    return expression

from sklearn.tree import export_text
def steering(qfile,ofile,vulnerabilities):
    training_set = build_training_set(qfile,ofile,vulnerabilities)
    
    X = training_set.loc[:, training_set.columns != "query"]
    y = training_set["query"]
    dtree = DecisionTreeClassifier()
    dtree = dtree.fit(X, y)
    tree_mod = dtree.tree_
    feature = tree_mod.feature
    threshold = tree_mod.threshold

    paths = _extract_paths(X, dtree)
    expr = _generate_expression(training_set, tree_mod, paths, feature, threshold)
    print(expr)

    # features = list(training_set.columns)
    # features.remove("query")
    # r = export_text(dtree, feature_names=features)
    # print(r)

if __name__ == "__main__":
    query_paths = "dataset/10_10_powerlaw_uniform_0.5_1/random/samples/query_paths.json"
    other_paths = "dataset/10_10_powerlaw_uniform_0.5_1/random/samples/paths.json"
    with open("dataset/10_10_powerlaw_uniform_0.5_1/10_10_powerlaw_uniform_0.5_1.json") as f:
        all_vulns = json.load(f)["vulnerabilities"]
    steering(query_paths,other_paths,all_vulns)