import gymnasium as gym
import torch as th
from torch import nn
import numpy as np

from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

class TransformerExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space: gym.spaces.Dict):
        # We do not know features-dim here before going over all the items,
        # so put something dummy for now. PyTorch requires calling
        # nn.Module.__init__ before adding modules
        super().__init__(observation_space, features_dim=1)

        total_concat_size = 0
        self.num_nodes = observation_space.spaces["nodes_cpu"].shape[0]
        self.num_nodes_attrs = 0

        # We need to know size of the output of this extractor,
        # so go over all the spaces and compute output feature sizes
        for key, subspace in observation_space.spaces.items():
            if key.startswith('nodes_'):
                self.num_nodes_attrs += 1
            elif key != 'position_encoder':
                total_concat_size += subspace.shape[0]

        total_concat_size += self.num_nodes_attrs * self.num_nodes

        encoder_layer = nn.TransformerEncoderLayer(d_model=self.num_nodes_attrs, nhead=1, dim_feedforward=256, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=2)

        # Update the features dim manually
        self._features_dim = total_concat_size

    def forward(self, observations) -> th.Tensor:
        encoded_tensor_list = []
        src = th.cat([observations['nodes_cpu'].unsqueeze(2), observations['nodes_mem'].unsqueeze(2), observations['nodes_delay'].unsqueeze(2)], dim=2)
        sfc_in_out_nodes = observations['sfc_in_out_nodes']
        sfc_request_vnfs = observations['sfc_request_vnfs']
        pe = observations['position_encoder']
        src_pe = src + pe

        out = self.transformer(src_pe)

        encoded_tensor_list += [out.view(out.size(0), -1), sfc_in_out_nodes, sfc_request_vnfs]

        # Return a (B, self._features_dim) PyTorch tensor, where B is batch dimension.
        return th.cat(encoded_tensor_list, dim=1)