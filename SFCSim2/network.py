import copy
from typing import Dict, List, Tuple, Union, Any
from SFCSim2.sfc import SFC
from SFCSim2.vnf import VNFType

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
        # 将target node 写入vnf上
        sfc.nodes[vnf]['node_deployed'] = target_node
        # 将processing delay加在sfc上
        sfc.delay_actual += self.nodes[target_node]['processing_delay']

    def undeploy_vnf(self, sfc: SFC, vnf):
        node_deployed = sfc.nodes[vnf]['node_deployed']
        # 去掉processing delay 和 node_deployed
        sfc.delay_actual -= self.nodes[node_deployed]['processing_delay']
        sfc.nodes[vnf]['node_deployed'] = ''
        # 去掉vnf消耗的resources demand
        self.nodes[node_deployed]['resources_cpu_used'] -= sfc.nodes[vnf]['vnf_type'].resources_cpu_demand
        self.nodes[node_deployed]['resources_mem_used'] -= sfc.nodes[vnf]['vnf_type'].resources_mem_demand
        # 去掉标记的sfc和vnf信息
        if len(self.nodes[node_deployed]['vnf_dict'][sfc.name]) == 1:
            self.nodes[node_deployed]['vnf_dict'].pop(sfc.name)
        else:
            self.nodes[node_deployed]['vnf_dict'][sfc.name].remove(vnf)

    def check_before_deploy_vl(self, sfc: SFC, vl, target_node=None, target_edge_list=None) -> int:
        # 确认vl正确
        assert vl in sfc.edges, 'vl not in sfc'
        # 确认target_node 和 target_edge_list有且仅有一个不为空
        assert (target_node is not None) ^ (target_edge_list is not None), 'target_node or/and target_edge_list incorrect'
        delay = 0
        if target_node is not None:
            # 内部部署
            assert target_node in self.nodes, 'target_node not in network'
        else:
            # 链路部署
            for target_edge in target_edge_list:
                assert target_edge in self.edges, 'target_edge not in network'
                # 判断有剩余带宽
                bandwidth_used = self.edges[target_edge]['bandwidth_used']
                assert bandwidth_used + sfc.edges[vl]['bandwidth'] <= self.edges[target_edge]['bandwidth'], 'bandwidth not enough'
                delay += self.edges[target_edge]['transmission_delay']
        # 返回增加的delay
        return delay

    def deploy_vl(self, sfc: SFC, vl, target_node=None, target_edge_list=None) -> None:
        # 内部部署模式
        if target_node is not None:
            # 将sfc和vl信息标记在物理节点上
            if sfc.name in self.nodes[target_node]['vl_dict']:
                self.nodes[target_node]['vl_dict'][sfc.name].append(vl)
            else:
                self.nodes[target_node]['vl_dict'][sfc.name] = [vl]
            # 将target node 写入vl上
            sfc.edges[vl]['node_deployed'] = target_node
        else:
            # 链路部署模式
            for target_edge in target_edge_list:
                # 将sfc和vl信息标记在物理链路上
                if sfc.name in self.edges[target_edge]['vl_dict']:
                    self.edges[target_edge]['vl_dict'][sfc.name].append(vl)
                else:
                    self.edges[target_edge]['vl_dict'][sfc.name] = [vl]
                # 将target link 写入vl上
                sfc.edges[vl]['edges_deployed'].append(target_edge)
                # 将vl消耗的bandwidth 写入物理链路上
                self.edges[target_edge]['bandwidth_used'] += sfc.edges[vl]['bandwidth']
                # 将物理链路的transmission delay 写入sfc上
                sfc.delay_actual += self.edges[target_edge]['transmission_delay']

    def undeploy_vl(self, sfc: SFC, vl):
        if sfc.edges[vl]['node_deployed'] != '':
            node_deployed = sfc.edges[vl]['node_deployed']
            # 去掉vl的target node
            sfc.edges[vl]['node_deployed'] = ''
            # 去掉物理节点上的sfc和vl信息
            if len(self.nodes[node_deployed]['vl_dict'][sfc.name]) == 1:
                self.nodes[node_deployed]['vl_dict'].pop(sfc.name)
            else:
                self.nodes[node_deployed]['vl_dict'][sfc.name].remove(vl)
        else:
            for edge_deployed in sfc.edges[vl]['edges_deployed']:
                self.edges[edge_deployed]['bandwidth_used'] -= sfc.edges[vl]['bandwidth']
                sfc.delay_actual -= self.edges[edge_deployed]['transmission_delay']
                # 去掉vl信息
                if len(self.edges[edge_deployed]['vl_dict'][sfc.name]) == 1:
                    self.edges[edge_deployed]['vl_dict'].pop(sfc.name)
                else:
                    self.edges[edge_deployed]['vl_dict'][sfc.name].remove(vl)
            sfc.edges[vl]['edges_deployed'] = []