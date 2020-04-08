import yaml
import sys

class QuectelParser:
    yaml_data = None
    QP_BL = None
    QP_ROM = None
    QP_APP = None
    QP_NVDM = None
    QP_RT_NVDM = None

    def __init__(self, p_cfg=""):
        if len(p_cfg) == 0:
            exit("\033[31mYou must point .cfg file\033[0m")

        try:
            with open(p_cfg, 'r') as fp:
                self.yaml_data = yaml.safe_load(fp)
        except FileNotFoundError:
                sys.exit("\033[31mNo such file or directory {}\033[0m".format(p_cfg))

    def export_data(self):
        rom_list = self.yaml_data["main_region"]["rom_list"]
        nvdm_list = self.yaml_data["nvdm_region"]["rom_list"]
        nvdm_rt_list = self.yaml_data["nvdm_retained_region"]["rom_list"]

        return rom_list, nvdm_list, nvdm_rt_list

    def parse_data(self):
        rom_list, nvdm_list, nvdm_rt_list = self.export_data()

        for i in range(len(rom_list)):
            if "Boot" in rom_list[i]["rom"]["name"]:
                self.QP_BL = rom_list[i]["rom"]
            if "ROM" in rom_list[i]["rom"]["name"]:
                self.QP_ROM = rom_list[i]["rom"]
            if "APP" in rom_list[i]["rom"]["name"]:
                self.QP_APP = rom_list[i]["rom"]

        for i in range(len(nvdm_list)):
            if "NVDM" in nvdm_list[i]["rom"]:
                self.QP_NVDM = nvdm_list[i]["rom"]

        for i in range(len(nvdm_rt_list)):
                self.QP_RT_NVDM = nvdm_rt_list[i]["rom"]

    def getData(self, req_field=None):
        self.parse_data()

        if req_field == "ROM":
            return self.QP_ROM
        elif req_field == "BOOTLOADER":
            return self.QP_BL
        elif req_field == "APP":
            return self.QP_APP
        elif req_field == "NVDM":
            return self.QP_NVDM
        elif req_field == "NVDM_RETAINED":
            return self.QP_RT_NVDM
        else:
            return -1
