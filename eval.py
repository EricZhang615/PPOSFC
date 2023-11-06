from SFCSim2.network import Network
from SFCSim2.vnf import VNFType
from SFCSim2.sfc import SFC
# from nsfnet_template import init
from triangular_lattice_template import init
from envs.sfc_deploy_simple_mode_env import SFCDeploySimpleModeEnv

from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy

template, vnf_type_template, sfc_template = init()
vnf_type_dict = {}
vnf_type_dict.update({list(vnf_type_info.keys())[0]: VNFType(vnf_type_info) for vnf_type_info in vnf_type_template})
sfc_list = [ SFC(sfc_info, vnf_type_dict) for sfc_info in sfc_template ]
network = Network(template=template, vnf_type_dict=vnf_type_dict)

eval_env = SFCDeploySimpleModeEnv(network, vnf_type_dict, sfc_list, deploy_mode='sp')
model = PPO.load('model/sfc_deploy_simple_mode/20231103-011056/model_5190000_steps.zip', env=eval_env)

# eval_env = SFCDeploySimpleModeEnv(network, vnf_type_dict, sfc_list, deploy_mode='vnf')
# model = PPO.load('model/sfc_deploy_simple_mode/20231106-014601/best_model.zip', env=eval_env)

# mean_reward, std_reward = evaluate_policy(model, model.get_env(), n_eval_episodes=10)

vec_env = model.get_env()
obs = vec_env.reset()
action_list = []
total_reward = 0
for i in range(1000):
    action, _states = model.predict(obs, deterministic=True)
    action_list.append(action)
    obs, rewards, dones, info = vec_env.step(action)
    total_reward += rewards
    if dones or i == 298:
        print(total_reward)
        break
        # obs = vec_env.reset()