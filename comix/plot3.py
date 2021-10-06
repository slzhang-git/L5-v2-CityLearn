import os
import sys
sys.path.append('../')
from citylearn import  CityLearn
import matplotlib.pyplot as plt
from pathlib import Path
from agents.rbc import RBC
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import json
from copy import deepcopy

def rbc_cost():
    # Select the climate zone and load environment
    climate_zone = 5
    sim_period = (0, 8760-1)
    params = {'data_path':Path("../data/Climate_Zone_"+str(climate_zone)), 
            'building_attributes':'building_attributes.json', 
            'weather_file':'weather_data.csv', 
            'solar_profile':'solar_generation_1kW.csv', 
            'carbon_intensity':'carbon_intensity.csv',
            'building_ids':["Building_"+str(i) for i in [1,2,3,4,5,6,7,8,9]],
            'buildings_states_actions':'buildings_state_action_space.json', 
            'simulation_period': sim_period, 
            'cost_function': ['ramping','1-load_factor','average_daily_peak','peak_demand','net_electricity_consumption','carbon_emissions'], 
            'central_agent': False,
            'save_memory': False }

    env = CityLearn(**params)
    observations_spaces, actions_spaces = env.get_state_action_spaces()
    # Simulation without energy storage
    env.reset()
    done = False
    while not done:
        _, rewards, done, _ = env.step([[0 for _ in range(len(actions_spaces[i].sample()))] for i in range(9)])
    env.cost()
    env.close()
    return env.net_electric_consumption

def get_cost(x):
    x = x.reshape(-1)
    cost = {}
    cost['ramping'] = np.abs((x - np.roll(x,1))[1:]).sum()
    cost['1-load_factor'] = np.mean([1-np.mean(x[i:i+int(8760/12)])/ np.max(x[i:i+int(8760/12)]) for i in range(0,len(x), int(8760/12))])
    cost['average_daily_peak'] = np.mean([x[i:i+24].max() for i in range(0,len(x),24)])
    cost['peak_demand'] = x.max()
    cost['net_electricity_consumption'] = x.clip(min=0).sum()
    return cost

def plot(rew):
    methods = ["iql-cem", "covdn", "covdn-naf", "comix", "comix-naf", "maddpg", "facmaddpg"]
    MM = {
        "comix": "COMIX", 
        "comix-naf": "COMIX-NAF", 
        "covdn":"COVDN", 
        "covdn-naf":"COVDN-NAF", 
        "facmaddpg": "FAC-MADDPG", 
        "maddpg":"MADDPG", 
        "iql-cem":"IQL",
        "rbc":"RBC",
        "no pv/storage": "no pv/storage"}

    color_maps = {}
    for i, m in enumerate(methods):
        color_maps[m] = f"C{i}"

    color_maps['rbc'] = 'k'
    color_maps['no pv/storage'] = 'gray'

    sacreds = np.array([ 
        [6,  4, 5, 8,  7, 2, 1],
        [13,11,12, 9, 16,10,15],
        [23,18,19,20,17,21,24]])

    seasons = ["spring", "summer", "fall", "winter"]

    season_intervals = {
        "spring": (24*(31+28), 24*(31+28+31+30+31)),
        "summer": (24*(31+28+31+30+31), 24*(31+28+31+30+31+30+31+31)),
        "fall":   (24*(31+28+31+30+31+30+31+31), 24*(31+28+31+30+31+30+31+31+30+31+30)),
        "winter": (24*(-31), 24*(31+28)),
    }

    results = {
        "net_electric_consumption_no_pv_no_storage": {},
        "net_electric_consumption_no_storage": {},
        "net_electric_consumption": {},
        "cost": {},
    }

    keys = None
    for method in methods:
        n1,n2,n3,c = [],[],[],[]
        for seed in [1]:
            res = np.load(f"./saved_envs/{method}_{rew}_{seed}", allow_pickle=True)
            ne1 = res["ne1"]
            ne2 = res["ne2"]
            ne3 = res["ne3"]
            try:
                cost = res["cost"].item()
            except:
                cost = res["cost"][1]
                tmp = {}
                for key in cost:
                    tmp[key[:-8]] = cost[key]
                cost = tmp
            n1.append(ne1)
            n2.append(ne2)
            n3.append(ne3)
            c.append(cost)

        n1 = np.array(n1)
        n2 = np.array(n2)
        n3 = np.array(n3)
        cc = {}
        for k in c[0].keys():
            cc[k] = np.array([ci[k] for ci in c])
        results["net_electric_consumption_no_pv_no_storage"][method] = n1
        results["net_electric_consumption_no_storage"][method] = n2
        results["net_electric_consumption"][method] = n3
        results["cost"][method] = cc
        keys = cost.keys()

    cc = rbc_cost()
    results["net_electric_consumption"]["rbc"] = np.array([cc])

    fs = 15
    lw = 5

    ### plot the season electric consumption

    fig, ax = plt.subplots(1,1,figsize=(20, 5))
    for i, method in enumerate(["rbc"] + methods):
        y = results["net_electric_consumption"][method].reshape(-1)
        ax.plot(np.arange(y.shape[0]), y, label=method, color=color_maps[method])

    #base = 0
    #for i, method in enumerate(["rbc"]+methods):
    #    y = results["net_electric_consumption"][method]
    #    cost = get_cost(y)
    #    if method == "rbc":
    #        base = deepcopy(cost)
    #    print(method, cost)
    #    w = 0.1
    #    x = i*0.1
    #    ax.bar([x, x+4, x+8, x+12, x+16],
    #        [cost['ramping']/base['ramping'], cost['1-load_factor']/base['1-load_factor'], cost['average_daily_peak']/base['average_daily_peak'], cost['peak_demand']/base['peak_demand'], cost['net_electricity_consumption']/base['net_electricity_consumption']],
    #        width=w, label=method)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"imgs/{rew}_year.png", format='png', dpi=300)
    plt.close()
    return
    #for season in seasons:
    #    fig, ax = plt.subplots(1,1,figsize=(5, 5))
    #    year = 1
    #    rg = season_intervals[season]
    #    interval = range((year-1)*8760 + rg[0], (year-1)*8760 + rg[1])

    #    x = np.arange(24)
    #    #y1 = results["net_electric_consumption_no_pv_no_storage"]["comix"][interval].reshape(-1,24).mean(0)
    #    #y2 = results["net_electric_consumption_no_storage"]["comix"][interval].reshape(-1,24).mean(0)

    #    #ax.plot(x, y2, label="no_storage", color="tab:gray", linewidth=lw)

    #    for method in (["rbc"] + methods):
    #        y = results["net_electric_consumption"][method][...,interval]
    #        y = y.reshape(1, -1, 24).mean(1)
    #        if method == 'rbc':
    #            ax.plot(x, y.mean(0), label=MM[method], color=color_maps[method], linewidth=4.0)
    #        else:
    #            ax.plot(x, y.mean(0), label=MM[method], color=color_maps[method], linewidth=2.0)
    #        #ax.fill_between(x, y.mean(0)-y.std(), y.mean(0)+y.std(), color=color_maps[method], alpha=0.1)
    #        #ax.plot(x, y, label=method, color=color_maps[method], linewidth=lw)

    #    #y = results["net_electric_consumption_no_pv_no_storage"]["comix"][...,interval]
    #    #y = y.reshape(1, -1, 24).mean(1)
    #    #ax.plot(x, y.mean(0), label=MM["no pv/storage"], color='gray', linewidth=4.0)
    # 
    #    ax.set_xlabel("Hour", fontsize=15)
    #    ax.set_ylim(0, 500)
    #    ax.grid()
    #    ax.set_title(season.title(), fontsize=(fs+5))
    #    ax.set_ylabel("Net Electric Consumption", fontsize=15)
    #    plt.tight_layout()
    #    plt.savefig(f"imgs/{rew}_{season}.png", format='png', dpi=300)
    #    plt.close()

    # Create a color palette
    plt.figure()
    colors = [color_maps[x] for x in ["no pv/storage","rbc"] + methods]
    palette = dict(zip([MM[x] for x in ["no pv/storage","rbc"] +methods], colors))
    # Create legend handles manually
    handles = [matplotlib.patches.Patch(color=palette[x], label=x) for x in palette.keys()]
    # Create legend
    plt.legend(handles=handles)
    # Get current axes object and turn off axis
    plt.gca().set_axis_off()
    plt.tight_layout()
    plt.savefig(f"imgs/{rew}_season_legend.png", format='png', dpi=300)
    plt.close()


    ### plot the cost
    n = len(keys)-1
    Y = np.arange(n) * (len(methods)*0.5 * 2)
    fig, ax = plt.subplots()
    ax.axvline(x=1, ymin=0, ymax=1000, linestyle='--', color='k', linewidth=2.0)
    for ki, key in enumerate(keys):
        if key == 'coordination_score':
            continue
        for i,method in enumerate(methods):
            value = results["cost"][method][key]
            plt.barh(Y[ki]+i*0.5, value.mean(), xerr=value.std(), color=color_maps[method], height=0.5)

    ax.set_yticks(Y+len(methods)/2*0.1)
    ax.set_yticklabels([k.title() for k in list(keys)[:-1]], fontsize=15)
    plt.tight_layout()
    plt.savefig(f"imgs/{rew}_cost.png", format='png', dpi=300)
    plt.close()


plot("exp")
plot("mixed")
plot("marlisa")
plot("ramping_square")