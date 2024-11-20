#!/bin/bash

export XRD_STREAMTIMEOUT=600

echo $KRB5CCNAME
klist -f

pwd
which python

ecloud_name=$1
collider=$2
sey=$3
intensity=$4
blen=$5

eos_url=root://eosproject.cern.ch/
parent=/eos/project/e/ecloud-simulations/kparasch/LHC_Triplets

xrdcp -r $eos_url$parent/Template_LHCIT_ecloud_buildup .
cd Template_LHCIT_ecloud_buildup

xrdcp $eos_url$parent/Colliders/$collider/eclouds_LHCIT_slices.json .
xrdcp $eos_url$parent/Colliders/$collider/eclouds_LHCIT_triplets.json .

python config.py --ecloud $ecloud_name --sey_max $sey --intensity $intensity --bunch_length $blen
python buildup.py

cat logfile.txt

xrdcp Pyecltest.mat $eos_url$parent/Buildup/$collider/sey${sey}_intensity${intensity}_blen${blen}/$ecloud_name.mat
sleep 5
xrdcp Pyecltest.mat $eos_url$parent/Buildup/$collider/sey${sey}_intensity${intensity}_blen${blen}/$ecloud_name.mat
sleep 5
xrdcp Pyecltest.mat $eos_url$parent/Buildup/$collider/sey${sey}_intensity${intensity}_blen${blen}/$ecloud_name.mat

python pinch.py --ecloud $ecloud_name

python combine.py --ecloud $ecloud_name --sey_max $sey --intensity $intensity --bunch_length $blen \
                  --path $parent/Pinches/$collider/ --eos_url $eos_url
