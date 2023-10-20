

from SFCSim2.network import Network
from SFCSim2.template1 import template, sfc_template, vnf_type_template
from SFCSim2.vnf import VNFType
from SFCSim2.sfc import SFC

vnf_type_dict = {}
sfc_dict = {}

vnf_type_dict.update({list(vnf_type_info.keys())[0]: VNFType(vnf_type_info) for vnf_type_info in vnf_type_template})

sfc_dict.update({list(sfc_info.keys())[0]: SFC(sfc_info, vnf_type_dict) for sfc_info in sfc_template})


network = Network(template=template)

print(0)