import yaml
import sys

class QuectelParser:
    yaml_data = None


    def __init__(self, p_cfg=""):
        if len(p_cfg) == 0:
            exit("\033[31mYou must point .cfg file\033[0m")

        try:
            with open(p_cfg, 'r') as fp:
                self.yaml_data = yaml.safe_load(fp)
        except FileNotFoundError:
                sys.exit("\033[31mNo such file or directory {}\033[0m".format(p_cfg))
