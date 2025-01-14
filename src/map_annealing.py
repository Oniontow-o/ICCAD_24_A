from abc_cmd import *
import subprocess
import os
import re
import verilog_read
import sys
import random
import json
import verilog_write
import shutil
from tqdm import tqdm
import math

from utils import count_gate, convert_to_wsl_path, get_cost, gate_list
from pick_singlegate import find_initial_mapping

# Function to recursively search for the string "and" in the JSON data

def map_annealing(netlist_path, cost_estimator_path, 
                      library_path, output_path,
                      determine_dict = None):
    '''
    this function takes in the path to the netlist file, the path to the cost estimator, 
    the path to the library file, and the path to the output file.
    returns the final cost after doing simulated annealing algorithm.
    '''
    # read the verilog file
    modulename, inputs , outputs, wires, gates = verilog_read.read_verilog(netlist_path)
    with open(library_path, 'r') as file:
        data = json.load(file)  
    # count the number of each type of gate
    typesofgate = {gate: count_gate(data,gate) for gate in gate_list}
    #assign initial gate number to each gate
    gate_number_result = []
    
    if determine_dict:
        for gate in gates:
            gate_number_result.append(determine_dict[gate[0]])  
    else:
        for gate in gates:
            gate_number_result.append(random.randint(1,typesofgate[gate[0]]))  
    
    # get the initial state and initial cost
    tmpmapping_path = "tmp/tmpmapping.v"
    verilog_write.write_parsed_verilog(tmpmapping_path, modulename, inputs, outputs, gates, gate_number_result)
    current_cost = get_cost(cost_estimator_path, tmpmapping_path, library_path, "output/output.txt")
    print("Initial Cost: ", current_cost)
    
    # Simulated Annealing parameters
    initialTemperature = 1000.0
    Temperature = initialTemperature
    minTemperature = 0.001
    reduceRate = 0.99
    
    lengthOfGates = len(gates)
    #define costs
    neighbor_cost = 0
    final_cost = current_cost
    #create a copy of the initial mapping so that we can copy the best mapping to the output file
    shutil.copy(tmpmapping_path, output_path)
    #progress bar
    pbar = tqdm(total=math.ceil(math.fabs(math.log(Temperature/minTemperature)/math.log(reduceRate))))
    
    while Temperature > minTemperature:
        # create a new gate number result
        new_gate_number_result = gate_number_result.copy()
        for i in range(0, min(math.floor(lengthOfGates * Temperature ), lengthOfGates * 10)):
            # move to neighbour state
            index = random.randint(0, lengthOfGates - 1)
            new_gate_number_result[index] = random.randint(1,typesofgate[gates[index][0]])
        # get the final_cost of the new state
        verilog_write.write_parsed_verilog(tmpmapping_path, modulename, inputs, outputs, gates, new_gate_number_result)
        neighbor_cost = get_cost(cost_estimator_path, tmpmapping_path, library_path, "output/output.txt")
        
        #compare the final_cost with the current_cost
        if neighbor_cost < current_cost:
            gate_number_result = new_gate_number_result
            current_cost = neighbor_cost
            if neighbor_cost < final_cost:
                final_cost = neighbor_cost
                shutil.copy(tmpmapping_path, sys.argv[4])
        else:
            if random.random() < pow(2.71828, (current_cost - neighbor_cost) / Temperature):
                # uphill move
                gate_number_result = new_gate_number_result
                current_cost = neighbor_cost
        #update the temperature
        Temperature = Temperature * reduceRate 
        pbar.update(1)
    pbar.close()
    print("Final Cost: ", final_cost)
    
    if os.path.isfile(tmpmapping_path):
        os.remove(tmpmapping_path)
    if os.path.isfile("output/output.txt"):
        os.remove("output/output.txt")
    
    return final_cost

def abc_annealing(netlist_path, cost_estimator_path, library_path, output_path, initial_dict = None):
    
    # Simulated Annealing parameters
    initialTemperature = 10.0
    Temperature = initialTemperature
    minTemperature = 0.1
    reduceRate = 0.8
    
    #define costs
    neighbor_cost = 0
    current_cost = float('inf')
    final_cost = current_cost
    
    #progress bar
    pbar = tqdm(total=math.ceil(math.fabs(math.log(Temperature/minTemperature)/math.log(reduceRate))))

    folder = netlist_path[:netlist_path.rfind('/')+1]
    # out folder = "./tmp/"
    out_folder = "./tmp/"
    #filename = os.listdir(folder)[0]
    filename = netlist_path[netlist_path.rfind('/')+1:]
    # print("Filename: ", filename)
    gate_lib_path = "./data/lib/lib1.genlib"
    assert filename.endswith(".v")
    
    shutil.copy(netlist_path, "./tmp/"+ filename[:-2] + "_current.v")
    
    loopcount = 0
    while Temperature > minTemperature:
        loopcount += 1
        # print("\nLoop Count: ", loopcount,"\n")
        # get the initial state and initial cost
        
        cmd = get_random_cmd(out_folder, out_folder, gate_lib_path, filename[:-2] + "_current.v")
        # print("\nCommand = ", cmd, "\n")
        abc_exec(abc_path, cmd)
        # abc_print(abc_path, out_folder, filename[:-2] + "_current_abc.v")
        
        modulename, inputs , outputs, wires, gates = verilog_read.abc_read_verilog(out_folder + filename[:-2] + "_current_abc.v")
        if initial_dict is not None:
            gate_number_result = [initial_dict[gate[0]] for gate in gates]
        else:
            gate_number_result = [1 for gate in gates]
        verilog_write.write_parsed_verilog(out_folder + filename[:-2] + "_current_abc_parsed.v", modulename, inputs, outputs, gates, gate_number_result)
        
        neighbor_cost = get_cost(cost_estimator_path, out_folder + filename[:-2] + "_current_abc_parsed.v", library_path, "output/output.txt")
        if loopcount == 1:
            print ("initial cost: ", neighbor_cost)
        
        if neighbor_cost < current_cost:
            verilog_write.write_verilog(out_folder + filename[:-2] + "_current.v", modulename, inputs, outputs, wires, gates)
            current_cost = neighbor_cost
        else:
            if random.random() < 0.05 * pow(2.71828, (current_cost - neighbor_cost) / Temperature):
                # uphill move
                verilog_write.write_verilog(out_folder + filename[:-2] + "_current.v", modulename, inputs, outputs, wires, gates)
                current_cost = neighbor_cost
        #update the temperature
        Temperature *= reduceRate 
        pbar.update(1)
    pbar.close()
    print("Stage 1 Cost: ", current_cost)
    
    if os.path.isfile("output/output.txt"):
        os.remove("output/output.txt")
    if os.path.isfile(out_folder + filename[:-2] + "_current_abc.v"):
        os.remove(out_folder + filename[:-2] + "_current_abc.v")
    if os.path.isfile(out_folder + filename[:-2] + "_current_abc_parsed.v"):
        os.remove(out_folder + filename[:-2] + "_current_abc_parsed.v")
    
    return out_folder + filename[:-2] + "_current.v"

if __name__ == "__main__":
    if(len(sys.argv) != 5):
        print("Usage: python3 mappingannealing.py <verilog_file> <cost_estimator> <library> <output.v>")
        sys.exit(1)
    
    '''
    example usage:
    type: python3 src/mappingannealing.py data/netlists/design1.v data/cost_estimators/cost_estimator_4 data/lib/lib1.json output/output.v
    '''
    
    # verilog_file_path = abc_annealing(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    # map_annealing(verilog_file_path, sys.argv[2], sys.argv[3], sys.argv[4])
    
    module_name, _, _, _, _ = verilog_read.read_verilog(sys.argv[1])
    dictionary = find_initial_mapping(module_name, sys.argv[2], sys.argv[3])
    verilog_file_path = abc_annealing(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], dictionary)
    map_annealing(verilog_file_path, sys.argv[2], sys.argv[3], sys.argv[4], dictionary)