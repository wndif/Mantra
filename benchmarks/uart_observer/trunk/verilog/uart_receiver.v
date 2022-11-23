module uart_receiver (
  input RXD,
  input CTR,
  
  input CLK_I,
  
  output wire [BITS-1:0] DAT_O  
);

// Clock frequency Hz
 parameter CLOCK_FREQ = 90_000_000;
 
 // Serial port speed baud
 parameter BAUDS = 921600;
 
 parameter DIV_MAX = CLOCK_FREQ/BAUDS; // 9375; 781; 
 
 parameter BITS = 32;
 
 parameter N = 10; // 16;
 parameter H = N-1; // Highest bit
 
 // RAM buffer to transfer from
 parameter RAM_LENGTH = 8;
 reg [7:0] mem [RAM_LENGTH - 1:0];
 // RAM index of value currently being sent
 reg [7:0] ram_addr = 0;
                          
 // Divider to 1 baud, receiver
 reg [31:0] divider_rx = 0;
 
 // Previous value of the RX line, for edge detection
 reg prev_rx = 1; 
 
 // Internal phase counters to track what we are doing
 reg [4:0] phase_rx = 0;

 // Initialize RAM with content to send
 initial
   begin
     mem[0] <= 8'b0011_0000;
     mem[1] <= 8'b0011_0001;
     mem[2] <= 8'b0011_0010;
     mem[3] <= 8'b0011_0011;
     mem[4] <= 8'b0011_0100;
     mem[5] <= 8'b0011_0101;
     mem[6] <= 8'b0011_0110;
     mem[7] <= 8'b0011_0111;     
   end
 
 // Increement the "phase_rx" variable that loops over 0-1-2-3-4-5-6-7-8-9-0
 task increment_phase_rx;
   begin
     if (phase_rx == 9)
       phase_rx = 0;
     else     
       phase_rx = phase_rx + 1;  
   end
 endtask; 
 
 // Signal transmission edge (to FPGA)
 reg [7:0] rxEdge = 0;
 reg [7:0] rxData = 0;
 reg [2:0] rxBit = 0;
 
 // Receiver servicing loop
 always @(posedge CLK_I)
 begin
   if (RXD != prev_rx) // edge
   begin
     // Upon the edge, position relative point of reading into the middle 
     // of the data reference. This can be done at any edge but at least
     // will be done for the start bit edge. It is not much difference
     // if this is a positive edge or negative (both happen 1/2 baud interval
     // before the value that must be observed 
     divider_rx <= DIV_MAX  >> 2;
     prev_rx = RXD;
     rxEdge <= rxEdge + 1;     
   end  
   if (divider_rx > DIV_MAX)
     begin       
       if (phase_rx == 0 && RXD == 0)
         begin
          // Start bit received         
           phase_rx <= 1;
           rxBit <= 0;
         end
       else if (phase_rx == 9 && RXD == 1)
         begin
           // stop bit received
           // rxData ready now
           phase_rx <= 0;
           
           // Take the received data into mem[0] for now.
           mem[0] <= rxData;
         end
       else if (phase_rx != 9 && phase_rx !=0)
         begin
           // Ordinary step
           rxData[rxBit] = RXD;
           rxBit = rxBit + 1;           
           phase_rx <= phase_rx + 1;                                            
         end;
       divider_rx = 0;      
     end
     
   divider_rx = divider_rx + 1;  
 end

 assign DAT_O[0] = rxData[0];
 assign DAT_O[1] = rxData[1];
 assign DAT_O[2] = rxData[2];
 assign DAT_O[3] = rxData[3];
 assign DAT_O[4] = rxData[4];
 assign DAT_O[5] = rxData[5];
 assign DAT_O[6] = rxData[6];
 assign DAT_O[7] = rxData[7]; 
 
endmodule
