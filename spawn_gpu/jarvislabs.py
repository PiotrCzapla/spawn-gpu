# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/00_jarvislabs.ipynb.

# %% auto 0
__all__ = ['JarvisClient']

# %% ../nbs/00_jarvislabs.ipynb 4
import re
import os
from pathlib import Path

from fastcore.script import *
from fastcore.basics import *
from fastcore.imports import *

# %% ../nbs/00_jarvislabs.ipynb 5
def _jl_parse_ssh_str(ssh_str, pat=re.compile(r"ssh -p *(\d+) root@(.*)")):
    m = pat.search(ssh_str)
    if not m:
        raise ValueError(f"Unrecognised jarvis ssh string: {ssh_str}")
    return m.group(2), int(m.group(1))

# %% ../nbs/00_jarvislabs.ipynb 7
def _jl_print_inst(inst, idx="", show_conn_info=True):
    addr = ', '.join(filter(lambda x: x, [f'{idx}', inst.name]))
    print(f"{addr}:  {inst.gpu_type} ({inst.num_gpus}) - {inst.status}")
    if show_conn_info:
        print(f"\t# {inst.url}")
        print(f"\t# {_jl_parse_ssh_str(inst.ssh_str) if inst.ssh_str else 'No SSH info, did you provide ssh key?'}")

# %% ../nbs/00_jarvislabs.ipynb 9
def _jl_make_ssh_config(inst, idx):
    name = inst.name or f'jl-{idx}'
    if not inst.ssh_str:
        return """# no ssh info available"""
    host, port = _jl_parse_ssh_str(inst.ssh_str)
    return f"""
    Host {name}
        Port {port}
        HostKeyAlias {name}
        ForwardAgent yes
        Hostname {host}
        User root
    """

# %% ../nbs/00_jarvislabs.ipynb 11
class JarvisClient():
    def __init__(self, ssh_d=None):
        self.ssh_d = ssh_d or Path.home()/'.ssh'
        self.ssh_config = self.ssh_d/'config'

    def _instances(self):
        from jlclient import jarvisclient as api
        api.token = os.environ['JARVIS_TOKEN']
        api.user_id = os.environ['JARVIS_USER_ID']
        try:
            ids = {str(idx): i for idx, i in enumerate(api.User.get_instances())}
        except AttributeError as e:
            if "'str' object has no attribute 'items'" in str(e):
                print('Api is not listing your instances correctly, check your token or contact jarvislabs support')
                return {},{}
        names = {inst.name: inst for inst in ids.values()}
        return ids, names


# %% ../nbs/00_jarvislabs.ipynb 16
@patch
def list(self:JarvisClient):
    ids, _ = self._instances()       
    for key, inst in ids.items():
        _jl_print_inst(inst, key)


# %% ../nbs/00_jarvislabs.ipynb 18
@patch
def _add_config_d(self: JarvisClient):
    line = 'Include ~/.ssh/config.d/*'
    if not self.ssh_config.exists():
        print(f'Creating {self.ssh_config} for you')
        self.ssh_d.mkdir(exist_ok=True)
        lines = []
    else:
        with self.ssh_config.open('rt') as f:
            lines = f.readlines()
    for l in lines:
        if '~/.ssh/config.d/' in l.strip():
            break
    else:
        if lines:
            print("Adding the following required include to your ~/.ssh/config:")
            print(line)
        with self.ssh_config.open('wt') as f:
            f.writelines([line, '\n', *lines])


# %% ../nbs/00_jarvislabs.ipynb 22
@patch
def setup(self: JarvisClient, instances = None):
    p = self.ssh_d / "config.d" 
    p.mkdir(parents=True, exist_ok=True)
    with (p/'jarvis.config').open('w') as f:
        for key, inst in (instances or self._instances()[0]).items():
            f.write(_jl_make_ssh_config(inst, key))


# %% ../nbs/00_jarvislabs.ipynb 24
@patch
def resume(self: JarvisClient, idx=0):
    ids, names = self._instances()       
    instance = {**ids, **names}[str(idx)]
    instance.resume()
    _jl_print_inst(instance)
    self.setup(ids)


# %% ../nbs/00_jarvislabs.ipynb 26
@patch
def pause(self: JarvisClient, idx=0):
    ids, names = self._instances()       
    instance = {**ids, **names}[str(idx)]
    instance.pause()
    _jl_print_inst(instance)
    self.setup(ids)

