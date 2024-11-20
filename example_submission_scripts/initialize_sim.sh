#!/bin/bash

parent=/eos/project/e/ecloud-simulations/kparasch/LHC_Triplets

xing=150

intensity=1.20
collider=Run3_2023_collisions_30cm_${xing}urad_${intensity}e11_2.0um_62.310_60.320_20_300_0.001

sey=1.30
blen=0.09

sed -i "/collider\ =\ /c\collider\ =\ ${collider}" submit.sub
sed -i "/sey\ =\ /c\sey\ =\ ${sey}" submit.sub
sed -i "/intensity\ =\ /c\intensity\ =\ ${intensity}" submit.sub
sed -i "/blen\ =\ /c\blen\ =\ ${blen}" submit.sub


mkdir -p log_${collider}_sey${sey}_intensity${intensity}_blen${blen}/
mkdir -p ${parent}/Pinches/${collider}
mkdir -p ${parent}/Refined_pinches/${collider}
mkdir -p ${parent}/Buildup/${collider}/sey${sey}_intensity${intensity}_blen${blen}
cp test.h5 ${parent}/Pinches/${collider}/LHCIT_itr1_sey${sey}_intensity${intensity}_blen${blen}.h5
cp test.h5 ${parent}/Pinches/${collider}/LHCIT_itl1_sey${sey}_intensity${intensity}_blen${blen}.h5
cp test.h5 ${parent}/Pinches/${collider}/LHCIT_itr5_sey${sey}_intensity${intensity}_blen${blen}.h5
cp test.h5 ${parent}/Pinches/${collider}/LHCIT_itl5_sey${sey}_intensity${intensity}_blen${blen}.h5

echo
cat submit.sub
echo

tree -L 2 ${parent}

condor_submit submit.sub
