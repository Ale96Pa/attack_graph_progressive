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

def normalize_convert_samples(sampleFile):
    with open(sampleFile) as f:
        all_samples = json.load(f)
    all_stats=[]
    all_base=[]
    for sample in all_samples:
        if sample["type"] == "sample": all_base.append(sample)
        else: all_stats.append(sample)
    return pd.json_normalize(all_stats), pd.json_normalize(all_base)

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
    s_len=[]
    s_imp=[]
    s_lik=[]
    
    for df_samples in dfs:
        grouped_by_sample = df_samples.groupby(["iteration"])

        for sample, item in grouped_by_sample:
            sample_df = grouped_by_sample.get_group(sample)
            sampled_len = []
            sampled_imp = []
            sampled_lik = []

            s_len+=list(sample_df["length"])
            s_len.sort()
            s_imp+=list(sample_df["impact"])
            s_imp.sort()
            s_lik+=list(sample_df["likelihood"])
            s_lik.sort()
            
            res_len = stats.ks_2samp(gt_len,s_len)
            res_imp = stats.ks_2samp(gt_imp,s_imp)
            res_lik = stats.ks_2samp(gt_lik,s_lik)
            
            sampled_len.append(res_len.statistic)
            sampled_imp.append(res_imp.statistic)
            sampled_lik.append(res_lik.statistic)
            
            if sample in dict_sampled_len.keys(): dict_sampled_len[sample]+=sampled_len
            else: dict_sampled_len[sample] = sampled_len

            if sample in dict_sampled_imp.keys(): dict_sampled_imp[sample]+=sampled_imp
            else: dict_sampled_imp[sample] = sampled_imp

            if sample in dict_sampled_lik.keys(): dict_sampled_lik[sample]+=sampled_lik
            else: dict_sampled_lik[sample] = sampled_lik
    
    dict_sampled_len = dict(sorted(dict_sampled_len.items()))
    dict_sampled_imp = dict(sorted(dict_sampled_imp.items()))
    dict_sampled_lik = dict(sorted(dict_sampled_lik.items()))
    len_vals=[]
    len_k=[]
    imp_vals=[]
    imp_k=[]
    lik_vals=[]
    lik_k=[]
    for i in range(0,len(dict_sampled_len.values())):
        if i%5==0:
            len_vals.append(list(dict_sampled_len.values())[i])
            len_k.append(list(dict_sampled_len.keys())[i])
            imp_vals.append(list(dict_sampled_imp.values())[i])
            imp_k.append(list(dict_sampled_imp.keys())[i])
            lik_vals.append(list(dict_sampled_lik.values())[i])
            lik_k.append(list(dict_sampled_lik.keys())[i])
    
    axs[0].boxplot(len_vals)
    axs[0].set_xticklabels(len_k, rotation = 90)
    axs[0].set_title("length", y=1.0, pad=-20)

    axs[1].boxplot(imp_vals)
    axs[1].set_xticklabels(imp_k, rotation = 90)
    axs[1].set_title("impact", y=1.0, pad=-20)

    axs[2].boxplot(lik_vals)
    axs[2].set_xticklabels(lik_k, rotation = 90)
    axs[2].set_title("likelihood", y=1.0, pad=-20)

    # dict_sampled_len = dict(sorted(dict_sampled_len.items()))
    # axs[0].boxplot(dict_sampled_len.values())
    # axs[0].set_xticklabels(dict_sampled_len.keys(), rotation = 90)
    # axs[0].set_title("length", y=1.0, pad=-20)

    # dict_sampled_imp = dict(sorted(dict_sampled_imp.items()))
    # axs[1].boxplot(dict_sampled_imp.values())
    # axs[1].set_xticklabels(dict_sampled_imp.keys(), rotation = 90)
    # axs[1].set_title("impact", y=1.0, pad=-20)

    # dict_sampled_lik = dict(sorted(dict_sampled_lik.items()))
    # axs[2].boxplot(dict_sampled_lik.values())
    # axs[2].set_xticklabels(dict_sampled_lik.keys(), rotation = 90)
    # axs[2].set_title("likelihood", y=1.0, pad=-20)

    plt.savefig(folder+config.plot_folder+sampling_algo+"_distanceBoxplot.png", bbox_inches='tight')

def plot_statistics_basefeatures(folder,df,sampling_algo,val="stat"):
    axesV2 = {'metricV2.accessVector':[0,0],
    'metricV2.accessComplexity':[0,1],
    'metricV2.authentication':[0,2],
    'metricV2.confidentiality':[0,3],
    'metricV2.integrity':[0,4],
    'metricV2.availability':[1,0],
    'metricV2.severity':[1,1],
    'metricV2.score':[1,2],
    'metricV2.impact':[1,3],
    'metricV2.exploitability':[1,4]
    }

    axesV3 = {'metricV3.attackVector':[0,0],
    'metricV3.attackComplexity':[0,1],
    'metricV3.privilegeRequired':[0,2],
    'metricV3.confidentiality':[0,3],
    'metricV3.integrity':[0,4],
    'metricV3.availability':[1,0],
    'metricV3.severity':[1,1],
    'metricV3.score':[1,2],
    'metricV3.impact':[1,3],
    'metricV3.exploitability':[1,4]
    }

    
    for axes_map in [axesV2,axesV3]:
        plt.rcParams.update({'font.size': 16})
        fig, axs = plt.subplots(2, 5)
        fig.set_figwidth(25)
        fig.set_figheight(10)
        
        if axes_map==axesV2: version="v2"
        else: version="v3"

        for parameter in axes_map.keys():
            i,j = axes_map[parameter]
            ax = axs[i][j]
            
            samples = df["iteration"]
            values = df[parameter+"."+val]
            # if parameter not in [sub.replace('.stat', '').replace('.pvalue', '') for sub in list(df.columns)]: 
            #     print(parameter, "not present")
            #     continue
            
            ax.plot(samples, values)

            label_title = parameter.replace("metricV2.","").replace("metricV3.","").replace(".stat","").replace(".pvalue","")
            ax.set_title(label_title, y=1.0, pad=-20)
            if i == 1: ax.set_xlabel("iteration")
            if j == 0:
                if val == "stat": ax.set_ylabel("distance")
                elif val == "pvalue": ax.set_ylabel("p-value")
                else: ax.set_ylabel("collision rate")

        plt.savefig(folder+config.plot_folder+sampling_algo+"_base_features_"+val+"_"+version+".png", bbox_inches='tight')

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
    df_stats = {}
    GT_path_file = ""
    num_iteration_sampling = []
    for n in config.nhosts:
        for v in config.nvulns:
            for t in config.topologies:
                for d in config.distro:
                    for u in config.diversity:
                        base_name = str(n)+'_'+str(v)+'_'+t+'_'+d+'_'+str(u)
                        folder_name = config.ROOT_FOLDER+base_name+"/"
                        
                        for samplingType in os.listdir(folder_name):
                            if samplingType in config.sampling_algorithms:
                                for exp in range(1,config.num_experiments+1):
                                    if isExperiment(n,v,t,d,u,samplingType,experiment_settings):
                                        """
                                        SAMPLING
                                        """
                                        GT_path_file = folder_name+config.gt_paths

                                        filename_sample_other = folder_name+samplingType+\
                                                    "/exp"+str(exp)+config.get_samples_filename("none")
                                        filename_sample_query = folder_name+samplingType+\
                                                    "/exp"+str(exp)+config.get_query_samples_filename("none")
                                        filename_sampling_stats = folder_name+samplingType+\
                                                    "/exp"+str(exp)+"/"+config.stats_sampling
                                        
                                        df_exp_sample = convert_samples_to_df(filename_sample_other, filename_sample_query)
                                        num_iteration_sampling.append(max(list(df_exp_sample["iteration"])))
                                        
                                        if samplingType not in df_samples.keys(): df_samples[samplingType] = [df_exp_sample]
                                        else: df_samples[samplingType].append(df_exp_sample)

                                        df_base_stats, df_base_samples = normalize_convert_samples(filename_sampling_stats)
                                        if samplingType not in df_stats.keys(): df_stats[samplingType] = [df_base_stats]
                                        else: df_stats[samplingType].append(df_base_stats)
                                        
                                        """
                                        STEERING
                                        """
                                        filename_steering_stats = folder_name+samplingType+\
                                                    "/exp"+str(exp)+"/"+config.stats_steering
                                        df_experiment = pd.read_csv(filename_steering_stats)
                                        # plot_lines_steering(folder_name+samplingType+"/",df_experiment)

                                        if samplingType not in df_steers.keys(): df_steers[samplingType] = [df_experiment]
                                        else: df_steers[samplingType].append(df_experiment)
    
    if not os.path.exists(config.plot_folder): os.makedirs(config.plot_folder)

    for k in df_stats.keys():
        df_sampling_base = pd.concat(df_stats[k])
        averages_base_stats = df_sampling_base.groupby(['iteration']).mean().reset_index()
        averages_base_stats.to_csv(config.plot_folder+"/avg_base_stats.csv",index=False)
        plot_statistics_basefeatures("",averages_base_stats,k)

    avg_iteration = sum(num_iteration_sampling)/len(num_iteration_sampling)
    for k in df_samples.keys():
        # list_dfcut=[]
        # for df_cut in df_samples[k]:
        #     d = df_cut[df_cut["iteration"]<=avg_iteration]
        #     list_dfcut.append(d)
        df_sampling_derivative = pd.concat(df_samples[k])
        averages_samples = df_sampling_derivative.groupby(['iteration']).median().reset_index()
        averages_samples.to_csv(config.plot_folder+"/avg_samples.csv",index=False)
        plot_delta_variation("",averages_samples,k)
    
        if GT_path_file!="": plot_distance_boxplot("",df_samples[k],GT_path_file,k)

    for k in df_steers.keys():
        df_sampling = pd.concat(df_steers[k])
        averages_stats = df_sampling.groupby(['iteration','num_samples','steering_type']).median().reset_index()
        averages_stats.to_csv(config.plot_folder+"/avg_stats.csv",index=False)
        plot_lines_steering("",averages_stats,k)
