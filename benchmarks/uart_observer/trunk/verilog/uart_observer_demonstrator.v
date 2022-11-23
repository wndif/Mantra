/**
* Demonstrates the functionality of the UART observer. Reads 64 bits from the terminal keyboard.
*/
module uart_observer_demonstrator (
  input USB_UART_TX_FPGA_RX_LS,
  input USB_UART_CTS_I_B_LS,
  input CLK_I,
  
  input GPIO_SW_E,
  input GPIO_SW_W,
  input GPIO_SW_S,
  input GPIO_SW_N,
  input GPIO_SW_C,  
  
  input GPIO_DIP_SW0,
  input GPIO_DIP_SW1,
  input GPIO_DIP_SW2,
  input GPIO_DIP_SW3,

  output GPIO_LED_0,
  output GPIO_LED_1,
  output GPIO_LED_2,
  output GPIO_LED_3,
  output GPIO_LED_4,
  output GPIO_LED_5,
  output GPIO_LED_6,
  output GPIO_LED_7,
  
  output USB_UART_RX_FPGA_TX_LS,
  output USB_UART_RTS_O_B_LS  
);

 // 32 bits we observe.
 wire [31:0] observables;
 
 uart_receiver #(.CLOCK_FREQ (90_000_000), .BAUDS(921600), .BITS(32) ) 
 UR(
  // Clock
  .CLK_I(CLK_I),
  
  // Values to observer
  .DAT_O(observables),
  
  // UART
  .RXD(USB_UART_TX_FPGA_RX_LS), // data  
  .CTR(USB_UART_CTS_I_B_LS)     // clear to receive
 );  
 
 uart_observer #(.CLOCK_FREQ (90_000_000), .BAUDS(921600), .BITS(32) ) 
 U0(
  // Clock
  .CLK_I(CLK_I),
  
  // Values to observer
  .DAT_I(observables),
  
  // UART
  .TXD(USB_UART_RX_FPGA_TX_LS), // data  
  .RTS(USB_UART_RTS_O_B_LS),    // request to send
  .CTS(USB_UART_CTS_I_B_LS)     // clear to send
  
 ); 

 assign GPIO_LED_0 = observables[0];
 assign GPIO_LED_1 = observables[1];
 assign GPIO_LED_2 = observables[2];
 assign GPIO_LED_3 = observables[3]; 
 assign GPIO_LED_4 = observables[4];
 
endmodule
