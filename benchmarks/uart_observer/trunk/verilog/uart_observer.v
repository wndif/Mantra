`timescale 1ns / 1ps

//////////////////////////////////////////////////////////////////////////////////
// Company: none 
// Engineer: Audrius Meskauskas
// 
// Create Date: 03/10/2018 09:31:52 PM
// Design Name:  UART observer
// Module Name: uart_observer
// 
//////////////////////////////////////////////////////////////////////////////////

module uart_observer (
// clock, tested with 90 MHZ clock
  input CLK_I,  

  // The array of observables.
  input wire [BITS-1:0] DAT_I,
  
  // UART  
  input CTS, // "clear to send"
  
  output TXD, // Serial data output
  output RTS  // Request to send, this UART does not send all the time.
);

 // The number of bits to show in the output
 parameter  BITS = 128;

// Clock frequency Hz
 parameter CLOCK_FREQ = 90_000_000;
 
 // Serial port speed baud
 parameter BAUDS = 921600; // 9600;
 
 parameter DIV_MAX = CLOCK_FREQ/BAUDS; 
 
 parameter DIV_BITS = 32; // bits in frequency divider
 
 parameter N = 10; 
 parameter H = N-1; // Highest bit
 
 // RAM buffer to transfer from 
 parameter RAM_LENGTH = 3 + 3 + 11*BITS;
 reg [7:0] mem [RAM_LENGTH - 1:0];
 // RAM index of value currently being sent
 reg [7:0] ram_addr = 0;
                          
 // Divider to 1 baud                          
 reg [DIV_BITS:0] divider = 0;
 
 // Internal phase counter to track what we are doing
 reg [4:0] phase = 0;
 
 // The output data connector
 wire s_out;
 // The output "sending" connector
 reg sending = 0;
 
 // Main sending register
 reg [H:0] r_reg;
 
 wire [H:0] r_next; 
 wire [H:0] r_sendit;
 
 // The byte being written
 reg [7:0] out; // = 8'b0011_0001;
 
 // New data from the buffer (start bit on the right)
 assign r_sendit = { 1'b1, out, 1'b0 };
 
 // Shifted value
 assign r_next = { 1'b0, r_reg [H:1] };
 // Out output (lowest bit)
 assign s_out = r_reg[0];

 reg [BITS-1:0] observables_reg;
 reg [BITS-1:0] observables_prev = 32'hFFFFF;
 
 parameter [7:0] ESC = 8'b0001_1011;
 
 integer b;
 integer p;
 integer bytes_in_row;
 
 // Initialize RAM with content to send
 initial
   begin
     // See http://www.termsys.demon.co.uk/vtansi.htm
     // Top left corner (ESC [ H)
     
     mem[0] <= ESC; // ESC
     mem[1] <= "["; // [
     mem[2] <= "H"; // H
     
     /*
     for (b = 3; b <= 3 + BITS*11; b = b + 11)
       render_byte(b);
     */  
     bytes_in_row = 0;  
     p = 3;  
     for (b = 0; b < BITS/8; b = b + 1) 
       begin      
         if (bytes_in_row == 3)
           begin
             render_byte(p, 8'h0d, 8'h0a);
             bytes_in_row = 0;
           end 
         else
           begin
             render_byte(p, " ", " ");
             bytes_in_row = bytes_in_row + 1;
           end;    
         p = p + 11;
       end  
     
     // Erase till end of screen (ESC [ J)
     mem[p] <= ESC; // ESC
     mem[p + 1] <= "["; // [
     mem[p + 2] <= "J"; // J    
   end

// Prepare initial data to render the byte (11 bytes - tetrad spacer and doubled byte spacer)
// The last two bytes (parameters) are inter-byte spacer that may be row separator.
task render_byte;
   input integer p;
   input reg [7:0] b1;
   input reg [7:0] b2;
   
   begin
     // (first tetrad 0 .. 3)
     mem[p + 4] <= " "; // Space separator
     // (second tetrad 5 .. 8)       
     // (Two spaces)    
     mem[p + 9] <= b1; // space
     mem[p + 10] <= b2; // space
   end
endtask   
   
 // Convert a bit to ASCII representation of it.  
 function [7:0] ascii;
    input x;
    begin
      if (x==0)
        ascii = "."; // dot
      else
        ascii = "1";  
    end
 endfunction   
   
 // Loop over all 32 bits, populating memory cells with translated values.  
 task update_ram;
   integer k;
   integer b;
   integer ib; // bit
   integer p; // memory pointer
   begin
     ib = 0;
     p = 3; // Leave place for the header
     for (b = 0; b < BITS / 8; b = b + 1) 
       begin
         for (k = 0; k < 4; k = k + 1) 
           begin
             mem[p] = ascii(observables_reg[ib]);
             ib = ib + 1;
             p = p + 1;
           end  
       
         p = p + 1; // spacer between tetrads
     
         for (k = 4; k < 8; k = k + 1)
           begin 
             mem[p] = ascii(observables_reg[ib]);
             ib = ib + 1;
             p = p + 1;
           end
           
         p = p + 2; // spacer between bytes  
       end
   end
 endtask
 
 // Populate the register 'out' with next data to write  
 task next_data;
   begin
     out = mem[ram_addr];
     ram_addr = ram_addr + 1;
     if (ram_addr == RAM_LENGTH)
       ram_addr = 0;
   end
 endtask 
 
 // Increement the "phase" variable that loops over 0-1-2-3-4-5-6-7-8-9-0
 task increment_phase;
   begin
     if (phase == 9)
       begin
         phase <= 0;
         observables_prev <= observables_reg;
       end         
     else     
       phase <= phase + 1;  
   end
 endtask    
 
 always @(posedge CLK_I)
 begin :cl
   // Need 781.25 (90000000 Hz to 115200 Hz)
   if (divider > DIV_MAX)
     begin
       if (phase == 0 && ram_addr == 0)
         begin
           observables_reg = DAT_I;
           if (observables_prev == observables_reg)
             begin
               r_reg <= 10'b1_1111_1111_1;   
               divider <= 0;
               sending <= 0;
               disable cl;
             end
           else
             update_ram();               
         end
           
       sending = 1;         
       if (CTS == 0)
         begin      
           // Not clear to send, keep inactive line high
           r_reg <= 10'b1_1111_1111_1;       
           phase <= 0;
           divider <= 0;
           disable cl;
         end;
       
       if (phase == 0)
         begin
            next_data();
            r_reg = r_sendit;            
         end
       else
         begin
           r_reg <= r_next;
         end;           
         
       increment_phase();  
       
       divider = 0;      
     end 

     divider = divider + 1;     
 end
 
 assign TXD = s_out;  
 assign RTS = sending; 
 
endmodule

