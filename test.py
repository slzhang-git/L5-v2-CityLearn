import pickle
import time
import numpy as np
from citylearn.citylearn import CityLearnEnv
from citylearn.simulator import Simulator
from citylearn.utilities import read_json

# revised for file path editing
import os   
current_directory=os.getcwd()
local_directory="citylearn/data/citylearn_challenge_2022_phase_1/schema.json"
final_directory=os.path.join(current_directory, local_directory)
schema = read_json(final_directory)
schema['root_directory']=os.path.join(current_directory,"citylearn/data/citylearn_challenge_2022_phase_1/")
# revised for file path editing

RESULT_FILEPATH = 'simulation.pkl'
#   schema = 'citylearn_challenge_2022_phase_1' # revised for file path editing
#   schema = read_json('/Users/kingsleyenweye/Desktop/INTELLIGENT_ENVIRONMENT_LAB/citylearn/CityLearn/citylearn/data/citylearn_challenge_2022_phase_1/schema.json') # revised for file path editing
# schema['episodes'] = 1
# schema['simulation_end_time_step'] = 100
schema['agent']['type'] = 'citylearn.agents.marlisa.MARLISA'    
#   schema['root_directory'] = '/Users/kingsleyenweye/Desktop/INTELLIGENT_ENVIRONMENT_LAB/citylearn/CityLearn/citylearn/data/citylearn_challenge_2022_phase_1/' # revised for file path editing

def main():
    # simulation
    citylearn_env = CityLearnEnv(schema)
    agent = citylearn_env.load_agent()
    simulator = Simulator(citylearn_env, agent, citylearn_env.schema['episodes'])
    simulator.simulate()

    # post-simulation evaluation
    values = {
        'nec': sum(simulator.citylearn_env.net_electricity_consumption),
        'newc': sum(simulator.citylearn_env.net_electricity_consumption_without_storage),
        'necp': sum(simulator.citylearn_env.net_electricity_consumption_price),
        'newcp': sum(simulator.citylearn_env.net_electricity_consumption_without_storage_price),
        'nece': sum(simulator.citylearn_env.net_electricity_consumption_emission),
        'newce': sum(simulator.citylearn_env.net_electricity_consumption_without_storage_emission),
    }
    values['necr'] = values['nec']/values['newc']
    values['necpr'] = values['necp']/values['newcp']
    values['necer'] = values['nece']/values['newce']
    print('values:',values)

    # save simulator to file
    with open(RESULT_FILEPATH, 'wb') as f:
        pickle.dump(simulator,f)

if __name__ == '__main__':
    start_time = time.time()
    main()
    runtime = time.time() - start_time
    print('runtime:',runtime)
