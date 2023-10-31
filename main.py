import datetime

from stable_baselines3.common.callbacks import CheckpointCallback

from SFCSim2.network import Network
from SFCSim2.vnf import VNFType
from SFCSim2.sfc import SFC
from nsfnet_template import init
from sfc_deploy_simple_mode_env import SFCDeploySimpleModeEnv

from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env

template, vnf_type_template, sfc_template = init()
vnf_type_dict = {}
vnf_type_dict.update({list(vnf_type_info.keys())[0]: VNFType(vnf_type_info) for vnf_type_info in vnf_type_template})
sfc_list = [ SFC(sfc_info, vnf_type_dict) for sfc_info in sfc_template ]
network = Network(template=template, vnf_type_dict=vnf_type_dict)

env = SFCDeploySimpleModeEnv(network, vnf_type_dict, sfc_list)

check_env(env, warn=True)

current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
checkpoint_call_back = CheckpointCallback(save_freq=10000, save_path='model/sfc_deploy_simple_mode/'+current_time+'/', name_prefix='model')

model = PPO('MultiInputPolicy', env, verbose=2, tensorboard_log="model/tensorboard_log/"+current_time+"/",
            n_steps=512,
            batch_size=256,
            clip_range=0.5,
            clip_range_vf=0.5,)
model.learn(total_timesteps=150*60*60*3, callback=checkpoint_call_back)
# model.save("model/sfc_deploy_simple_mode/"+current_time)
