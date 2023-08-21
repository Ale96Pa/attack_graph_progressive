import os, json
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

import config

def plot_lines_steering(folder,df_experiments,sampling_algo=""):
    plt.rcParams.update({'font.size': 24})
    fig, axs = plt.subplots()
    fig.set_figwidth(15)
    fig.set_figheight(10)

    if "isSteering" in df_experiments.columns:
        index_steering = list(df_experiments[df_experiments.isSteering == True]["iteration"])
        if len(index_steering)>0:
            print("Iteration where steering started: ", index_steering[0])
    
    tot_paths = max(list(df_experiments["num_query_paths"]))#+max(list(sample_df["num_other_paths"]))
    
    grouped_by_sample = df_experiments.groupby(["steering_type"])
    labels_legend = []
    for sample, item in grouped_by_sample:
        sample_df = grouped_by_sample.get_group(sample)

        x_vals = sample_df["iteration"]
        y_vals_0 = sample_df["num_query_paths"]/tot_paths

        labels_legend.append(sample)
        axs.plot(x_vals,y_vals_0,linewidth = '3')
    
    axs.set_xlabel("iterations")
    axs.set_ylabel("% query paths")
    axs.legend(title="Steering", labels=labels_legend)
    axs.set_title("Percentage of Queried Paths to total")

    plt.savefig(folder+config.plot_folder+sampling_algo+"_steering.png", bbox_inches='tight')

def isExperiment(n,v,t,d,u,s,setting):
    if setting['n'] == n and setting['v'] == v and setting['t'] == t and \
        setting['d'] == d and setting['u'] == u and setting['s'] == s:
        return True
    else: return False

def convert_samples_to_df(sampleFile1, sampleFile2):
    with open(sampleFile1) as f1, open(sampleFile2) as f2:
        other_s = json.load(f1)
        query_s = json.load(f2)
    all_samples = other_s+query_s
    return pd.DataFrame(all_samples)

def plot_delta_variation(folder,df_aggregate,sampling_algo=""):
    plt.rcParams.update({'font.size': 22})
    fig, axs = plt.subplots(3, 1)
    fig.set_figwidth(15)
    fig.set_figheight(20)
    
    iteration_ids = list(df_aggregate["iteration"])[:-1]
    all_lengths = list(df_aggregate["length"])
    past_len=all_lengths[0]
    x_vals_len = []
    all_impacts = list(df_aggregate["impact"])
    past_imp=all_impacts[0]
    x_vals_imp = []
    all_likelihoods = list(df_aggregate["likelihood"])
    past_lik=all_likelihoods[0]
    x_vals_lik = []
    for i in range(1,len(all_lengths)):
        curr_len = all_lengths[i]
        x_vals_len.append(curr_len-past_len)
        curr_imp = all_impacts[i]
        x_vals_imp.append(curr_imp-past_imp)
        curr_lik = all_likelihoods[i]
        x_vals_lik.append(curr_lik-past_lik)

        past_len=curr_len
        past_imp=curr_imp
        past_lik=curr_lik
        
    axs[0].plot(iteration_ids, x_vals_len,linewidth = '2')
    axs[1].plot(iteration_ids, x_vals_imp,linewidth = '2')
    axs[2].plot(iteration_ids, x_vals_lik,linewidth = '2')


    # axs[0].set_xlabel("iteration")
    axs[0].set_ylabel("delta variation")
    axs[0].set_title("length", y=1.0, pad=-20)

    # axs[1].set_xlabel("iteration")
    axs[1].set_ylabel("delta variation")
    axs[1].set_title("impact", y=1.0, pad=-20)

    axs[2].set_xlabel("iteration")
    axs[2].set_ylabel("delta variation")
    axs[2].set_title("likelihood", y=1.0, pad=-20)

    plt.savefig(folder+config.plot_folder+sampling_algo+"_deltaVariation.png", bbox_inches='tight')

    # return x_vals_len,x_vals_imp,x_vals_lik

def plot_distance_boxplot(folder,dfs,gt_file,sampling_algo=""):
    plt.rcParams.update({'font.size': 18})
    fig, axs = plt.subplots(3, 1)
    fig.set_figwidth(20)
    fig.set_figheight(15)

    with open(gt_file) as f: gt_paths = json.load(f)
    df_gt = pd.DataFrame(gt_paths)
    gt_len=list(df_gt["length"])
    gt_len.sort()
    gt_imp=list(df_gt["impact"])
    gt_imp.sort()
    gt_lik=list(df_gt["likelihood"])
    gt_lik.sort()
    
    dict_sampled_len = {}
    dict_sampled_imp = {}
    dict_sampled_lik = {}
    
    for df_samples in dfs:
        grouped_by_sample = df_samples.groupby(["iteration"])

        count_s = 0
        for sample, item in grouped_by_sample:
            if count_s%10==0:
            # if (len(grouped_by_sample)>250 and count_s%30==0) or \
            #     (len(grouped_by_sample)<=250 and len(grouped_by_sample)>200 and count_s%20==0) or \
            #     (len(grouped_by_sample)<=200 and len(grouped_by_sample)>70 and count_s%5==0) or \
            #     (len(grouped_by_sample)<=70):
                sample_df = grouped_by_sample.get_group(sample)
                sampled_len = []
                sampled_imp = []
                sampled_lik = []

                s_len=list(sample_df["length"])
                s_len.sort()
                s_imp=list(sample_df["impact"])
                s_imp.sort()
                s_lik=list(sample_df["likelihood"])
                s_lik.sort()
                
                res_len = stats.ks_2samp(s_len, gt_len)
                res_imp = stats.ks_2samp(s_imp, gt_imp)
                res_lik = stats.ks_2samp(s_lik, gt_lik)
                
                sampled_len.append(res_len.statistic)
                sampled_imp.append(res_imp.statistic)
                sampled_lik.append(res_lik.statistic)
                
                if sample in dict_sampled_len.keys(): dict_sampled_len[sample]+=sampled_len
                else: dict_sampled_len[sample] = sampled_len

                if sample in dict_sampled_imp.keys(): dict_sampled_imp[sample]+=sampled_imp
                else: dict_sampled_imp[sample] = sampled_imp

                if sample in dict_sampled_lik.keys(): dict_sampled_lik[sample]+=sampled_lik
                else: dict_sampled_lik[sample] = sampled_lik
            count_s+=1
    
    dict_sampled_len = dict(sorted(dict_sampled_len.items()))
    axs[0].boxplot(dict_sampled_len.values())
    axs[0].set_xticklabels(dict_sampled_len.keys(), rotation = 90)
    axs[0].set_title("length", y=1.0, pad=-20)

    dict_sampled_imp = dict(sorted(dict_sampled_imp.items()))
    axs[1].boxplot(dict_sampled_imp.values())
    axs[1].set_xticklabels(dict_sampled_imp.keys(), rotation = 90)
    axs[1].set_title("impact", y=1.0, pad=-20)

    dict_sampled_lik = dict(sorted(dict_sampled_lik.items()))
    axs[2].boxplot(dict_sampled_lik.values())
    axs[2].set_xticklabels(dict_sampled_lik.keys(), rotation = 90)
    axs[2].set_title("likelihood", y=1.0, pad=-20)

    plt.savefig(folder+config.plot_folder+sampling_algo+"_distanceBoxplot.png", bbox_inches='tight')

if __name__ == "__main__":
    experiment_settings={
        'n': 10,
        'v': 5,
        't':"powerlaw",
        'd':"uniform",
        'u':0.5,
        's':"random"
    }

    df_steers = {}
    df_samples = {}
    GT_path_file = ""
    num_iteration_sampling = []
    for n in config.nhosts:
        for v in config.nvulns:
            for t in config.topologies:
                for d in config.distro:
                    for u in config.diversity:
                        for exp in range(1,config.num_experiments+1):
                            base_name = str(n)+'_'+str(v)+'_'+t+'_'+d+'_'+str(u)+'_'+str(exp)
                            folder_name = config.ROOT_FOLDER+base_name+"/"
                            for samplingType in os.listdir(folder_name):
                                if samplingType in config.sampling_algorithms:
                                    if isExperiment(n,v,t,d,u,samplingType,experiment_settings):
                                        file_gt = folder_name+config.gt_paths
                                        """
                                        SAMPLING
                                        """
                                        file_samples = folder_name+samplingType+config.get_samples_filename("none")
                                        file_samples_q = folder_name+samplingType+config.get_query_samples_filename("none")
                                        file_stats_sampling = folder_name+samplingType+"/"+config.stats_sampling
                                        df_exp_sample = convert_samples_to_df(file_samples, file_samples_q)
                                        
                                        num_iteration_sampling.append(max(list(df_exp_sample["iteration"])))
                                        
                                        if samplingType not in df_samples.keys(): df_samples[samplingType] = [df_exp_sample]
                                        else: df_samples[samplingType].append(df_exp_sample)

                                        if os.path.exists(file_gt): GT_path_file = file_gt
                                        """
                                        STEERING
                                        """
                                        file_steering_stats = folder_name+samplingType+"/"+config.stats_steering
                                        df_experiment = pd.read_csv(file_steering_stats)
                                        plot_lines_steering(folder_name+samplingType+"/",df_experiment)

                                        if samplingType not in df_steers.keys(): df_steers[samplingType] = [df_experiment]
                                        else: df_steers[samplingType].append(df_experiment)
    
    if not os.path.exists(config.plot_folder): os.makedirs(config.plot_folder)

    avg_iteration = sum(num_iteration_sampling)/len(num_iteration_sampling)
    for k in df_samples.keys():
        list_dfcut=[]
        for df_cut in df_samples[k]:
            d = df_cut[df_cut["iteration"]<=avg_iteration]
            list_dfcut.append(d)
        df_sampling_derivative = pd.concat(list_dfcut)
        averages_samples = df_sampling_derivative.groupby(['iteration']).median().reset_index()
        averages_samples.to_csv(config.plot_folder+"/avg_samples.csv",index=False)
        plot_delta_variation("",averages_samples,k)
    
        plot_distance_boxplot("",list_dfcut,GT_path_file,k)

    for k in df_steers.keys():
        df_sampling = pd.concat(df_steers[k])
        averages_stats = df_sampling.groupby(['iteration','num_samples','steering_type']).median().reset_index()
        averages_stats.to_csv(config.plot_folder+"/avg_stats.csv",index=False)
        plot_lines_steering("",averages_stats,k)
