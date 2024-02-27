import json
from pathlib import Path
import numpy as np
from ECIX_tools import replaceline as rl
from rich.pretty import pprint
import subprocess
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--ecloud', nargs='?', default='ecloud.q3r1.ir1.0', type=str)
parser.add_argument('--sey_max', nargs='?', default=1.35, type=float)
parser.add_argument('--intensity', nargs='?', default=1.2, type=float)
parser.add_argument('--bunch_length', nargs='?', default=0.09, type=float)
args = parser.parse_args()

del_max = args.sey_max
fact_beam = args.intensity * 1e11
bunchlen = args.bunch_length
Dt = 5e-12
energy_eV = 6800e9

with open("eclouds_LHCIT_slices.json","r") as fid:
    eclouds_info = json.load(fid)

ecloud = eclouds_info[args.ecloud]

pprint(ecloud)

beamscreen = ecloud["beamscreen"]
filename_chm = f"LHC_{beamscreen.upper()}.mat"

# Download chamber
if Path(filename_chm).exists():
    Path(filename_chm).unlink()
github_chambers = f"https://raw.githubusercontent.com/ecloud-cern/ECIX_LHC_top_energy/main/Slice_triplet/Beam_chambers/"
subprocess.run(["wget", "-c", f"{github_chambers}{filename_chm}" ])


rl.replaceline_and_save(fname = "secondary_emission_parameters.input",
                        findln = "del_max =", newline = f"del_max = {del_max:f}\n")

rl.replaceline_and_save(fname = "beam1.beam",
                        findln = "energy_eV =", newline = f"energy_eV = {energy_eV:e}\n")
rl.replaceline_and_save(fname = "beam2.beam",
                        findln = "energy_eV =", newline = f"energy_eV = {energy_eV:e}\n")

rl.replaceline_and_save(fname = "beam1.beam",
                        findln = "fact_beam =", newline = f"fact_beam = {fact_beam:e}\n")
rl.replaceline_and_save(fname = 'beam2.beam',
                        findln = "fact_beam =", newline = f"fact_beam = {fact_beam:e}\n")

rl.replaceline_and_save(fname = "machine_parameters.input",
                        findln = "filename_chm =", newline = f"filename_chm = '{filename_chm}'\n")

Bgrad = ecloud["Bgrad"]
rl.replaceline_and_save(fname = "machine_parameters.input",
                        findln = "B_multip =", newline = f"B_multip = [0., {Bgrad:e}]\n")
rl.replaceline_and_save(fname = "machine_parameters.input",
                        findln = "B_skew =", newline = f"B_skew = [0., 0.]\n")

x_b1 = ecloud["x_b1"]
y_b1 = ecloud["y_b1"]
sigx_b1 = ecloud["sigx_b1"]
sigy_b1 = ecloud["sigy_b1"]
rl.replaceline_and_save(fname = "beam1.beam",
                        findln = "x_beam_pos =", newline = f"x_beam_pos = {x_b1:e}\n")
rl.replaceline_and_save(fname = "beam1.beam",
                        findln = "y_beam_pos =", newline = f"y_beam_pos = {y_b1:e}\n")
rl.replaceline_and_save(fname = "beam1.beam",
                        findln = "t_offs =", newline = "t_offs = 2.5e-9\n")
rl.replaceline_and_save(fname = "beam1.beam",
                        findln = "sigmax =", newline = f"sigmax = {sigx_b1:e}\n")
rl.replaceline_and_save(fname = "beam1.beam",
                        findln = "sigmay =", newline = f"sigmay = {sigy_b1:e}\n")
rl.replaceline_and_save(fname = "beam1.beam",
                        findln = "sigmaz =", newline = f"sigmaz = {bunchlen:e}\n")

x_b2 = ecloud["x_b2"]
y_b2 = ecloud["y_b2"]
sigx_b2 = ecloud["sigx_b2"]
sigy_b2 = ecloud["sigy_b2"]
t_offset_s = ecloud["t_offset_s"]
rl.replaceline_and_save(fname = "beam2.beam",
                        findln = "x_beam_pos =", newline = f"x_beam_pos = {x_b2:e}\n")
rl.replaceline_and_save(fname = "beam2.beam",
                        findln = "y_beam_pos =", newline = f"y_beam_pos = {y_b2:e}\n")
rl.replaceline_and_save(fname = "beam2.beam",
                        findln = "t_offs =", newline = f"t_offs = 2.5e-9 + ({t_offset_s:e})\n")
rl.replaceline_and_save(fname = "beam2.beam",
                        findln = "sigmax =", newline = f"sigmax = {sigx_b2:e}\n")
rl.replaceline_and_save(fname = "beam2.beam",
                        findln = "sigmay =", newline = f"sigmay = {sigy_b2:e}\n")
rl.replaceline_and_save(fname = "beam2.beam",
                        findln = "sigmaz =", newline = f"sigmaz = {bunchlen:e}\n")

edens_probes =f"el_density_probes = [{{'x' : {x_b1:e}, 'y': {y_b1:e}, 'r_obs': 1e-3}},{{'x' : {x_b2:e}, 'y': {y_b2:2}, 'r_obs': 1e-3}}]\n"
rl.replaceline_and_save(fname = "simulation_parameters.input",
                        findln = "el_density_probes =", newline = edens_probes)