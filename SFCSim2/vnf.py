from typing import Dict, List, Tuple, Union, Any

class VNFType:

    def __init__(self, vnf_type_info: Dict[str, Dict[str, Any]]):
        self.name = list(vnf_type_info.keys())[0]
        self.resources_cpu_demand = vnf_type_info[self.name]['resources_cpu_demand']
        self.resources_mem_demand = vnf_type_info[self.name]['resources_mem_demand']
        pass
