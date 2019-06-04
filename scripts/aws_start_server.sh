#!/bin/bash

sudo pkill python3
rm log/*
python3 src/chord.py $1 --id $2 --join $3
#address, id, join, server_config_file, remote):