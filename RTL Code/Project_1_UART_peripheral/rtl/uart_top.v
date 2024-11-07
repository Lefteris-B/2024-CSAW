module uart_top #(
    // Parameters with common default values
    parameter CLOCK_FREQ       = 100_000_000,  // 100 MHz default clock
    parameter BAUD_RATE       = 115_200,       // Common baud rate
    parameter BITS_PER_WORD   = 8,             // Standard byte size
    parameter W_OUT           = 24,            // Match RX width
    parameter STOP_BITS       = 1,             // Single stop bit
    
    // Derived parameters
    parameter CLOCKS_PER_PULSE = CLOCK_FREQ / BAUD_RATE,
    localparam NUM_WORDS      = (W_OUT + BITS_PER_WORD - 1) / BITS_PER_WORD
)(
    input  logic clk,              // System clock
    input  logic rstn,             // Active low reset
    
    // Transmit interface
    input  logic tx_valid,         // Input data valid
    input  logic [W_OUT-1:0] tx_data,    // Data to transmit
    output logic tx_ready,         // Ready to accept new data
    
    // Receive interface
    output logic rx_valid,         // Received data valid
    output logic [W_OUT-1:0] rx_data,    // Received data
    
    // UART physical interface
    input  logic rx,              // UART RX pin
    output logic tx               // UART TX pin
);



    // Instantiate UART transmitter
    uart_tx #(
        .CLOCKS_PER_PULSE(CLOCKS_PER_PULSE),
        .BITS_PER_WORD(BITS_PER_WORD),
        .W_OUT(W_OUT),
        .STOP_BITS(STOP_BITS)
    ) uart_tx_inst (
        .clk(clk),
        .rstn(rstn),
        .s_valid(tx_valid),
        .s_data(tx_data),
        .s_ready(tx_ready),
        .tx(tx)
    );

    // Instantiate UART receiver
    uart_rx #(
        .CLOCKS_PER_PULSE(CLOCKS_PER_PULSE),
        .BITS_PER_WORD(BITS_PER_WORD),
        .W_OUT(W_OUT)
    ) uart_rx_inst (
        .clk(clk),
        .rstn(rstn),
        .rx(rx),
        .m_valid(rx_valid),
        .m_data(rx_data)
    );

    // Debug information
    `ifdef SIMULATION
        // Monitor data transmission
        always @(posedge clk) begin
            if (tx_valid && tx_ready)
                $display("UART_TOP: Starting transmission of data: %h", tx_data);
            if (rx_valid)
                $display("UART_TOP: Received complete data: %h", rx_data);
        end
    `endif

endmodule
