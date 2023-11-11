import gymnasium as gym
import numpy as np
import torch as th
from stable_baselines3 import PPO

import envs

from SFCSim2.network import Network
from SFCSim2.vnf import VNFType
from SFCSim2.sfc import SFC
from custom_features_extractor import TransformerExtractor
# from nsfnet_template import init
from triangular_lattice_template_600 import init

template, vnf_type_template, sfc_template = init()
vnf_type_dict = {}
vnf_type_dict.update({list(vnf_type_info.keys())[0]: VNFType(vnf_type_info) for vnf_type_info in vnf_type_template})
sfc_list = [ SFC(sfc_info, vnf_type_dict) for sfc_info in sfc_template ]
network = Network(template=template, vnf_type_dict=vnf_type_dict)

env = envs.SFCDeploySimpleModeEnv(network, vnf_type_dict, sfc_list, deploy_mode='vnf', tf=True)

# env.reset()
# total_reward = 0
# ep = 0
# while ep!=10:
#     action = np.random.randint(0, 35, 3)
#     # action = 1
#     obs, rewards, terminate, trunc, info = env.step(action)
#     total_reward += rewards
#     if terminate:
#         print(f'delay: {env.delay_mean}')
#         env.reset()
#         print(total_reward)
#         total_reward = 0
#         ep += 1

policy_kwargs = dict(activation_fn=th.nn.ReLU,
                     net_arch=dict(pi=[256, 256], vf=[256, 256]),
                     features_extractor_class=TransformerExtractor,)
model = PPO('MultiInputPolicy', env, policy_kwargs=policy_kwargs, verbose=2,
                learning_rate=0.0001,
                n_steps=1024,
                batch_size=256,
                # clip_range=0.5,
                # clip_range_vf=0.5,
                ent_coef=0.02,
                stats_window_size=10,)

model.learn(total_timesteps=100000)