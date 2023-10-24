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

def generate_node_attrs():
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