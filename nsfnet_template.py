import random

template = {
    'nodes': ['node1', 'node2', 'node3', 'node4', 'node5', 'node6', 'node7', 'node8', 'node9', 'node10', 'node11', 'node12', 'node13', 'node14'],
    'node_attrs': {},
    'edges': [('node1', 'node2'), ('node1', 'node3'), ('node1', 'node6'),
              ('node2', 'node3'), ('node2', 'node4'),
              ('node3', 'node9'),
              ('node4', 'node5'), ('node4', 'node7'), ('node4', 'node14'),
              ('node5', 'node10'),
              ('node6', 'node7'), ('node6', 'node11'),
              ('node7', 'node8'),
              ('node8', 'node9'),
              ('node9', 'node10'),
              ('node10', 'node12'), ('node10', 'node13'),
              ('node11', 'node12'), ('node11', 'node13'),
              ('node12', 'node14'),
              ('node13', 'node14')],
    'edge_attrs': {}
    }
vnf_type = ['vnf_type_1', 'vnf_type_2', 'vnf_type_3', 'vnf_type_4', 'vnf_type_5', 'vnf_type_6']
vnf_type_template = [
    {'vnf_type_1': {'resources_cpu_demand': 1, 'resources_mem_demand': 1}},
    {'vnf_type_2': {'resources_cpu_demand': 2, 'resources_mem_demand': 4}},
    {'vnf_type_3': {'resources_cpu_demand': 4, 'resources_mem_demand': 2}},
    {'vnf_type_4': {'resources_cpu_demand': 4, 'resources_mem_demand': 4}},
    {'vnf_type_5': {'resources_cpu_demand': 1, 'resources_mem_demand': 4}},
    {'vnf_type_6': {'resources_cpu_demand': 2, 'resources_mem_demand': 2}}
]

sfc = []

def generate_attrs():
    for node in template['nodes']:
        template['node_attrs'][node] = {
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
    for edge in template['edges']:
        template['edge_attrs'][edge] = {
            'bandwidth': 100000,
            'bandwidth_used': 0,
            'transmission_delay': 5,
            'vl_dict': {}
        }

def generate_sfc():
    for i in range(1, 301):
        node_in_out = random.sample(template['nodes'], 2)
        vnf = random.sample(vnf_type, 3)
        bandwidth = random.sample([50, 100, 200, 500], 1)[0]
        delay = random.sample([60, 70, 80, 90, 100], 1)[0]
        sfc.append({
            'sfc' + str(i): {
                'node_in': node_in_out[0],
                'node_out': node_in_out[1],
                'vnf_list': vnf,
                'bandwidth': bandwidth,
                'bandwidth_used': 0,
                'delay_limit': delay,
                'delay_actual': 0
            }
        })

def init():
    generate_attrs()
    generate_sfc()
    return template, vnf_type_template, sfc
