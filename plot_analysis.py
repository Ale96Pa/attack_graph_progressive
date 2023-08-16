import os, json
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

import config

def plot_lines_steering(folder,df_experiments,sampling_algo=""):
    plt.rcParams.update({'font.size': 24})
    fig, axs = plt.subplots()
    fig.set_figwidth(20)
    fig.set_figheight(10)

    if "isSteering" in df_experiments.columns:
        index_steering = list(df_experiments[df_experiments.isSteering == True]["iteration"])
        if len(index_steering)>0:
            print("Iteration where steering started: ", index_steering[0])
    

    grouped_by_sample = df_experiments.groupby(["steering_type"])
    labels_legend = []
    for sample, item in grouped_by_sample:
        sample_df = grouped_by_sample.get_group(sample)

        tot_paths = max(list(sample_df["num_query_paths"]))#+max(list(sample_df["num_other_paths"]))

        x_vals = sample_df["iteration"]
        y_vals_0 = sample_df["num_query_paths"]/tot_paths

        labels_legend.append(sample)
        axs.plot(x_vals,y_vals_0,linewidth = '3')
    
    axs.set_xlabel("iterations")
    axs.set_ylabel("num. in-query paths")
    axs.legend(title="Steering", labels=labels_legend)
    axs.set_title("Percentage of Queried Paths to total")

    plt.savefig(folder+config.plot_folder+sampling_algo+"_steering.png", bbox_inches='tight')

if __name__ == "__main__":
    # for subfolder in os.listdir(config.ROOT_FOLDER):
    #     for samplingType in os.listdir(config.ROOT_FOLDER+subfolder):
    #         if samplingType in config.sampling_algorithms:
    #             folder_experiment = config.ROOT_FOLDER+subfolder+"/"+samplingType+"/"
    #             file_steering_stats = config.ROOT_FOLDER+subfolder+"/"+samplingType+"/"+config.stats_steering
    #             df_steer = pd.read_csv(file_steering_stats)
    #             plot_lines_steering(folder_experiment,df_steer)
    for n in config.nhosts:
        for v in config.nvulns:
            for t in config.topologies:
                for d in config.distro:
                    for u in config.diversity:
                        df_steers = {}
                        for exp in range(1,config.num_experiments+1):
                            base_name = str(n)+'_'+str(v)+'_'+t+'_'+d+'_'+str(u)+'_'+str(exp)
                            folder_name = config.ROOT_FOLDER+base_name+"/"
                            for samplingType in os.listdir(folder_name):
                                if samplingType in config.sampling_algorithms:
                                    file_steering_stats = folder_name+samplingType+"/"+config.stats_steering
                                    df_experiment = pd.read_csv(file_steering_stats)
                                    plot_lines_steering(folder_name+samplingType+"/",df_experiment)

                                    if samplingType not in df_steers.keys(): df_steers[samplingType] = [df_experiment]
                                    else: df_steers[samplingType].append(df_experiment)
    
    if not os.path.exists(config.plot_folder): os.makedirs(config.plot_folder)

    for k in df_steers.keys():
        df_sampling = pd.concat(df_steers[k])
        averages_stats = df_sampling.groupby(['iteration','num_samples','steering_type']).median().reset_index()
        averages_stats.to_csv(config.plot_folder+"/avg_stats.csv",index=False)
        plot_lines_steering("",averages_stats,k)
