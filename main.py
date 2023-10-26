

from SFCSim2.network import Network
from SFCSim2.vnf import VNFType
from SFCSim2.sfc import SFC
from nsfnet_template import init
from sfc_deploy_simple_mode_env import SFCDeploySimpleModeEnv
from stable_baselines3.common.env_checker import check_env

template, vnf_type_template, sfc_template = init()
vnf_type_dict = {}
vnf_type_dict.update({list(vnf_type_info.keys())[0]: VNFType(vnf_type_info) for vnf_type_info in vnf_type_template})
sfc_list = [ SFC(sfc_info, vnf_type_dict) for sfc_info in sfc_template ]
network = Network(template=template, vnf_type_dict=vnf_type_dict)

env = SFCDeploySimpleModeEnv(network, vnf_type_dict, sfc_list)

check_env(env, warn=True)