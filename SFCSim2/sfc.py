from typing import Dict, List, Tuple, Union, Any

import networkx as nx

class SFC(nx.DiGraph):

    def __init__(self, sfc_info, vnf_type_dict, **attr):
        super().__init__(**attr)
        self.name = ''
        self.status = 'idle'    # idle or deployed
        self.bandwidth = 0
        self.bandwidth_used = 0
        self.delay_limit = 0
        self.delay_actual = 0
        self.generate(sfc_info, vnf_type_dict)

    def generate(self, sfc_info: Dict[str, Dict[str, Any]], vnf_type_dict) -> None:
        self.name = list(sfc_info.keys())[0]
        self.status = 'idle'

        num = 0

        for k, v in sfc_info[self.name].items():
            if k == 'node_in':
                self.add_node('in', node_in=v)
            elif k == 'node_out':
                self.add_node('out', node_out=v)
            elif k == 'vnf_list':
                num = len(v)
                for i in range(num):
                    self.add_node('vnf' + str(i+1), vnf_type=vnf_type_dict[v[i]], node_deployed='')
            elif k == 'bandwidth':
                self.bandwidth = v
            elif k == 'bandwidth_used':
                self.bandwidth_used = v
            elif k == 'delay_limit':
                self.delay_limit = v
            elif k == 'delay_actual':
                self.delay_actual = v
            else:
                pass

        self.add_edge('in', 'vnf1', node_deployed='', edges_deployed=[])
        for i in range(1, num):
            self.add_edge('vnf' + str(i), 'vnf' + str(i+1), node_deployed='', edges_deployed=[])
        self.add_edge('vnf' + str(num), 'out', node_deployed='', edges_deployed=[])

    def is_deployed(self) -> bool:
        return self.status == 'deployed'

    def status_deploy(self):
        self.status = 'deployed'

    def status_idle(self):
        self.status = 'idle'

    def update_delay_simple_model(self, network) -> (bool, str):
        '''
        按照动态时延简单模型更新sfc当前时延
        动态延时简单模型：处理延时和资源占用率相关：
        Returns
        -------

        '''
        if not self.is_deployed():
            return False, f"update delay failed -- sfc: {self.name} status: {self.status}"
        delay_calc = 0
        for vnf in self.nodes:
            if vnf == 'in' or vnf == 'out':
                continue
            delay_calc += network.nodes[self.nodes[vnf]['node_deployed']]['processing_delay']
        for vl in self.edges:
            if not self.edges[vl]['edges_deployed']:
                continue
            for edge in self.edges[vl]['edges_deployed']:
                delay_calc += network.edges[edge]['transmission_delay']
        self.delay_actual = delay_calc
        return True, f"update delay success -- sfc: {self.name} delay: {self.delay_actual}"