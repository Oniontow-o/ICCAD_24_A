def write_parsed_verilog(filename, modulename, inputs, outputs, gates ,gate_number_result):
    with open(filename, "w") as file:
        inputlist = ", ".join(f"{input}" for input in inputs)
        outputlist = ", ".join(f"{output}" for output in outputs)
        file.write(modulename + " (" + inputlist + ", " + outputlist + ");\n")
        # file.write("module top_1598227639_809568180_776209382_1234615" + " (" + inputlist + ", " + outputlist + ");\n")
        file.write("  input " + inputlist + ';' + '\n')
        file.write("  output " + outputlist + ';' + '\n')
        for i in range(0, len(gates)):
            # print (gates[i])
            if gates[i][0] != 'not' and gates[i][0] != 'buf':
                file.write("  " + gates[i][0] + "_" + str(gate_number_result[i]) +" "+ gates[i][1] + "(" + gates[i][3] + "," + gates[i][4] + "," + gates[i][2] + ");\n")
            else:
                file.write("  " + gates[i][0] + "_" + str(gate_number_result[i]) +" "+ gates[i][1] + "(" + gates[i][4] + "," + gates[i][2] + ");\n")
        file.write('endmodule\n')

def write_verilog(filename, modulename, inputs, outputs, wires, gates):
    with open(filename, "w") as file:
        inputlist = ", ".join(f"{input}" for input in inputs)
        outputlist = ", ".join(f"{output}" for output in outputs)
        wirelist = ", ".join(f"{wire}" for wire in wires)
        file.write(modulename + "(" + inputlist + ", " + outputlist + ");\n")
        file.write("  input " + inputlist + ';' + '\n')
        file.write("  output " + outputlist + ';' + '\n')
        file.write("  wire " + wirelist + ';' + '\n')
        for i in range(0, len(gates)):
            if gates[i][0] != 'not' and gates[i][0] != 'buf':
                file.write("  " + gates[i][0] +" "+ gates[i][1] + " ( " + gates[i][2] + " , " + gates[i][3] + " , " + gates[i][4] + " ) ;\n")
            else:
                file.write("  " + gates[i][0] +" "+ gates[i][1] + " ( " + gates[i][2] + " , " + gates[i][4] + " ) ;\n")
        file.write('endmodule\n')