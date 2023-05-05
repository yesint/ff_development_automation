#!/bin/bash
for f in ../water_def/water_*.def;do cp $f current_params/water.par; ./manage.py -a ; done