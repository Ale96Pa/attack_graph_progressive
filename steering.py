def isQuery(query,attack_path):
    for k in query.keys():
        min_v, max_v = query[k]
        if attack_path[k] < min_v or attack_path[k] > max_v: return False
    return True