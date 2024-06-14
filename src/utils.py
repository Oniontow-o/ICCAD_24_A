import re
import subprocess

gate_list: list[str] = ["and", "or", "nand", "nor", "xor", "xnor", "not", "buf"]

def is_single_gate(gate:str) -> bool:
    '''
    check if the gate is a single gate
    '''
    if gate.startswith(("not", "buf")):
        return True
    return False

def number_of_choices(libs: dict) -> dict[str, int]:
    '''
    return the number of choices for each type of gates
    '''
    libs = libs["cells"]
    result = {gate: 0 for gate in gate_list}
    for cell in libs:
        result[cell["cell_type"]] += 1
    return result

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
    # print("result:",result.stdout)
    match = re.search(r'cost\s*=\s*([0-9.]+)', result.stdout)
    if not match:
        raise ValueError("Cost value not found in the output.")
    cost_value = float(match.group(1))
    return cost_value

possible_cmds = [
"src_rw      ",
"src_rs      ",
"src_rws     ",
"resyn2rs    ",
"r2rs        ",
"compress2rs ",
"c2rs        ",
"&resyn2rs   ",
"&compress2rs",
"resyn       ",
"resyn2      ",
"resyn2a     ",
"resyn3      ",
"compress    ",
"compress2   ",
"choice      ",
"choice2     ",
"rwsat       ",
"drwsat2     ",
"share       ",
"addinit     ",
"blif2aig    ",
"v2p         ",
"g2p         ",
"&sw_        ",
"&fx_        ",
"&dc3        ",
"&dc4        ",
"recadd3     ",
]