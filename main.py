import datetime

import gymnasium as gym

from SFCSim2.network import Network
from SFCSim2.vnf import VNFType
from SFCSim2.sfc import SFC
# from nsfnet_template import init
from triangular_lattice_template import init
from sfc_deploy_simple_mode_env import SFCDeploySimpleModeEnv,TensorboardCallback

from stable_baselines3 import PPO, A2C
from stable_baselines3.common.callbacks import CheckpointCallback, EveryNTimesteps
from stable_baselines3.common.env_checker import check_env

template, vnf_type_template, sfc_template = init()
vnf_type_dict = {}
vnf_type_dict.update({list(vnf_type_info.keys())[0]: VNFType(vnf_type_info) for vnf_type_info in vnf_type_template})
sfc_list = [ SFC(sfc_info, vnf_type_dict) for sfc_info in sfc_template ]
network = Network(template=template, vnf_type_dict=vnf_type_dict)

env = SFCDeploySimpleModeEnv(network, vnf_type_dict, sfc_list)

# check_env(env, warn=True)

current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
checkpoint_call_back = CheckpointCallback(save_freq=10000, save_path='model/sfc_deploy_simple_mode/'+current_time+'/', name_prefix='model')
tb_call_back = TensorboardCallback()
every_n_call_back = EveryNTimesteps(n_steps=500, callback=tb_call_back)

# model = PPO('MultiInputPolicy', env, verbose=2, tensorboard_log="model/tensorboard_log/"+current_time+"/",
#             n_steps=512,
#             batch_size=256,
#             clip_range=0.5,
#             clip_range_vf=0.5,
#             ent_coef=0.01,
#             stats_window_size=10,)
model = A2C('MultiInputPolicy', env, verbose=2, tensorboard_log="model/tensorboard_log/"+current_time+"/",
            device='cpu',
            stats_window_size=10,)
model.learn(total_timesteps=150*60*60*3, callback=[checkpoint_call_back, every_n_call_back])
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
