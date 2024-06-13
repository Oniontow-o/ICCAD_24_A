# Interface For Batch Mode ABC
# type: ignore

import subprocess
import os 
import random

possible_cmds = [
"strash; balance;",
"strash; rewrite -l;",
"strash; rewrite -lz;",
"strash; dsd; strash;",
"strash; iresyn -l;",
"strash; dc2 -bl;",
"strash; refactor -N 15 -lz;",
"strash; orchestrate;",
"strash; resub -lz;",
"strash; csweep; trim;",
# "&get; &muxdec; &put;",
]

abc_path = "./src/abc"
gate_lib_path = "./data/lib/lib1.genlib"

def get_random_cmd(in_folder, out_folder, gate_lib, filename):
    choosen = random.choice(possible_cmds)
    prefix = f"read_verilog {in_folder}{filename};"
    suffix = f"read_library {gate_lib};map;write_verilog {out_folder}{filename[:-2]}_abc.v;"
    return prefix + choosen + suffix

def abc_exec(abc_path, cmd):
    subprocess.run([abc_path, "-c", cmd])
    
def abc_print(abc_path, folder, filename):
    subprocess.run([abc_path, "-c", f"read_verilog {folder}{filename}; print_stats;"])

def abc_out_to_default(folder, filename):
    with open(f"{folder}{filename}", "r") as file:
        contents = file.read()[2:]
    

if __name__ == "__main__":
    folder = "./data/netlists/"
    #folder = "./tmp/"
    out_folder = "./tmp/"
    #filename = os.listdir(folder)[0]
    filename = "design1.v"
    gate_lib_path = "./data/lib/lib1.genlib"
    assert filename.endswith(".v")
    cmd = get_random_cmd(folder, out_folder, gate_lib_path, filename)
    print(cmd)
    abc_exec(abc_path, cmd)
    abc_print(abc_path, out_folder, filename[:-2] + "_abc.v")
    
    
    

 