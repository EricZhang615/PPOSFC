import datetime

import gymnasium as gym
import torch as th
from torch.utils.tensorboard import SummaryWriter

from SFCSim2.network import Network
from SFCSim2.vnf import VNFType
from SFCSim2.sfc import SFC
# from nsfnet_template import init
from triangular_lattice_template import init
from sfc_deploy_simple_mode_env import SFCDeploySimpleModeEnv

from stable_baselines3 import PPO, A2C
from stable_baselines3.common.callbacks import CheckpointCallback, EveryNTimesteps
from stable_baselines3.common.env_checker import check_env

template, vnf_type_template, sfc_template = init()
vnf_type_dict = {}
vnf_type_dict.update({list(vnf_type_info.keys())[0]: VNFType(vnf_type_info) for vnf_type_info in vnf_type_template})
sfc_list = [ SFC(sfc_info, vnf_type_dict) for sfc_info in sfc_template ]
network = Network(template=template, vnf_type_dict=vnf_type_dict)

current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
writer = SummaryWriter("model/tensorboard_log/"+current_time+"/time_monitor")
env = SFCDeploySimpleModeEnv(network, vnf_type_dict, sfc_list, deploy_mode='sp', writer=writer)

# check_env(env, warn=True)

checkpoint_call_back = CheckpointCallback(save_freq=10000, save_path='model/sfc_deploy_simple_mode/'+current_time+'/', name_prefix='model')

policy_kwargs = dict(activation_fn=th.nn.ReLU,
                     net_arch=dict(pi=[512, 512, 512, 512], vf=[512, 512, 512, 512]))
model = PPO('MultiInputPolicy', env, policy_kwargs=policy_kwargs, verbose=2, tensorboard_log="model/tensorboard_log/"+current_time+"/",
            learning_rate=0.0001,
            n_steps=512,
            batch_size=256,
            # clip_range=0.5,
            # clip_range_vf=0.5,
            ent_coef=0.02,
            stats_window_size=10,)
# model = A2C('MultiInputPolicy', env, policy_kwargs=policy_kwargs, verbose=2, tensorboard_log="model/tensorboard_log/"+current_time+"/",
#             device='cpu',
#             learning_rate=0.0001,
#             stats_window_size=10,)
model.learn(total_timesteps=150*60*60*10, callback=checkpoint_call_back)
# vec_env = model.get_env()
# obs = vec_env.reset()
# total_reward = 0
# while True:
#     action, _states = model.predict(obs)
#     obs, rewards, done, info = vec_env.step(action)
#     total_reward += rewards
#     if done:
#         obs = vec_env.reset()
#         print(total_reward)
#         total_reward = 0

# model.save("model/sfc_deploy_simple_mode/"+current_time)
