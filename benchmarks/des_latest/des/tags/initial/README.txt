/////////////////////////////////////////////////////////////////////
////                                                             ////
////  DES CORE                                                   ////
////                                                             ////
////  Author: Rudolf Usselmann                                   ////
////          russelmann@hotmail.com                             ////
////                                                             ////
/////////////////////////////////////////////////////////////////////
////                                                             ////
//// Copyright (C) 2000 Rudolf Usselmann                         ////
////                    russelmann@hotmail.com                   ////
////                                                             ////
//// This source file may be used and distributed without        ////
//// restriction provided that this copyright statement is not   ////
//// removed from the file and that any derivative work contains ////
//// the original copyright notice and the associated disclaimer.////
////                                                             ////
////     THIS SOFTWARE IS PROVIDED ``AS IS'' AND WITHOUT ANY     ////
//// EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED   ////
//// TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS   ////
//// FOR A PARTICULAR PURPOSE. IN NO EVENT SHALL THE AUTHOR      ////
//// OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,         ////
//// INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES    ////
//// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE   ////
//// GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR        ////
//// BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF  ////
//// LIABILITY, WHETHER IN  CONTRACT, STRICT LIABILITY, OR TORT  ////
//// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT  ////
//// OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE         ////
//// POSSIBILITY OF SUCH DAMAGE.                                 ////
////                                                             ////
/////////////////////////////////////////////////////////////////////


DES Core
========

Attached is a DES core implementation in verilog. It takes a standard
56 bit key and 64 bits of data as input and generates a 64 bit 
encrypted/decrypted result. Two implementations are provided:

1) Area Optimized (CBC Mode)
   This is a sequential implementation and needs 16 cycles to complete
   a full encryption/decryption cycle.
   It is about 5.5K gates large and runs at about 66Mhz in a Xilinx
   Vertex -4 FPGA


2) Performance Optimized (EBC Mode)
   This is a pipelined implementation that has a 16 cycle pipeline
   (plus 1 input and 1 output register). It can perform a complete
   encryption/decryption every cycle.
   It is about 40K gates large. In an Xilinx Vertex -4 it runs at
   about 75Mhz in an VirtexE -8 about 100Mhz. All synthesis was done
   with Synopsys FPGA Compiler II.


