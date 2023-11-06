from gymnasium.envs.registration import register
from envs.sfc_deploy_simple_mode_env import SFCDeploySimpleModeEnv

register(
        id='SFCDeploySimpleModeEnv-v0',
        entry_point='envs.sfc_deploy_simple_mode_env:SFCDeploySimpleModeEnv',
)