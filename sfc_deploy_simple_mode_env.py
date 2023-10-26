import copy
import random
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from gymnasium.core import ObsType

from SFCSim2.network import Network


class SFCDeploySimpleModeEnv(gym.Env):
    def __init__(self, network: Network, vnf_types, sfc_requests):
        super().__init__()
        self.network = network
        self.num_nodes = len(self.network.nodes)
        self.num_edges = len(self.network.edges)
        self.vnf_types = vnf_types
        self.sfc_requests = sfc_requests
        self.sfc_request_mark = 0
        self.sfc_handled = []

        # 观测空间 节点数*3属性（cpu mem delay）+链路数*1属性（bandwidth）+节点数*1（sfc入出节点01编码）+vnf需求2*3+sfc带宽
        self.observation_space = spaces.Dict(
            {
                'nodes': spaces.Box(low=0, high=1, shape=(self.num_nodes, 3)),
                'edges': spaces.Box(low=0, high=1, shape=(self.num_edges, 1)),
                'sfc_in_out_nodes': spaces.MultiBinary(self.num_nodes),
                'sfc_request_vnfs': spaces.Box(low=0, high=1, shape=(2, 3)),
                'sfc_bandwidth': spaces.Box(low=0, high=1, shape=(1,))
            }
        )
        # 动作空间 节点数^3
        self.action_space = spaces.MultiDiscrete([len(self.network.nodes), len(self.network.nodes), len(self.network.nodes)])

    def _get_obs(self):
        cpu = []
        mem = []
        delay = []
        for node in self.network.nodes:
            cpu.append(self.network.nodes[node]['resources_cpu_used'] / self.network.nodes[node]['resources_cpu'])
            mem.append(self.network.nodes[node]['resources_mem_used'] / self.network.nodes[node]['resources_mem'])
            delay.append(self.network.nodes[node]['processing_delay'] / (self.network.nodes[node]['processing_delay_base'] * 20))

        bw = [ self.network.edges[edge]['bandwidth_used'] / self.network.edges[edge]['bandwidth'] for edge in self.network.edges]

        sfc_in_out_nodes = [ 0 for _ in range(self.num_nodes)]
        list_of_nodes = list(self.network.nodes)
        sfc_in_out_nodes[list_of_nodes.index(self.sfc_requests[self.sfc_request_mark].nodes['in']['node_in'])] = 1
        sfc_in_out_nodes[list_of_nodes.index(self.sfc_requests[self.sfc_request_mark].nodes['out']['node_out'])] = 1

        # remember to modify the MAGIC NUMBERS 100 500
        sfc_request_vnfs = []
        for vnf in self.sfc_requests[self.sfc_request_mark].nodes:
            if vnf == 'in' or vnf == 'out':
                continue
            tmp = [self.sfc_requests[self.sfc_request_mark].nodes[vnf]['vnf_type'].resources_cpu_demand / 100,
                   self.sfc_requests[self.sfc_request_mark].nodes[vnf]['vnf_type'].resources_mem_demand / 100]
            sfc_request_vnfs.append(tmp)

        sfc_bandwidth = self.sfc_requests[self.sfc_request_mark].bandwidth / 500

        return {
            'nodes': np.array([cpu, mem, delay]),
            'edges': np.array(bw),
            'sfc_in_out_nodes': np.array(sfc_in_out_nodes),
            'sfc_request_vnfs': np.array(sfc_request_vnfs),
            'sfc_bandwidth': sfc_bandwidth
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
        random.shuffle(self.sfc_requests)

        observation = self._get_obs()

        return observation, {}

    def _get_reward(self):
        reward = 0.0
        for sfc in self.sfc_handled:
            reward -= sfc.delay_actual
        return reward

    def step(self, action):
        reward = 0.0
        terminated = False
        # 将动作转换为 target_node_dict
        target_node_dict = {}
        for i in range(len(action)):
            target_node_dict['vnf' + str(i + 1)] = list(self.network.nodes)[action[i]]
        # 部署sfc
        err, msg =  self.network.deploy_sfc_by_vnf(self.sfc_requests[self.sfc_request_mark], target_node_dict, is_delay_limit_enable=False)
        if err is False:
            print(msg)

        self.sfc_handled.append(copy.deepcopy(self.sfc_requests[self.sfc_request_mark]))
        # 更新所有已部署sfc延时
        for sfc in self.sfc_handled:
            sfc.update_delay_simple_model(self.network)
        # 计算reward
        if self.sfc_request_mark == len(self.sfc_requests):
            terminated = True
            reward = self._get_reward()
        else:
            self.sfc_request_mark += 1

        observation = self._get_obs()

        return observation, reward, terminated, {}

