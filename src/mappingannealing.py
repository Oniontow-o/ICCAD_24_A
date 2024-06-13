''' 
function: mapping_annealing(netlist_path, cost_estimator_path, library_path, output_path)
this function takes in the path to the netlist file, the path to the cost estimator, 
the path to the library file, and the path to the output file.
returns the final cost after doing simulated annealing algorithm.

function: initial_mapping(netlist_path, cost_estimator_path, library_path)
this function takes in the path to the netlist file, the path to the cost estimator,
and the path to the library file.
returns the initial cost after map all gates to gate type 1 (ex: and_1, xor_1 ...) .

function: initial_mapping_determine(netlist_path, cost_estimator_path, library_path)
this function takes in the path to the netlist file, the path to the cost estimator,
and the path to the library file.
returns a dictionary represents the assignment of the gate type for each gate that has the lowest cost.

function: initial_mapping_with_assignment(netlist_path, cost_estimator_path, library_path, gatetype_dict)
this function takes in the path to the netlist file, the path to the cost estimator,
the path to the library file, and the dictionary that represents the assignment of the gate type for each gate.
returns the cost after mapping all gates to the gate type in the dictionary.
'''
from abcc import *
import subprocess
import os
import re
import verilogread
import sys
import random
import json
import parsedverilog
import shutil
from tqdm import tqdm
import math

# Function to recursively search for the string "and" in the JSON data
def count_gate(data, typeofgate):
    count = 0
    for cell in data['cells']:
        # Check if the cell_type is 'and'
        if cell['cell_type'] == typeofgate:
            count += 1
    return count

def convert_to_wsl_path(path):
    drive, path = os.path.splitdrive(path)
    path = path.replace('\\', '/')
    return f'/mnt/{drive[0].lower()}{path}'

def get_cost(cost_estimator_path, netlist_path, library_path, output_path):
    # Construct the WSL command
    # print("Cost Estimator Path: ", cost_estimator_path)
    # print("Netlist Path: ", netlist_path)
    # print("Library Path: ", library_path)
    command = [
        # 'wsl',  # Use WSL to run the command
        cost_estimator_path,
        '-netlist', netlist_path,
        '-library', library_path,
        '-output', output_path
    ]
    # print (command)
    # Run the command
    result = subprocess.run(command, capture_output=True, text=True)

    # Check for errors
    match = re.search(r'cost\s*=\s*([0-9.]+)', result.stdout)
    if match:
        cost_value = float(match.group(1))
        return cost_value
    else:
        raise ValueError("Cost value not found in the output.")

def mapping_annealing(netlist_path, cost_estimator_path, library_path, output_path):
    # read the verilog file
    modulename, inputs , outputs, wires, gates = verilogread.veryread(netlist_path)
    # print (modulename)
    # print (inputs)
    # print (outputs)
    # print (wires)
    # print (gates)
    # pause = input("Press Enter to continue...")
    with open(library_path, 'r') as file:
        data = json.load(file)  
    # count the number of each type of gate
    typesofgate = {'and': count_gate(data,'and'), 'or' : count_gate(data,'or'),
                'xor' : count_gate(data,'xor'), 'nand' : count_gate(data,'nand'),
                'nor' : count_gate(data,'nor'), 'xnor' : count_gate(data,'xnor'),
                'not' : count_gate(data,'not'), 'buf' : count_gate(data,'buf')}
    #assign initial gate number to each gate
    gate_number_result = []
    for gate in gates:
        gate_number_result.append(random.randint(1,typesofgate[gate[0]]))  
    
    # get the initial state and initial cost
    tmpmapping_path = "tmp/tmpmapping.v"
    parsedverilog.write_parsed_verilog(tmpmapping_path, modulename, inputs, outputs, gates, gate_number_result)
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
        parsedverilog.write_parsed_verilog(tmpmapping_path, modulename, inputs, outputs, gates, new_gate_number_result)
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

def mapping_annealing_with_initial_determine(netlist_path, cost_estimator_path, library_path, output_path, determine_dictionary):
    # read the verilog file
    modulename, inputs , outputs, wires, gates = verilogread.veryread(netlist_path)
    with open(library_path, 'r') as file:
        data = json.load(file)  
    # count the number of each type of gate
    typesofgate = {'and': count_gate(data,'and'), 'or' : count_gate(data,'or'),
                'xor' : count_gate(data,'xor'), 'nand' : count_gate(data,'nand'),
                'nor' : count_gate(data,'nor'), 'xnor' : count_gate(data,'xnor'),
                'not' : count_gate(data,'not'), 'buf' : count_gate(data,'buf')}
    #assign initial gate number to each gate
    gate_number_result = []
    
    for gate in gates:
        gate_number_result.append(determine_dictionary[gate[0]])  
    
    # get the initial state and initial cost
    tmpmapping_path = "tmp/tmpmapping.v"
    parsedverilog.write_parsed_verilog(tmpmapping_path, modulename, inputs, outputs, gates, gate_number_result)
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
        parsedverilog.write_parsed_verilog(tmpmapping_path, modulename, inputs, outputs, gates, new_gate_number_result)
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

def abc_mapping_annealing(netlist_path, cost_estimator_path, library_path, output_path):
    # read the verilog file
    modulename, inputs , outputs, wires, gates = verilogread.abc_veryread(netlist_path)
    with open(library_path, 'r') as file:
        data = json.load(file)  
    # count the number of each type of gate
    typesofgate = {'and': count_gate(data,'and'), 'or' : count_gate(data,'or'),
                'xor' : count_gate(data,'xor'), 'nand' : count_gate(data,'nand'),
                'nor' : count_gate(data,'nor'), 'xnor' : count_gate(data,'xnor'),
                'not' : count_gate(data,'not'), 'buf' : count_gate(data,'buf')}
    #assign initial gate number to each gate
    gate_number_result = []
    for gate in gates:
        gate_number_result.append(random.randint(1,typesofgate[gate[0]]))  
    
    # get the initial state and initial cost
    tmpmapping_path = "tmp/tmpmapping.v"
    parsedverilog.write_parsed_verilog(tmpmapping_path, modulename, inputs, outputs, gates, gate_number_result)
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
        parsedverilog.write_parsed_verilog(tmpmapping_path, modulename, inputs, outputs, gates, new_gate_number_result)
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

def initial_mapping(netlist_path, cost_estimator_path, library_path):
    # read the verilog file
    modulename, inputs , outputs, wires, gates = verilogread.abc_veryread(netlist_path)
    with open(library_path, 'r') as file:
        data = json.load(file)  
    
    gate_number_result = []
    for gate in gates:
        gate_number_result.append(1)  
    
    # get the initial state and initial cost
    tmpmapping_path = "tmp/initialtmpmapping.v"
    parsedverilog.write_parsed_verilog(tmpmapping_path, modulename, inputs, outputs, gates, gate_number_result)
    cost = get_cost(cost_estimator_path, tmpmapping_path, library_path, "output/output.txt")
    print("Cost: ", cost)
    
    if os.path.isfile(tmpmapping_path):
        os.remove(tmpmapping_path)
    if os.path.isfile("output/output.txt"):
        os.remove("output/output.txt")
    
    return cost

def initial_mapping_with_assignment(netlist_path, cost_estimator_path, library_path, gatetype_dict):
    # read the verilog file
    modulename, inputs , outputs, wires, gates = verilogread.abc_veryread(netlist_path)
    with open(library_path, 'r') as file:
        data = json.load(file)  
    
    # assign the gate number of the gate type to each gate
    gate_number_result = []
    for gate in gates:
        gate_number_result.append(gatetype_dict[gate[0]])  
    
    # get the cost
    tmpmapping_path = "tmp/initialtmpmapping.v"
    parsedverilog.write_parsed_verilog(tmpmapping_path, modulename, inputs, outputs, gates, gate_number_result)
    cost = get_cost(cost_estimator_path, tmpmapping_path, library_path, "output/output.txt")
    print("Cost: ", cost)
    
    if os.path.isfile(tmpmapping_path):
        os.remove(tmpmapping_path)
    if os.path.isfile("output/output.txt"):
        os.remove("output/output.txt")
    
    return cost

def initial_mapping_determine(netlist_path, cost_estimator_path, library_path):
    # read the verilog file
    modulename, inputs , outputs, wires, gates = verilogread.veryread(netlist_path)
    with open(library_path, 'r') as file:
        data = json.load(file)  
    # count the number of each type of gate
    
    gate_number_result = []
    for gate in gates:
        gate_number_result.append(1)  
    
    mapping_dict = {'and' : 1, 'or'   : 1, 'xor' : 1, 'nand' : 1,
                    'nor' : 1, 'xnor' : 1, 'not' : 1, 'buf'  : 1}
    typesofgate  = {'and': count_gate(data,'and'), 'or' : count_gate(data,'or'),
                    'xor' : count_gate(data,'xor'), 'nand' : count_gate(data,'nand'),
                    'nor' : count_gate(data,'nor'), 'xnor' : count_gate(data,'xnor'),
                    'not' : count_gate(data,'not'), 'buf' : count_gate(data,'buf')}
    
    # get the initial state and initial cost
    tmpmapping_path = "tmp/tmpinitialmapping.v"
    parsedverilog.write_parsed_verilog(tmpmapping_path, modulename, inputs, outputs, gates, gate_number_result)
    cost = get_cost(cost_estimator_path, tmpmapping_path, library_path, "output/output.txt")
    print("Initial Cost: ", cost)
    
    for key in mapping_dict:
        for num in range(1,typesofgate[key]+1):
            for gate in gates:
                if gate[0] == key:
                    gate_number_result[gates.index(gate)] = num
            parsedverilog.write_parsed_verilog(tmpmapping_path, modulename, inputs, outputs, gates, gate_number_result)
            new_cost = get_cost(cost_estimator_path, tmpmapping_path, library_path, "output/output.txt")
            if new_cost < cost:
                cost = new_cost
                mapping_dict[key] = num
        for gate in gates:
            if gate[0] == key:
                gate_number_result[gates.index(gate)] = mapping_dict[key]
    
    print("Final Cost = ", cost)
    # print(mapping_dict)
    
    if os.path.isfile(tmpmapping_path):
        os.remove(tmpmapping_path)
    if os.path.isfile("output/output.txt"):
        os.remove("output/output.txt")
    
    return mapping_dict

def abc_annealing(netlist_path, cost_estimator_path, library_path, output_path, initial_dict = None):
    
    # Simulated Annealing parameters
    initialTemperature = 10.0
    Temperature = initialTemperature
    minTemperature = 0.1
    reduceRate = 0.5
    
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
        
        modulename, inputs , outputs, wires, gates = verilogread.abc_veryread(out_folder + filename[:-2] + "_current_abc.v")
        if initial_dict is not None:
            gate_number_result = []
            for gate in gates:
                gate_number_result.append(initial_dict[gate[0]])
            parsedverilog.write_parsed_verilog(out_folder + filename[:-2] + "_current_abc_parsed.v", modulename, inputs, outputs, gates, gate_number_result)
        else:
            gate_number_result = []
            for gate in gates:
                gate_number_result.append(1)
            parsedverilog.write_parsed_verilog(out_folder + filename[:-2] + "_current_abc_parsed.v", modulename, inputs, outputs, gates, gate_number_result)
        
        neighbor_cost = get_cost(cost_estimator_path, out_folder + filename[:-2] + "_current_abc_parsed.v", library_path, "output/output.txt")
        
        print ("neighbor cost: ", neighbor_cost)
        
        if neighbor_cost < current_cost:
            
            parsedverilog.write_verilog(out_folder + filename[:-2] + "_current.v", modulename, inputs, outputs, wires, gates)
            current_cost = neighbor_cost
        else:
            if random.random() < pow(2.71828, (current_cost - neighbor_cost) / Temperature):
                # uphill move
                parsedverilog.write_verilog(out_folder + filename[:-2] + "_current.v", modulename, inputs, outputs, wires, gates)
                current_cost = neighbor_cost
        #update the temperature
        Temperature = Temperature * reduceRate 
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
        print("Usage: python3 getinitialgatenumber.py <verilog_file> <cost_estimator> <library> <output.v>")
        sys.exit(1)
    
    # mapping_annealing(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    # abc_mapping_annealing(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    # initialCost = initial_mapping(sys.argv[1], sys.argv[2], sys.argv[3])
    # dictionary = initial_mapping_determine(sys.argv[1], sys.argv[2], sys.argv[3])
    # mapping_annealing_with_initial_determine(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], dictionary)
    # initial_mapping_with_assignment(sys.argv[1], sys.argv[2], sys.argv[3], dictionary)
    verilog_file_path = abc_annealing(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    mapping_annealing(verilog_file_path, sys.argv[2], sys.argv[3], sys.argv[4])