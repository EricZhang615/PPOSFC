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
        self.ksp = {}

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

    def generate_ksp(self, k):
        for i in range(1, len(self.nodes)+1):
            for j in range(1, len(self.nodes)+1):
                paths = nx.shortest_simple_paths(self, source='node'+str(i), target='node'+str(j), weight='transmission_delay')
                path_list = []
                for m, p in enumerate(paths):
                    path_list.append(p)
                    if m == k:
                        break
                self.ksp[('node'+str(i), 'node'+str(j))] = path_list

    def reset(self):
        for node in self.nodes:
            self.nodes[node].update({
                'resources_cpu_used': 0,
                'resources_mem_used': 0,
                'load_cpu': 0.0,
                'load_mem': 0.0,
                'processing_delay': 10,
                'vnf_dict': {},
                'vl_dict': {}
            })
        for edge in self.edges:
            self.edges[edge].update({
                'bandwidth_used': 0,
                'vl_dict': {}
            })

    def update_delay(self):
        '''
        按照动态时延简单模型更新物理节点当前时延
        动态延时简单模型：处理延时和资源占用率相关：
        '''
        for node in self.nodes:
            self.update_node_delay_simple_mode(node)

    def update_node_delay_simple_mode(self, node):
        self.nodes[node]['processing_delay'] = self.calc_node_delay_simple_mode(node)

    def calc_node_delay_simple_mode(self, node, estimate=0.0):
        cpu_ratio = (self.nodes[node]['resources_cpu_used'] + estimate) / self.nodes[node]['resources_cpu']
        if cpu_ratio <= 0.5:
            return self.nodes[node]['processing_delay_base']
        elif cpu_ratio > 0.95:
            return self.nodes[node]['processing_delay_base'] * 20
        else:
            return self.nodes[node]['processing_delay_base'] * (cpu_ratio / (1 - cpu_ratio))


    def check_before_deploy_vnf(self, sfc: SFC, vnf, target_node):
        # 判断vnf target node正确
        assert vnf in sfc.nodes, f'vnf {vnf} not in sfc'
        assert target_node in self.nodes, f'target_node {target_node} not in network'
        # 判断有剩余resources
        cpu_limit = self.nodes[target_node]['resources_cpu']
        cpu_used = self.nodes[target_node]['resources_cpu_used']
        assert cpu_used + sfc.nodes[vnf]['vnf_type'].resources_cpu_demand <= cpu_limit, 'cpu not enough'
        mem_limit = self.nodes[target_node]['resources_mem']
        mem_used = self.nodes[target_node]['resources_mem_used']
        assert mem_used + sfc.nodes[vnf]['vnf_type'].resources_mem_demand <= mem_limit, 'mem not enough'
        # # 返回增加的processing delay
        # return self.nodes[target_node]['processing_delay']
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
        # # 将processing delay加在sfc上
        # sfc.delay_actual += self.nodes[target_node]['processing_delay']

    def undeploy_vnf(self, sfc: SFC, vnf):
        node_deployed = sfc.nodes[vnf]['node_deployed']
        # 去掉processing delay 和 node_deployed
        # sfc.delay_actual -= self.nodes[node_deployed]['processing_delay']
        sfc.nodes[vnf]['node_deployed'] = ''
        # 去掉vnf消耗的resources demand
        self.nodes[node_deployed]['resources_cpu_used'] -= sfc.nodes[vnf]['vnf_type'].resources_cpu_demand
        self.nodes[node_deployed]['resources_mem_used'] -= sfc.nodes[vnf]['vnf_type'].resources_mem_demand
        # 去掉标记的sfc和vnf信息
        if len(self.nodes[node_deployed]['vnf_dict'][sfc.name]) == 1:
            self.nodes[node_deployed]['vnf_dict'].pop(sfc.name)
        else:
            self.nodes[node_deployed]['vnf_dict'][sfc.name].remove(vnf)

    def check_before_deploy_vl(self, sfc: SFC, vl, target) -> int:
        # 确认vl正确
        assert vl in sfc.edges, f'vl {vl} not in sfc'
        # 确认target是str或list
        assert isinstance(target, str) ^ isinstance(target, list), f'target type {type(target)} incorrect'
        delay = 0
        if isinstance(target, str):
            # 内部部署
            assert target in self.nodes, f'target_node {target} not in network'
        else:
            # 链路部署
            for target_edge in target:
                assert target_edge in self.edges, f'target_edge {target_edge} not in network'
                # 判断有剩余带宽
                bandwidth_used = self.edges[target_edge]['bandwidth_used']
                assert bandwidth_used + sfc.bandwidth <= self.edges[target_edge]['bandwidth'], 'bandwidth not enough'
                delay += self.edges[target_edge]['transmission_delay']
        # 返回增加的delay
        return delay

    def deploy_vl(self, sfc: SFC, vl, target) -> None:
        # 内部部署模式
        if isinstance(target, str):
            # 将sfc和vl信息标记在物理节点上
            if sfc.name in self.nodes[target]['vl_dict']:
                self.nodes[target]['vl_dict'][sfc.name].append(vl)
            else:
                self.nodes[target]['vl_dict'][sfc.name] = [vl]
            # 将target node 写入vl上
            sfc.edges[vl]['node_deployed'] = target
        else:
            # 链路部署模式
            for target_edge in target:
                # 将sfc和vl信息标记在物理链路上
                if sfc.name in self.edges[target_edge]['vl_dict']:
                    self.edges[target_edge]['vl_dict'][sfc.name].append(vl)
                else:
                    self.edges[target_edge]['vl_dict'][sfc.name] = [vl]
                # 将target link 写入vl上
                sfc.edges[vl]['edges_deployed'].append(target_edge)
                # 将vl消耗的bandwidth 写入物理链路上
                self.edges[target_edge]['bandwidth_used'] += sfc.bandwidth
                # # 将物理链路的transmission delay 写入sfc上
                # sfc.delay_actual += self.edges[target_edge]['transmission_delay']

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
                self.edges[edge_deployed]['bandwidth_used'] -= sfc.bandwidth
                # sfc.delay_actual -= self.edges[edge_deployed]['transmission_delay']
                # 去掉vl信息
                if len(self.edges[edge_deployed]['vl_dict'][sfc.name]) == 1:
                    self.edges[edge_deployed]['vl_dict'].pop(sfc.name)
                else:
                    self.edges[edge_deployed]['vl_dict'][sfc.name].remove(vl)
            sfc.edges[vl]['edges_deployed'] = []

    def undeploy_sfc(self, sfc) -> (bool, str):
        if not sfc.is_deployed():
            return False, f"undeploy sfc failed -- sfc: {sfc.name} status: {sfc.status}"
        # undeploy vnf
        for vnf in sfc.nodes:
            if vnf != 'in' and vnf != 'out':
                self.undeploy_vnf(sfc, vnf)
        for vl in sfc.edges:
            self.undeploy_vl(sfc, vl)
        # 更新网络延时
        self.update_delay()
        sfc.status_idle()
        sfc.delay_actual = 0
        return True, f"undeploy sfc success -- sfc: {sfc.name}"

    def deploy_sfc_by_sp(self, sfc: SFC, k, is_delay_limit_enable=True, check_delay_only=False) -> (bool, str):
        source = sfc.nodes['in']['node_in']
        target = sfc.nodes['out']['node_out']
        num_remain_vnf = len(list(sfc.nodes)) - 2
        if self.ksp is {}:
            print("k sp empty")
            return False, f"deploy sfc failed -- ksp empty"
        path = copy.deepcopy(self.ksp[(source, target)][k])
        target_node_list = copy.deepcopy(path)

        # 均匀排布vnf位置
        target_node_dict = {}
        vl_deploy_plan = {}
        # 逐项重复列表中的每个元素，直到列表的长度等于vnf数量
        if len(target_node_list) < num_remain_vnf:
            tmp = [item for item in target_node_list for _ in range(num_remain_vnf // len(target_node_list) + 1)]
            target_node_list = tmp[:num_remain_vnf]
        for i in range(1, num_remain_vnf+1):
            target_node_dict['vnf' + str(i)] = target_node_list[i-1]

        # 生成链路部署方案 按照ksp为基础
        for vl in sfc.edges:
            if vl[0] == 'in':
                source = sfc.nodes['in']['node_in']
                target = target_node_dict[vl[1]]
            elif vl[1] == 'out':
                source = target_node_dict[vl[0]]
                target = sfc.nodes['out']['node_out']
            else:
                source = target_node_dict[vl[0]]
                target = target_node_dict[vl[1]]
            if source == target:
                vl_deploy_plan[vl] = source
            else:
                vl_path = []
                index_source = path.index(source)
                index_target = path.index(target)
                if index_source < index_target:
                    vl_path = path[index_source:index_target + 1]
                else:
                    vl_path = path[index_target:index_source + 1]

                vl_deploy_plan[vl] = [(vl_path[i], vl_path[i + 1]) for i in range(len(vl_path) - 1)]

        return self.deploy_sfc_by_vnf(sfc, target_node_dict, vl_deploy_plan=vl_deploy_plan, is_delay_limit_enable=is_delay_limit_enable, check_delay_only=check_delay_only)


    def deploy_sfc_by_vnf(self, sfc: SFC, target_node_dict, vl_deploy_plan=None, is_delay_limit_enable=True, check_delay_only=False) -> (bool, str):
        '''
        按vnf目标节点部署sfc；vnf根据输入目标物理节点部署，vl按节点间最短路径部署
        target_node_dict: {'vnf1': 'node1', 'vnf2': 'node2', ...}
        Parameters
        ----------
        vl_deploy_plan
        check_delay_only
        is_delay_limit_enable
        target_node_dict
        sfc

        Returns
        -------

        '''
        # 检查入参
        assert len(target_node_dict) == sfc.number_of_nodes() - 2, 'target_node_dict length not match sfc number of vnfs'
        # sfc是否已经部署
        if sfc.is_deployed():
            return False, f"deploy sfc failed -- sfc: {sfc.name} status: {sfc.status}"
        # 生成链路部署方案
        # vl_deploy_plan = {}     # {('in', 'vnf1'): 'node1', ('vnf1', 'vnf2'): [('node1', 'node2'), ...], ...}
        if vl_deploy_plan is None:
            vl_deploy_plan = {}
            for vl in sfc.edges:
                if vl[0] == 'in':
                    source = sfc.nodes['in']['node_in']
                    target = target_node_dict[vl[1]]
                elif vl[1] == 'out':
                    source = target_node_dict[vl[0]]
                    target = sfc.nodes['out']['node_out']
                else:
                    source = target_node_dict[vl[0]]
                    target = target_node_dict[vl[1]]
                if source == target:
                    vl_deploy_plan[vl] = source
                else:
                    path = nx.shortest_path(self, source, target, weight='transmission_delay')
                    vl_deploy_plan[vl] = [(path[i], path[i+1]) for i in range(len(path)-1)]

        # 检查vnf部署是否可行
        node_cpu_used_tmp = {}
        if is_delay_limit_enable or check_delay_only:
            for vnf, target_node in target_node_dict.items():
                try:
                    self.check_before_deploy_vnf(sfc, vnf, target_node)
                except AssertionError as e:
                    return False, f"deploy sfc failed -- vnf: {e}"
                if target_node in node_cpu_used_tmp:
                    node_cpu_used_tmp[target_node] += sfc.nodes[vnf]['vnf_type'].resources_cpu_demand
                else:
                    node_cpu_used_tmp[target_node] = sfc.nodes[vnf]['vnf_type'].resources_cpu_demand
        else:
            for vnf, target_node in target_node_dict.items():
                try:
                    self.check_before_deploy_vnf(sfc, vnf, target_node)
                except AssertionError as e:
                    return False, f"deploy sfc failed -- vnf: {e}"

        # 检查vl部署是否可行
        delay = 0
        for vl in vl_deploy_plan:
            target = vl_deploy_plan[vl]
            try:
                delay += self.check_before_deploy_vl(sfc, vl, target)
            except AssertionError as e:
                return False, f"deploy sfc failed -- vl: {e}"

        # 检查delay是否超时
        if is_delay_limit_enable or check_delay_only:
            for vnf, target_node in target_node_dict.items():
                delay += self.calc_node_delay_simple_mode(target_node, estimate=node_cpu_used_tmp[target_node])
            if check_delay_only:
                return delay
            if delay > sfc.delay_limit:
                return False, f"deploy sfc failed -- delay: {delay} > {sfc.delay_limit}"

        # 部署sfc
        for vnf, target_node in target_node_dict.items():
            self.deploy_vnf(sfc, vnf, target_node)
        for vl in vl_deploy_plan:
            target = vl_deploy_plan[vl]
            self.deploy_vl(sfc, vl, target)
        sfc.status_deploy()

        # 更新网络延时
        self.update_delay()

        # 更新sfc延时
        r = sfc.update_delay_simple_model(self)
        if not r:
            print(r)

        return True, f"deploy sfc success: {sfc.name}"