import json
import scipy.io
from scipy.constants import c,e
import matplotlib.pyplot as plt
import numpy as np
# from cmcrameri import cm
from rich.progress import Progress
import pendulum
import glob

from ECIX_tools import replaceline as rl
from ECIX_tools import filemanager as exfm

from PyECLOUD.buildup_simulation import BuildupSimulation
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--ecloud", nargs="?", type=str, default="ecloud.q3r1.ir1.0")
args = parser.parse_args()

ecloud = args.ecloud

mod_factor = 1
with open("eclouds_LHCIT_slices.json","r") as fid:
    eclouds_info = json.load(fid)

out_pinch = f"Pinch.h5"

mp_state_files = glob.glob("MP_state*")
mp_states = []
for name in mp_state_files:
    mp_system = scipy.io.loadmat(name)
    mp_system['nel_mp'] = mp_system['nel_mp']/len(mp_state_files)
    mp_states.append(mp_system)

t_min = 2.5e-9 - 0.4 / c
t_max = 2.5e-9 + 0.4 / c
t_end_sim = t_max + 0.02 / c
total_N_particles = sum([mp_system["N_mp"][0][0] for mp_system in mp_states])
total_N_particles *= 2 #put more particles to max allowed
total_N_particles += 10000 #put more particles to max allowed

nsigma = 7.5
xc = eclouds_info[ecloud]["x_b1"]
yc = eclouds_info[ecloud]["y_b1"]
sigx = eclouds_info[ecloud]["sigx_b1"]
sigy = eclouds_info[ecloud]["sigy_b1"]

betx = eclouds_info[ecloud]["betx_b1"]
bety = eclouds_info[ecloud]["bety_b1"]

xmax = xc + nsigma*sigx
xmin = xc - nsigma*sigx
ymax = yc + nsigma*sigy
ymin = yc - nsigma*sigy

print(f"x_max = {xmax:.3e} m")
print(f"x_min = {xmin:.3e} m")
print(f"y_max = {ymax:.3e} m")
print(f"y_min = {ymin:.3e} m")


PyPICmode = 'ShortleyWeller_WithTelescopicGrids'
target_grid = {'x_min_target' : xmin, 'x_max_target' : xmax,
               'y_min_target' : ymin, 'y_max_target' : ymax,
               'Dh_target' : 2.e-5}
f_telescope = 0.5
N_nodes_discard = 10
N_min_Dh_main = 50

sim = BuildupSimulation(extract_sey=False, N_mp_max=total_N_particles, PyPICmode=PyPICmode,
                        target_grid=target_grid, f_telescope=f_telescope,
                        N_nodes_discard=N_nodes_discard, N_min_Dh_main=N_min_Dh_main,
                        init_unif_edens_flag=0)


sim.cloud_list[0].MP_e.init_from_dict(mp_states[0])
sim.cloud_list[0].MP_e.nel_mp_ref *= len(mp_states)
prev_mp = sim.cloud_list[0].MP_e.N_mp
for mp_system in mp_states[1:]:
    sim.cloud_list[0].MP_e.add_from_file(mp_system)
    now_mp = sim.cloud_list[0].MP_e.N_mp
    print(now_mp, mp_system["N_mp"][0][0], now_mp - prev_mp)
    prev_mp = now_mp

N_mp = sim.cloud_list[0].MP_e.N_mp
max_nel_mp = np.max(sim.cloud_list[0].MP_e.nel_mp[:N_mp])
sim.cloud_list[0].MP_e.nel_mp_split = 3*(max_nel_mp)

print(sim.cloud_list[0].MP_e.nel_mp_split)

print("Start timestep iter")

## simulation
def time_step(sim, t_end_sim=None):
    beamtim = sim.beamtim
    if t_end_sim is not None and beamtim.tt_curr is not None:
        if beamtim.tt_curr >= t_end_sim:
            print("Reached user defined t_end_sim --> Ending simulation")
            return 1
 
    beamtim.next_time_step()
 
    if sim.flag_presence_sec_beams:
        for sec_beam in sim.sec_beams_list:
            sec_beam.next_time_step()
 
    sim.sim_time_step(force_reinterp_fields_at_substeps=True, skip_MP_cleaning=True, skip_MP_regen=True)
 
    if beamtim.flag_new_bunch_pass:
        print(
            "**** Done pass_numb = %d/%d\n"
            % (beamtim.pass_numb, beamtim.N_pass_tot)
        )
    return 0


exfm.dict_to_h5({"produced" : pendulum.now().to_datetime_string()}, out_pinch, group='date', readwrite_opts='w')

xg = sim.spacech_ele.xg
yg = sim.spacech_ele.yg
zg = []

ii = 0
jj = 0

with Progress() as progress:
    task = progress.add_task("PyECLOUD tracking", total=t_end_sim)

    while not time_step(sim, t_end_sim=t_end_sim):
        print(sim.cloud_list[0].MP_e.N_mp/total_N_particles)
        ii += 1
        tt = sim.beamtim.tt_curr
        progress.update(task, completed=tt)
        if tt > t_min and tt < t_max:
            if ii%mod_factor == 0.:
                print(jj, ii, -c*(tt-2.5e-9))
                zg.append(-c*(tt-2.5e-9))
                exfm.dict_to_h5({'phi' : sim.spacech_ele.phi, 'rho' : sim.spacech_ele.rho}, out_pinch, group='slices/slice%d'%jj, readwrite_opts='a')
                jj += 1

grid_dict = {"xg" : np.array(xg),
             "yg" : np.array(yg),
             "zg" : np.array(zg),
             "xc" : xc,
             "yc" : yc,
             "sigx" : sigx,
             "sigy" : sigy,
}
exfm.dict_to_h5(grid_dict, out_pinch, group='grid', readwrite_opts='a')
