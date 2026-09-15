`timescale 1ns/1ps
// Value-dump testbench: writes one CSV row per sampled cycle and finishes
// cleanly.  Mantra2 compares this dump against the golden run to decide
// observable vs equivalent, so the bench must NOT abort on a mismatch.
module counter_tb;
    reg clk = 0;
    reg rst = 1;
    wire [3:0] value;
    integer output_file;
    counter dut(.clk(clk), .rst(rst), .value(value));
    always #5 clk = ~clk;
    initial begin
        output_file = $fopen("output.txt", "w");
        $fwrite(output_file, "time,value\n");
        #12 rst = 0;
        repeat (8) begin
            #10;
            $fwrite(output_file, "%0t,%0d\n", $time, value);
        end
        $fclose(output_file);
        $finish;
    end
endmodule
