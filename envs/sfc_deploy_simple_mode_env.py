import copy
import random
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from gymnasium.core import ObsType
from stable_baselines3.common.callbacks import BaseCallback
from torch.utils.tensorboard import SummaryWriter

from SFCSim2.network import Network


class SFCDeploySimpleModeEnv(gym.Env):
    def __init__(self, network: Network, vnf_types, sfc_requests, deploy_mode='vnf', writer: SummaryWriter = None, **kwargs):
        super().__init__()
        self._deploy_mode = deploy_mode
        self.network = network
        self.num_nodes = len(self.network.nodes)
        self.num_edges = len(self.network.edges)
        self.vnf_types = vnf_types
        self.sfc_requests = sfc_requests
        self.sfc_request_mark = 0
        self.sfc_handled = []
        self.num_deployed = 0
        self.delay_mean = 0.0
        self._writer = writer

        # 观测空间 节点数*3属性（cpu mem delay）+链路数*1属性（bandwidth）+节点数*1（sfc入出节点01编码）+vnf需求2*3+sfc带宽
        self.observation_space = spaces.Dict(
            {
                'nodes_cpu': spaces.Box(low=0, high=1, shape=(self.num_nodes, )),
                'nodes_mem': spaces.Box(low=0, high=1, shape=(self.num_nodes, )),
                'nodes_delay': spaces.Box(low=0, high=1, shape=(self.num_nodes, )),
                # 'edges': spaces.Box(low=0, high=1, shape=(self.num_edges, )),
                'sfc_in_out_nodes': spaces.MultiBinary(self.num_nodes),
                'sfc_request_vnfs': spaces.Box(low=0, high=1, shape=(3*2, )),
                # 'sfc_bandwidth': spaces.Box(low=0, high=1, shape=(1,))
            }
        )
        if deploy_mode == 'vnf':
            # 动作空间 节点数^3
            self.action_space = spaces.MultiDiscrete([len(self.network.nodes), len(self.network.nodes), len(self.network.nodes)])
        elif deploy_mode == 'sp':
            # 动作空间 前k最短路径
            self.action_space = spaces.Discrete(5)

    def _get_obs(self):
        cpu = []
        mem = []
        delay = []
        for node in self.network.nodes:
            cpu.append(self.network.nodes[node]['resources_cpu_used'] / self.network.nodes[node]['resources_cpu'])
            mem.append(self.network.nodes[node]['resources_mem_used'] / self.network.nodes[node]['resources_mem'])
            delay.append(self.network.nodes[node]['processing_delay'] / (self.network.nodes[node]['processing_delay_base'] * 20))

        # bw = [ self.network.edges[edge]['bandwidth_used'] / self.network.edges[edge]['bandwidth'] for edge in self.network.edges]

        sfc_in_out_nodes = [ 0 for _ in range(self.num_nodes)]
        list_of_nodes = list(self.network.nodes)
        sfc_in_out_nodes[list_of_nodes.index(self.sfc_requests[self.sfc_request_mark].nodes['in']['node_in'])] = 1
        sfc_in_out_nodes[list_of_nodes.index(self.sfc_requests[self.sfc_request_mark].nodes['out']['node_out'])] = 1

        # remember to modify the MAGIC NUMBERS 100 500
        sfc_request_vnfs = []
        for vnf in self.sfc_requests[self.sfc_request_mark].nodes:
            if vnf == 'in' or vnf == 'out':
                continue
            sfc_request_vnfs.append(self.sfc_requests[self.sfc_request_mark].nodes[vnf]['vnf_type'].resources_cpu_demand / 100)
            sfc_request_vnfs.append(self.sfc_requests[self.sfc_request_mark].nodes[vnf]['vnf_type'].resources_mem_demand / 100)

        # sfc_bandwidth = [ self.sfc_requests[self.sfc_request_mark].bandwidth / 500 ]

        return {
            'nodes_cpu': np.array(cpu).astype(np.float32),
            'nodes_mem': np.array(mem).astype(np.float32),
            'nodes_delay': np.array(delay).astype(np.float32),
            # 'edges': np.array(bw).astype(np.float32),
            'sfc_in_out_nodes': np.array(sfc_in_out_nodes).astype(np.int8),
            'sfc_request_vnfs': np.array(sfc_request_vnfs).astype(np.float32),
            # 'sfc_bandwidth': np.array(sfc_bandwidth).astype(np.float32)
        }

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[ObsType, dict[str, Any]]:
        super().reset(seed=seed)

        self.network.reset()
        self.network.update_delay()
        self.sfc_request_mark = 0
        self.sfc_handled = []

        # 打乱sfc请求
        # random.shuffle(self.sfc_requests)

        observation = self._get_obs()

        return observation, {}

    def _get_reward(self, sfc_is_deployed: bool):
        reward = 0.0
        deployed = 0
        idle = 0
        total = len(self.sfc_requests)
        total_delay = 0.0
        for sfc in self.sfc_handled:
            if sfc.is_deployed():
                deployed += 1
                total_delay += sfc.delay_actual
        avg_delay = total_delay / deployed
        self.num_deployed = deployed
        self.delay_mean = avg_delay
        if sfc_is_deployed:
            # reward = 1.6 * ((self.sfc_request_mark+1) / total) - avg_delay / 1000
            if self.sfc_request_mark > 310:
                reward = 1.5
            else:
                reward = 1 - self.sfc_handled[-1].delay_actual / 500
        else:
            # reward = -1 * (1 - self.sfc_request_mark / total)
            if self.sfc_request_mark <= 310:
                reward = -1
            else:
                reward = 0
            # reward = -1
        if self.sfc_request_mark == len(self.sfc_requests) - 1:
            reward = 500 - avg_delay
            # print('deployed: ', deployed, 'avg_delay: ', avg_delay, 'reward: ', reward)
            if self._writer is not None:
                self._writer.add_scalar('debug/reward', reward)
                self._writer.add_scalar('debug/avg_delay', avg_delay)
                self._writer.add_scalar('debug/deployed', deployed)
        return reward

    def step(self, action):
        reward = 0.0
        terminated = False
        if self._deploy_mode == 'vnf':
            # 将动作转换为 target_node_dict
            target_node_dict = {}
            for i in range(len(action)):
                target_node_dict['vnf' + str(i + 1)] = list(self.network.nodes)[action[i]]
            # 部署sfc
            sfc_req = copy.deepcopy(self.sfc_requests[self.sfc_request_mark])
            err, msg =  self.network.deploy_sfc_by_vnf(sfc_req, target_node_dict, is_delay_limit_enable=False)
            # if err is False:
            #     print(msg)
            self.sfc_handled.append(sfc_req)
        elif self._deploy_mode == 'sp':
            # 部署sfc
            sfc_req = copy.deepcopy(self.sfc_requests[self.sfc_request_mark])
            err, msg =  self.network.deploy_sfc_by_sp(sfc_req, action, is_delay_limit_enable=False)
            self.sfc_handled.append(sfc_req)

        # 更新所有已部署sfc延时
        for sfc in self.sfc_handled:
            if sfc.is_deployed():
                err, msg = sfc.update_delay_simple_model(self.network)
                if err is False:
                    print(msg)

        # 计算reward
        reward = self._get_reward(self.sfc_handled[-1].is_deployed())
        if self.sfc_request_mark == len(self.sfc_requests) - 1:
            terminated = True
        else:
            self.sfc_request_mark += 1

        observation = self._get_obs()

        return observation, reward, terminated, False, {}


class TensorboardCallback(BaseCallback):
    def __init__(self, verbose=0):
        super().__init__(verbose)
        self.training_env = None

    def _on_step(self) -> bool:
        num_deployed = self.training_env.envs[0].env.num_deployed
        delay_mean = self.training_env.envs[0].env.delay_mean
        self.logger.record('num_deployed', num_deployed)
        self.logger.record('delay_mean', delay_mean)
        return True
