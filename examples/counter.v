module counter (
    input wire clk,
    input wire rst,
    output reg [3:0] value
);
    always @(posedge clk) begin
        if (rst)
            value <= 4'd0;
        else
            value <= value + 4'd1;
    end
endmodule

