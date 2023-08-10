import os
import pandas as pd
import config

from reachability_graph import clean_benchmark,build_reachability


def build_dataset(clean_data=False):
    if clean_data: clean_benchmark(config.ROOT_FOLDER)

    if not os.path.exists(config.ROOT_FOLDER): os.makedirs(config.ROOT_FOLDER)
    generated_files = os.listdir(config.ROOT_FOLDER)
    
    nhosts = [10]
    nvulns = [15]
    topologies = ["powerlan"]
    distro = ["uniform"]
    diversity = [0.5]
    
    for n in nhosts:
        for v in nvulns:
            for t in topologies:
                for d in distro:
                    for u in diversity:
                        base_name = str(n)+'_'+str(v)+'_'+t+'_'+d+'_'+str(u)
                        folder_name = config.ROOT_FOLDER+base_name+"/"
                        filename = base_name+".json"
                        if not os.path.exists(folder_name): os.makedirs(folder_name)
                        if base_name not in generated_files:
                            correct_filename = build_reachability(folder_name,filename)
                            correct_folder = config.ROOT_FOLDER+correct_filename.split(".json")[0]+"/"
                            if correct_folder != folder_name:
                                os.rename(folder_name, correct_folder)
                                folder_name = correct_folder
                        
                        stat_folder = folder_name+config.stat_folder
                        plot_folder = folder_name+config.plot_folder
                        samples_folder = folder_name+config.samples_folder
                        gt_folder = folder_name+config.gt_folder
                        if not os.path.exists(stat_folder): os.mkdir(stat_folder)
                        if not os.path.exists(plot_folder): os.mkdir(plot_folder)
                        if not os.path.exists(samples_folder): os.mkdir(samples_folder)
                        if not os.path.exists(gt_folder): os.mkdir(gt_folder)

if __name__ == "__main__":
    build_dataset(True)