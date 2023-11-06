import gymnasium as gym
import numpy as np

import envs

from SFCSim2.network import Network
from SFCSim2.vnf import VNFType
from SFCSim2.sfc import SFC
# from nsfnet_template import init
from triangular_lattice_template import init

template, vnf_type_template, sfc_template = init()
vnf_type_dict = {}
vnf_type_dict.update({list(vnf_type_info.keys())[0]: VNFType(vnf_type_info) for vnf_type_info in vnf_type_template})
sfc_list = [ SFC(sfc_info, vnf_type_dict) for sfc_info in sfc_template ]
network = Network(template=template, vnf_type_dict=vnf_type_dict)

env = envs.SFCDeploySimpleModeEnv(network, vnf_type_dict, sfc_list, deploy_mode='vnf')

env.reset()
total_reward = 0
ep = 0
while ep!=10:
    action = np.random.randint(0, 35, 3)
    # action = 1
    obs, rewards, terminate, trunc, info = env.step(action)
    total_reward += rewards
    if terminate:
        env.reset()
        print(total_reward)
        total_reward = 0
        ep += 1

# model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="model/tensorboard_log/test/"+current_time+'/',
#             n_steps=512,
#             batch_size=256,
#             clip_range=0.5,
#             clip_range_vf=0.5,
#             ent_coef=0.01,)
#
# model.learn(total_timesteps=100000)