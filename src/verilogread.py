# ---------------start---------------
# 2 functions: veryread, abc_veryread
# -----------------------------------
# veryread:
# read verilog file (output, input, input)
# ----------------------------------- 
# abc_veryread ()
# read verilog file (input, input, output)
# mainly for reading verilog file produced by abc
# ----------------end---------------


def veryread(filename):

    with open(filename, "r") as file:
        contents = file.read()

    lines = contents.split(";")
    # module name
    modulename = lines[0].split("\n")[0].split("(")[0]
    
    # inputs
    inputs_data = lines[1].replace(","," ").split(" ")
    input = []
    for i in inputs_data:
        if (i.startswith("n")) or (i.startswith("p")) :
            input.append(i)
    # print(f"Input is {input}",)

    # outputs
    outputs_data = lines[2].replace(","," ").split(" ")
    output = []
    for i in outputs_data:
        if (i.startswith("n")) or (i.startswith("p")):
            output.append(i)
    # print(f"Output is {output}",)

    # wire
    wire_data = lines[3].split(" ")
    wire = []
    for i in wire_data:
        if (i.startswith("n")):
            wire.append(i)
        if (i.startswith("p")):
            wire.append(i)
    # print(f"Wire is {wire}")

    #gates
    gate = []

    loc = 4
    while True:
        if(lines[loc].startswith("\nendmodule")):
            break
        temp = []
        for i in lines[loc].replace("("," ").replace(")"," ").split(" "):
            if (
            i.startswith("a") or 
            i.startswith("o") or
            i.startswith("g") or 
            i.startswith("n") or 
            i.startswith("b") or 
            i.startswith("x")):
                temp.append(i.lower())
            if (i.startswith("g")):
                temp.append(i)            
            if (i.startswith("n")):
                temp.append(i)
            if (i.startswith("p")):
                temp.append(i)


        loc += 1
    # print(modulename, input, output, wire, gate)
    # print(f"gate is {gate}")
    # print(modulename)
    # print(input)
    # print(output)
    # print(wire)
    # print(gate)
    return modulename, input, output, wire, gate

def abc_veryread(filename):

    with open(filename, "r") as file:
        contents = file.read()

    lines = contents.split(";")
    # module name
    modulename = lines[0].split("\n")[2].split("(")[0]
    
    # inputs
    inputs_data = lines[1].replace(","," ").split(" ")
    input = []
    for i in inputs_data:
        if (i.startswith("n")) or (i.startswith("p")):
            input.append(i)
    # print(f"Input is {input}",)

    # outputs
    outputs_data = lines[2].replace(","," ").split(" ")
    output = []
    for i in outputs_data:
        if (i.startswith("n")) or (i.startswith("p")):
            output.append(i)
    # print(f"Output is {output}",)

    # wire
    wire_data = lines[3].replace(","," ").split(" ")
    wire = []
    for i in wire_data:
        if (i.startswith("n")):
            wire.append(i)
    # print(f"Wire is {wire}")

    #gates
    gate = []

    loc = 4
    while True:
        if(lines[loc].startswith("\nendmodule")):
            break
        temp = []
        for i in lines[loc].replace("("," ").replace(")"," ").split(" "):
            if (
            i.startswith("A") or 
            i.startswith("I") or
            i.startswith("O") or 
            i.startswith("N") or 
            i.startswith("B") or 
            i.startswith("X")):
                temp.append(i.lower())
            if (i.startswith("g")):
                temp.append(i)            
            if (i.startswith("n")):
                temp.append(i)
            if (i.startswith("p")):
                temp.append(i)

        if (len(temp) == 5):
            temp = temp[0:2] + temp[4:5] + temp[2:4]
            gate.append(temp)
        if (len(temp) == 4):
            temp = temp[0:2] + temp[3:] + temp[2:3] + temp[2:3]
            gate.append(temp)

        loc += 1
    # print(modulename)
    # print(input)
    # print(output)
    # print(wire)
    # print(gate)
    # print(f"gate is {gate}")
    return modulename, input, output, wire, gate

if __name__ == "__main__":
    veryread("./src/readtest.v")
    #abc_veryread("tmp/design1_abc.v")