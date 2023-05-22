#!/bin/sh

printf "================== RUNNING SIMULATION ================== \n\n"
python AsynchGHS.py in/10-nodes-network.xml in/10-nodes-network_d.xml "--log=root.fmt:'[%r] [%h] %m%n" 2>&1 | tee out/log_file.log
#python AsynchGHS.py 10-nodes-network.xml 10-nodes-network_d.xml 2>&1 | simgrid-colorizer

printf "\n================== RUNNING PLOTTING ================== \n\n"
python plot_graph_evolution.py

printf "\n================== DONE ================== \n\n"