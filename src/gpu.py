from pathlib import Path
import re
import os
import fire
from jlclient import jarvisclient
from jlclient.jarvisclient import *

def _jl_parse_ssh_str(ssh_str, pat=re.compile(r"ssh -p *(\d+) root@(.*)")):
    m = pat.search(ssh_str)
    if not m:
        raise ValueError(f"Invalid ssh string: {ssh_str}")
    return m.group(2), int(m.group(1))

def _jl_print_inst(inst, idx="", show_conn_info=True):
    addr = ', '.join(filter(lambda x: x, [f'{idx}', inst.name]))
    print(f"{addr}:  {inst.gpu_type} ({inst.num_gpus}) - {inst.status}")
    if show_conn_info:
        print(f"\t# {inst.url}")
        print(f"\t# {_jl_parse_ssh_str(inst.ssh_str)}")

def make_ssh_config(inst, idx):
    name = inst.name or f'jl-{idx}'
    host, port = _jl_parse_ssh_str(inst.ssh_str)
    return f"""
    Host {name}
        Port {port}
        HostKeyAlias {name}
        ForwardAgent yes
        Hostname {host}
        User root
    """

class JarvisClient():
    def __init__(self):
        jarvisclient.token = os.environ['JARVIS_TOKEN']
        jarvisclient.user_id = os.environ['JARVIS_USER_ID']

    def _instances(self):
        ids = {str(idx): i for idx, i in enumerate(User.get_instances())}
        names = {inst.name: inst for inst in ids.values()}
        return ids, names

    def list(self):
        ids, _ = self._instances()       
        for key, inst in ids.items():
            _jl_print_inst(inst, key)

    def add_ssh_entries(self, instances = None):
        p = Path.home() / ".ssh" / "config.d" 
        p.mkdir(parents=True, exist_ok=True)
        with (p/'jarvis.config').open('w') as f:
            for key, inst in (instances or self._instances()[0]).items():
                f.write(make_ssh_config(inst, key))

    def resume(self, idx=0):
        ids, names = self._instances()       
        instance = {**ids, **names}[str(idx)]
        instance.resume()
        _jl_print_inst(instance)
        self.add_ssh_entries(ids)

    def pause(self, idx=0):
        ids, names = self._instances()       
        instance = {**ids, **names}[str(idx)]
        instance.pause()
        _jl_print_inst(instance)
        self.add_ssh_entries(ids)

class DataCrunch(): #TODO
    def add_ssh_entries(self, instances):
        return """
        Host dl7
            HostKeyAlias dl8887
            ForwardAgent yes
            Hostname 65.108.32.132
            User user

        Host dl6
            HostKeyAlias dl8886
            ForwardAgent yes
            Hostname 65.108.32.138
            User user

        Host dl5
            HostKeyAlias dl5
            ForwardAgent yes
            Hostname 65.108.32.182
            User user
        """    

if __name__ == '__main__':
    fire.Fire({'jl': JarvisClient()})