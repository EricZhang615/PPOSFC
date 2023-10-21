from typing import Dict, List, Tuple, Union, Any

import networkx as nx

class SFC(nx.DiGraph):

    def __init__(self, sfc_info, vnf_type_dict, **attr):
        super().__init__(**attr)
        self.name = ''
        self.bandwidth = 0
        self.bandwidth_used = 0
        self.delay_limit = 0
        self.delay_actual = 0
        self.generate(sfc_info, vnf_type_dict)

    def generate(self, sfc_info: Dict[str, Dict[str, Any]], vnf_type_dict) -> None:
        self.name = list(sfc_info.keys())[0]

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