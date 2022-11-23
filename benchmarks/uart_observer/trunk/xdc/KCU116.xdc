# W12 RX Input LVCMOS18 USB_UART_TX 21 TXD Output
# W13 TX Output LVCMOS18 USB_UART_RX 20 RXD Input
# Y13 CTS Output LVCMOS18 USB_UART_CTS 18 CTS Input
# AA13 RTS Input LVCMOS18 USB_UART_RTS 19 RTS Output

#USB UART
set_property PACKAGE_PIN W13 [get_ports USB_UART_RX_FPGA_TX_LS]
set_property IOSTANDARD LVCMOS33 [get_ports USB_UART_RX_FPGA_TX_LS]

set_property PACKAGE_PIN W12 [get_ports USB_UART_TX_FPGA_RX_LS]
set_property IOSTANDARD LVCMOS33 [get_ports USB_UART_TX_FPGA_RX_LS]

set_property PACKAGE_PIN AA13 [get_ports USB_UART_RTS_O_B_LS]
set_property IOSTANDARD LVCMOS33 [get_ports USB_UART_RTS_O_B_LS]

set_property PACKAGE_PIN Y13 [get_ports USB_UART_CTS_I_B_LS]
set_property IOSTANDARD LVCMOS33 [get_ports USB_UART_CTS_I_B_LS]

#GPIO

#GPIO PB SWITCHES
set_property PACKAGE_PIN B11 [get_ports GPIO_SW_E]
set_property IOSTANDARD LVCMOS33 [get_ports GPIO_SW_E]
set_property PACKAGE_PIN A10 [get_ports GPIO_SW_N]
set_property IOSTANDARD LVCMOS33 [get_ports GPIO_SW_N]
set_property PACKAGE_PIN B10 [get_ports GPIO_SW_W]
set_property IOSTANDARD LVCMOS33 [get_ports GPIO_SW_W]
set_property PACKAGE_PIN A9 [get_ports GPIO_SW_C]
set_property IOSTANDARD LVCMOS33 [get_ports GPIO_SW_C]
set_property PACKAGE_PIN C11 [get_ports GPIO_SW_S]
set_property IOSTANDARD LVCMOS33 [get_ports GPIO_SW_S]

#GPIO DIP SWITCHES
set_property PACKAGE_PIN G11 [get_ports "GPIO_DIP_SW0"] ;
set_property IOSTANDARD LVCMOS33 [get_ports "GPIO_DIP_SW0"] ;
set_property PACKAGE_PIN H11 [get_ports "GPIO_DIP_SW1"] ;
set_property IOSTANDARD LVCMOS33 [get_ports "GPIO_DIP_SW1"] ;
set_property PACKAGE_PIN H9 [get_ports "GPIO_DIP_SW2"] ;
set_property IOSTANDARD LVCMOS33 [get_ports "GPIO_DIP_SW2"] ;
set_property PACKAGE_PIN J9 [get_ports "GPIO_DIP_SW3"] ;
set_property IOSTANDARD LVCMOS33 [get_ports "GPIO_DIP_SW3"] ;

# LEDs 
#GPIO LEDs
set_property PACKAGE_PIN C9 [get_ports GPIO_LED_0]
set_property IOSTANDARD LVCMOS33 [get_ports GPIO_LED_0]
set_property PACKAGE_PIN D9 [get_ports GPIO_LED_1]
set_property IOSTANDARD LVCMOS33 [get_ports GPIO_LED_1]
set_property PACKAGE_PIN E10 [get_ports GPIO_LED_2]
set_property IOSTANDARD LVCMOS33 [get_ports GPIO_LED_2]
set_property PACKAGE_PIN E11 [get_ports GPIO_LED_3]
set_property IOSTANDARD LVCMOS33 [get_ports GPIO_LED_3]
set_property PACKAGE_PIN F9 [get_ports GPIO_LED_4]
set_property IOSTANDARD LVCMOS33 [get_ports GPIO_LED_4]
set_property PACKAGE_PIN F10 [get_ports GPIO_LED_5]
set_property IOSTANDARD LVCMOS33 [get_ports GPIO_LED_5]
set_property PACKAGE_PIN G9 [get_ports GPIO_LED_6]
set_property IOSTANDARD LVCMOS33 [get_ports GPIO_LED_6]
set_property PACKAGE_PIN G10 [get_ports GPIO_LED_7]
set_property IOSTANDARD LVCMOS33 [get_ports GPIO_LED_7]

#CLOCKS

#create_clock -period 1000000.000 -name AM_CLOCK -waveform {0.000 500000.000} [get_ports CLK_125_P]

set_property ALLOW_COMBINATORIAL_LOOPS true [get_nets *]
# set_property CLOCK_DEDICATED_ROUTE FALSE [get_nets *]

# Forum clock (90.0 MHz single-ended 1.8V LVCMOS, series resistor coupled FPGA_EMCCLK, connected to XCKU5P FPGA U1 bank 65 dedicated EMCCLK input pin N21), works posedge
set_property PACKAGE_PIN N21 [get_ports CLK_I]
set_property IOSTANDARD LVCMOS18 [get_ports CLK_I]

set_property CLOCK_DEDICATED_ROUTE FALSE [get_nets CLK_I_IBUF_inst/O]

create_clock -period 11.111 -name CLK_I -waveform {0.000 5.556} [get_ports CLK_I]


