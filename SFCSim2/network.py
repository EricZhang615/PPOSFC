import copy
from typing import Dict, List, Tuple, Union, Any
from sfc import SFC
from vnf import VNFType

import networkx as nx


Nodes = List[str]
NodeAttr = Dict[str, Dict[str, Any]]
Edges = List[Tuple[str, str]]
EdgesAttr = Dict[Tuple[str, str], Dict[str, Any]]

class Network(nx.Graph):

    def __init__(self, template: Dict[str, Union[Nodes, NodeAttr, Edges, EdgesAttr]], vnf_type_dict: Dict[str, VNFType], **attr) -> None:
        super().__init__(**attr)
        self.generate(template)
        self.vnf_type_dict = {}
        self.update_vnf_type(vnf_type_dict)

    def generate(self, template: Dict[str, Union[Nodes, NodeAttr, Edges, EdgesAttr]]) -> None:
        self.add_nodes(template['nodes'], template['node_attrs'])
        self.add_edges(template['edges'], template['edge_attrs'])

    def add_nodes(self, nodes: Nodes, attrs: NodeAttr) -> None:
        self.add_nodes_from(nodes)
        for k, v in attrs.items():
            self.nodes[k].update(v)

    def add_edges(self, edges: Edges, attrs: EdgesAttr) -> None:
        self.add_edges_from(edges)
        for k, v in attrs.items():
            self.edges[k].update(v)

    def update_vnf_type(self, vnf_type_dict: Dict[str, VNFType]) -> None:
        self.vnf_type_dict = copy.deepcopy(vnf_type_dict)


    def check_before_deploy_vnf(self, sfc: SFC, vnf, target_node) -> int:
        # 判断vnf target node正确
        assert vnf in sfc.nodes, 'vnf not in sfc'
        assert target_node in self.nodes, 'target_node not in network'
        # 判断有剩余resources
        cpu_limit = self.nodes[target_node]['resources_cpu']
        cpu_used = self.nodes[target_node]['resources_cpu_used']
        assert cpu_used + sfc.nodes[vnf]['vnf_type'].resources_cpu_demand <= cpu_limit, 'cpu not enough'
        mem_limit = self.nodes[target_node]['resources_mem']
        mem_used = self.nodes[target_node]['resources_mem_used']
        assert mem_used + sfc.nodes[vnf]['vnf_type'].resources_mem_demand <= mem_limit, 'mem not enough'
        # 返回增加的processing delay
        return self.nodes[target_node]['processing_delay']
        pass

    def deploy_vnf(self, sfc: SFC, vnf, target_node) -> None:
        # 将sfc和vnf信息标记在物理节点上
        if sfc.name in self.nodes[target_node]['vnf_dict']:
            self.nodes[target_node]['vnf_dict'][sfc.name].append(vnf)
        else:
            self.nodes[target_node]['vnf_dict'][sfc.name] = [vnf]
        # 将vnf消耗的resources demand加在物理节点上
        self.nodes[target_node]['resources_cpu_used'] += sfc.nodes[vnf]['vnf_type'].resources_cpu_demand
        self.nodes[target_node]['resources_mem_used'] += sfc.nodes[vnf]['vnf_type'].resources_mem_demand
        # 将processing delay加在sfc上
        sfc.nodes[vnf]['node_deployed'] = target_node
        sfc.delay_actual += self.nodes[target_node]['processing_delay']

