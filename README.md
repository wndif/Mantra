# Mantra: Mutation Testing of Hardware Design Code Based on Real Bugs
# Dependencies:
PyVerilog 1.2.1
    pip3 install pyverilog==1.2.1
    Make sure to replace source files for PyVerilog to support Mantra (see documentaiton in /pyverilog_changes).

Icarus Verilog
    sudo yum install iverilog (for RHEL)

Synopsys VCS
    (Commercial license; you may use alternative Verilog simulators, but would likely need to modify the scripts to match the API of the simulator.)
