template = {
    'nodes': ['node1', 'node2', 'node3', 'node4', 'node5', 'node6', ],
    'node_attrs': {
        "node1": {
            'resources_cpu': 100,
            'resources_cpu_used': 0,
            'resources_mem': 100,
            'resources_mem_used': 0,
            'load_cpu': 0.0,
            'load_mem': 0.0,
            'processing_delay_base': 10,
            'processing_delay': 10,
            'vnf_dict': {},
            'vl_dict': {}
        },
        "node2": {
            'resources_cpu': 100,
            'resources_cpu_used': 0,
            'resources_mem': 100,
            'resources_mem_used': 0,
            'load_cpu': 0.0,
            'load_mem': 0.0,
            'processing_delay_base': 10,
            'processing_delay': 10,
            'vnf_dict': {},
            'vl_dict': {}
        },
        "node3": {
            'resources_cpu': 100,
            'resources_cpu_used': 0,
            'resources_mem': 100,
            'resources_mem_used': 0,
            'load_cpu': 0.0,
            'load_mem': 0.0,
            'processing_delay_base': 10,
            'processing_delay': 10,
            'vnf_dict': {},
            'vl_dict': {}
        },
        "node4": {
            'resources_cpu': 100,
            'resources_cpu_used': 0,
            'resources_mem': 100,
            'resources_mem_used': 0,
            'load_cpu': 0.0,
            'load_mem': 0.0,
            'processing_delay_base': 10,
            'processing_delay': 10,
            'vnf_dict': {},
            'vl_dict': {}
        },
        "node5": {
            'resources_cpu': 100,
            'resources_cpu_used': 0,
            'resources_mem': 100,
            'resources_mem_used': 0,
            'load_cpu': 0.0,
            'load_mem': 0.0,
            'processing_delay_base': 10,
            'processing_delay': 10,
            'vnf_dict': {},
            'vl_dict': {}
        },
        "node6": {
            'resources_cpu': 100,
            'resources_cpu_used': 0,
            'resources_mem': 100,
            'resources_mem_used': 0,
            'load_cpu': 0.0,
            'load_mem': 0.0,
            'processing_delay_base': 10,
            'processing_delay': 10,
            'vnf_dict': {},
            'vl_dict': {}
        }
    },
    'edges': [('node1', 'node2'), ('node2', 'node3'), ('node3', 'node4'), ('node4', 'node5'), ('node5', 'node6')],
    'edge_attrs': {
        ('node1', 'node2'): {
            'bandwidth': 1000,
            'bandwidth_used': 0,
            'transmission_delay': 10,
            'vl_dict': {}
        },
        ('node2', 'node3'): {
            'bandwidth': 1000,
            'bandwidth_used': 0,
            'transmission_delay': 10,
            'vl_dict': {}
        },
        ('node3', 'node4'): {
            'bandwidth': 1000,
            'bandwidth_used': 0,
            'transmission_delay': 10,
            'vl_dict': {}
        },
        ('node4', 'node5'): {
            'bandwidth': 1000,
            'bandwidth_used': 0,
            'transmission_delay': 10,
            'vl_dict': {}
        },
        ('node4', 'node5'): {
            'bandwidth': 1000,
            'bandwidth_used': 0,
            'transmission_delay': 10,
            'vl_dict': {}
        },
        ('node5', 'node6'): {
            'bandwidth': 1000,
            'bandwidth_used': 0,
            'transmission_delay': 10,
            'vl_dict': {}
        }
    }
}

sfc_template = [
    {'sfc1': {'node_in': 'node1', 'node_out': 'node3', 'vnf_list': ['vnf_type_1'], 'bandwidth': 100, 'bandwidth_used': 0, 'delay_limit': 50, 'delay_actual': 0}},
    {'sfc2': {'node_in': 'node2', 'node_out': 'node4', 'vnf_list': ['vnf_type_2'], 'bandwidth': 100, 'bandwidth_used': 0, 'delay_limit': 55, 'delay_actual': 0}},
    {'sfc3': {'node_in': 'node3', 'node_out': 'node5', 'vnf_list': ['vnf_type_3'], 'bandwidth': 100, 'bandwidth_used': 0, 'delay_limit': 20, 'delay_actual': 0}}
]

vnf_type_template = [
    {'vnf_type_1': {'resources_cpu_demand': 60, 'resources_mem_demand': 2}},
    {'vnf_type_2': {'resources_cpu_demand': 2, 'resources_mem_demand': 4}},
    {'vnf_type_3': {'resources_cpu_demand': 4, 'resources_mem_demand': 4}}
]