import numpy as np
import json
import h5py
import argparse
import pendulum
from rich.progress import track
from xaux import ProtectFile
import PyECLOUD.int_field_for as iff

parser = argparse.ArgumentParser()
parser.add_argument("--ecloud", nargs="?", type=str, default="ecloud.q3r1.ir1.0")
parser.add_argument("--sey_max", nargs="?", type=str, default="1.35")
parser.add_argument("--intensity", nargs="?", type=str, default="1.20")
parser.add_argument("--bunch_length", nargs="?", type=str, default="0.09")
parser.add_argument("--path", nargs="?", type=str, default='/temp/')
parser.add_argument("--eos_url", nargs="?", type=str, default='root://eosproject.cern.ch/')
args = parser.parse_args()


ecloud_name = args.ecloud
sey_max = args.sey_max
intensity = args.intensity
bunch_length = args.bunch_length

ecloud_split = ecloud_name.split('.')
ecloud_split[1] = f'it{ecloud_split[1][-2:]}'
ecloud_split[3] = '0'

triplet_name = '.'.join(ecloud_split)

triplet_file = f'LHCIT_{ecloud_split[1]}_sey{sey_max}_intensity{intensity}_blen{bunch_length}.h5'

triplet_path = args.path + triplet_file



ecloud_slices_info = json.load(open("eclouds_LHCIT_slices.json","r"))
info = ecloud_slices_info[ecloud_name]
ecloud_triplet_info = json.load(open("eclouds_LHCIT_triplets.json","r"))
triplet = ecloud_triplet_info[triplet_name]

reduce = 0.95

mag = 1e5
dh = 2./mag
nsigma=7.5
# Nd = 10 #N_discard


betx_target = triplet['betx_b1']
bety_target = triplet['bety_b1']
xco_target = triplet['x_b1']
yco_target = triplet['y_b1']
sigx_target = triplet['sigx_b1']
sigy_target = triplet['sigy_b1']

xmax = xco_target + nsigma*sigx_target
xmin = xco_target - nsigma*sigx_target
ymax = yco_target + nsigma*sigy_target
ymin = yco_target - nsigma*sigy_target

xmin = int(xmin*mag)/mag
ymin = int(ymin*mag)/mag
xmax = int(xmax*mag)/mag
ymax = int(ymax*mag)/mag

new_Nx = int(np.round((xmax - xmin)/dh)) + 1
new_Ny = int(np.round((ymax - ymin)/dh)) + 1

new_xg = np.linspace(xmin, xmax, new_Nx)
new_yg = np.linspace(ymin, ymax, new_Ny)

# we need to initialize all slices
# open Triplet
print(triplet_path)
with ProtectFile(triplet_path, 'r+b', backup=False, wait=10, eos_url=args.eos_url) as pf:
    with h5py.File(pf, "a") as Triplet:
        with h5py.File('Pinch.h5', 'r') as pinch:
            new_zg = pinch['grid/zg'][()]
            Nz = len(new_zg)

            if 'fresh' in Triplet.keys():
                print('Initializing.')
                date_group = Triplet.create_group('date')
                date_group['produced'] = pendulum.now().to_datetime_string()

                grid_group = Triplet.create_group('grid')
                grid = {'xg' : new_xg,
                        'yg' : new_yg,
                        'zg' : new_zg,
                        'xc' : xco_target,
                        'yc' : yco_target,
                        'sigx' : sigx_target,
                        'sigy' : sigy_target,
                        'betx' : betx_target,
                        'bety' : bety_target,
                        }
                for kk in grid.keys():
                    var = grid[kk]
                    if isinstance(var, np.ndarray):
                        dset = grid_group.create_dataset(kk, shape=var.shape, dtype=var.dtype)
                        dset[...] = var
                    else:
                        grid_group[kk] = var

                zero_phi = np.zeros([new_Nx, new_Ny])
                slices_group = Triplet.create_group('slices')
                for ii in range(Nz):
                    sl_group = slices_group.create_group(f'slice{ii}')
                    dset = sl_group.create_dataset('phi', shape=zero_phi.shape, dtype=zero_phi.dtype)
                    dset[...] = zero_phi
                Triplet.create_group('progress')

                del Triplet['fresh']

            xco_source = info['x_b1']
            yco_source = info['y_b1']
            betx_source = info['betx_b1']
            bety_source = info['bety_b1']
            length = info['length']

            xg = pinch['grid/xg'][()]
            yg = pinch['grid/yg'][()]
            for ii in track(range(Nz), description=f'{ecloud_name}'):
                phi = Triplet[f'slices/slice{ii}/phi'][()]
                myslice = pinch[f'slices/slice{ii}/phi'][()]
                trans_xg = ( new_xg - xco_target ) * np.sqrt(betx_source/betx_target) + xco_source
                trans_yg = ( new_yg - yco_target ) * np.sqrt(bety_source/bety_target) + yco_source

                XX, YY = np.meshgrid(trans_xg, trans_yg, indexing='ij')
                int_phi, _ = iff.int_field(XX.flatten(), YY.flatten(), xg[0], yg[0],
                                                            xg[1] - xg[0], yg[1] - yg[0], myslice, myslice)
                phi += length*int_phi.reshape(new_Nx, new_Ny)
                Triplet[f'slices/slice{ii}/phi'][...] = phi
            Triplet[f'progress/{ecloud_name}'] = pendulum.now().to_datetime_string()