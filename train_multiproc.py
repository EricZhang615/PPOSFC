import copy
import datetime

import gymnasium as gym
import numpy as np
import torch as th
from torch.utils.tensorboard import SummaryWriter

from SFCSim2.network import Network
from SFCSim2.vnf import VNFType
from SFCSim2.sfc import SFC
# from nsfnet_template import init
from triangular_lattice_template_600 import init
import envs

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv

if __name__ == '__main__':
    template, vnf_type_template, sfc_template = init()
    vnf_type_dict = {}
    vnf_type_dict.update({list(vnf_type_info.keys())[0]: VNFType(vnf_type_info) for vnf_type_info in vnf_type_template})
    sfc_list = [ SFC(sfc_info, vnf_type_dict) for sfc_info in sfc_template ]
    network = Network(template=template, vnf_type_dict=vnf_type_dict)

    current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    # current_time = '20231106-014601'
    writer = SummaryWriter("model/tensorboard_log/"+current_time+"/time_monitor")

    env_kwargs = {
        'render_mode': None,
        'network': network,
        'vnf_types': vnf_type_dict,
        'sfc_requests': sfc_list,
        'deploy_mode': 'vnf',
        # 'writer': writer
    }

    # env = SFCDeploySimpleModeEnv(network, vnf_type_dict, sfc_list, deploy_mode='vnf', writer=writer)
    env = make_vec_env('SFCDeploySimpleModeEnv-v0', n_envs=24, env_kwargs=env_kwargs, vec_env_cls=SubprocVecEnv, seed=np.random.randint(0, 2**31 - 1) )
    # eval_env = envs.SFCDeploySimpleModeEnv(network, vnf_type_dict, sfc_list, deploy_mode='vnf')
    eval_env = make_vec_env('SFCDeploySimpleModeEnv-v0', n_envs=1, env_kwargs=env_kwargs, vec_env_cls=SubprocVecEnv, seed=np.random.randint(0, 2**31 - 1) )
    # check_env(env, warn=True)

    checkpoint_call_back = CheckpointCallback(save_freq=10_000, save_path='model/sfc_deploy_simple_mode/'+current_time+'/', name_prefix='model')
    eval_callback = EvalCallback(eval_env, best_model_save_path='model/sfc_deploy_simple_mode/'+current_time+'/', log_path='model/sfc_deploy_simple_mode/'+current_time+'/',
                                 eval_freq=2_000, n_eval_episodes=3, deterministic=True)

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
    # model = PPO.load('model/sfc_deploy_simple_mode/20231106-014601/best_model.zip', env)
    # model = A2C('MultiInputPolicy', env, policy_kwargs=policy_kwargs, verbose=2, tensorboard_log="model/tensorboard_log/"+current_time+"/",
    #             device='cpu',
    #             learning_rate=0.0001,
    #             stats_window_size=10,)
    model.learn(total_timesteps=150*60*60*25, callback=[checkpoint_call_back, eval_callback])

    # model.save("model/sfc_deploy_simple_mode/"+current_time)
