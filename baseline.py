import gymnasium as gym
import numpy as np

import envs

from SFCSim2.network import Network
from SFCSim2.vnf import VNFType
from SFCSim2.sfc import SFC
# from nsfnet_template import init
from triangular_lattice_template_600 import init

template, vnf_type_template, sfc_template = init()
vnf_type_dict = {}
vnf_type_dict.update({list(vnf_type_info.keys())[0]: VNFType(vnf_type_info) for vnf_type_info in vnf_type_template})
sfc_list = [ SFC(sfc_info, vnf_type_dict) for sfc_info in sfc_template ]
network = Network(template=template, vnf_type_dict=vnf_type_dict)

k_sp = 20
env = envs.SFCDeploySimpleModeEnv(network, vnf_type_dict, sfc_list, deploy_mode='sp', k_sp=k_sp)

env.reset()
total_reward = 0
ep = 0
while ep!=1:
    delay = np.inf
    action = 0
    for k in range(k_sp):
        delay_k = env.network.deploy_sfc_by_sp(env.sfc_requests[env.sfc_request_mark], k, is_delay_limit_enable=False, check_delay_only=True)
        if isinstance(delay_k, float) and delay_k < delay:
            delay = delay_k
            action = k

    obs, rewards, terminate, trunc, info = env.step(action)
    total_reward += rewards
    if terminate:
        print(f'delay_mean: {env.delay_mean}')
        env.reset()
        print(total_reward)
        total_reward = 0
        ep += 1
