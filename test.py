import gymnasium as gym
import datetime

from stable_baselines3 import PPO

current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
env = gym.make('CartPole-v1')

model = PPO("MlpPolicy", env, verbose=1, tensorboard_log="model/tensorboard_log/test/"+current_time+'/',
            n_steps=512,
            batch_size=256,
            clip_range=0.5,
            clip_range_vf=0.5,
            ent_coef=0.01,)

model.learn(total_timesteps=100000)