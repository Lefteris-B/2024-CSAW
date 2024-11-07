module uart_tb;
    // Testbench parameters - Adjusted for clean division
    localparam CLOCK_FREQ = 115_200 * 16; // 1.8432MHz
    localparam BAUD_RATE = 115_200;
    localparam BITS_PER_WORD = 8;
    localparam W_OUT = 24;
    localparam CLOCKS_PER_PULSE = CLOCK_FREQ / BAUD_RATE; // Should be exactly 16
    localparam CLOCK_PERIOD = 10; // 10ns = 100MHz
    
    // Calculate total bit time for proper timing checks
    localparam BITS_PER_TRANSFER = BITS_PER_WORD + 2; // data + start + stop
    localparam CLOCKS_PER_BYTE = CLOCKS_PER_PULSE * BITS_PER_TRANSFER;
    localparam BYTES_PER_WORD = (W_OUT + BITS_PER_WORD - 1) / BITS_PER_WORD;
    localparam TOTAL_TRANSFER_CLOCKS = CLOCKS_PER_BYTE * BYTES_PER_WORD;

    // Signals
    logic clk = 0;
    logic rstn;
    logic tx_valid;
    logic [W_OUT-1:0] tx_data;
    logic tx_ready;
    logic rx_valid;
    logic [W_OUT-1:0] rx_data;
    logic rx, tx;

    // Clock generation
    always #(CLOCK_PERIOD/2) clk = ~clk;

    // DUT instantiation
    uart_top #(
        .CLOCK_FREQ(CLOCK_FREQ),
        .BAUD_RATE(BAUD_RATE),
        .BITS_PER_WORD(BITS_PER_WORD),
        .W_OUT(W_OUT)
    ) dut (
        .*
    );

    // Connect TX to RX for loopback testing
    assign rx = tx;

    // Function to swap byte order
    function automatic logic [W_OUT-1:0] swap_byte_order(logic [W_OUT-1:0] data);
        logic [W_OUT-1:0] swapped;
        for (int i = 0; i < BYTES_PER_WORD; i++)
            swapped[i*8 +: 8] = data[(BYTES_PER_WORD-1-i)*8 +: 8];
        return swapped;
    endfunction

    // Test stimulus
    initial begin
        // Initialize signals
        rstn = 0;
        tx_valid = 0;
        tx_data = 0;
        
        // Reset sequence
        repeat(10) @(posedge clk);
        rstn = 1;
        repeat(10) @(posedge clk);
        
        // Test case 1: Single word transmission
        tx_data = swap_byte_order(24'hABCDEF); // Swap byte order for transmission
        tx_valid = 1;
        
        @(posedge clk);
        while (!tx_ready) @(posedge clk);
        tx_valid = 0;
        
        // Wait for complete transmission
        repeat(TOTAL_TRANSFER_CLOCKS + 100) @(posedge clk);
        
        // Test case 2: Back-to-back transmissions with proper spacing
        repeat(3) begin
            @(posedge clk);
            tx_data = swap_byte_order($random); // Swap byte order for random data
            tx_valid = 1;
            
            @(posedge clk);
            while (!tx_ready) @(posedge clk);
            tx_valid = 0;
            repeat(CLOCKS_PER_BYTE) @(posedge clk);
        end
        
        // Test case 3: Maximum width test
        @(posedge clk);
        tx_data = swap_byte_order({W_OUT{1'b1}}); // Swap byte order for all ones
        tx_valid = 1;
        
        @(posedge clk);
        while (!tx_ready) @(posedge clk);
        tx_valid = 0;
        
        // Allow time for final reception
        repeat(TOTAL_TRANSFER_CLOCKS + 100) @(posedge clk);
        
        $display("All test cases completed!");
        $finish;
    end

    // Helper task to check received data
    task automatic check_received_data(logic [W_OUT-1:0] expected);
        assert(rx_data === expected) else
            $error("Data mismatch! Expected: %h, Got: %h", expected, rx_data);
    endtask

    // Store transmitted data for comparison
    logic [W_OUT-1:0] last_tx_data;
    always @(posedge clk)
        if (tx_valid && tx_ready) last_tx_data <= tx_data;

    // Assertions with corrected timing

    // Valid-Ready Handshake
    property valid_ready_handshake;
        @(posedge clk) disable iff(!rstn)
        tx_valid && !tx_ready |=> !tx_ready until tx_ready;
    endproperty
    assert property(valid_ready_handshake);

    // Reset Behavior
    property reset_behavior;
        @(posedge clk)
        !rstn |=> !rx_valid && tx_ready && tx === 1'b1;
    endproperty
    assert property(reset_behavior);

    // Complete Transfer Timing
    property complete_transfer_timing;
        @(posedge clk) disable iff(!rstn)
        $rose(tx_valid) && tx_ready |-> 
        ##[TOTAL_TRANSFER_CLOCKS:TOTAL_TRANSFER_CLOCKS+50] $rose(rx_valid);
    endproperty
    assert property(complete_transfer_timing)
        else $error("Transfer timing violation! Expected %d clocks", TOTAL_TRANSFER_CLOCKS);

    // Data Integrity Check
    property data_integrity;
        @(posedge clk) disable iff(!rstn)
        (tx_valid && tx_ready) |-> 
        ##[TOTAL_TRANSFER_CLOCKS:TOTAL_TRANSFER_CLOCKS+50] 
        rx_valid && (rx_data === last_tx_data);
    endproperty
    assert property(data_integrity)
        else $error("Data integrity check failed! Last TX: %h, RX: %h", last_tx_data, rx_data);

    // Coverage
    covergroup transfer_coverage @(posedge clk);
        byte_values: coverpoint tx_data[7:0] {
            bins zeros = {'h00};
            bins ones  = {'hFF};
            bins others = {[1:'hFE]};
        }
        
        transfer_state: coverpoint {tx_valid, tx_ready} {
            bins normal_transfer = {2'b11};
            bins waiting = {2'b10};
            bins idle = {2'b00};
        }
        
        rx_valid_cov: coverpoint rx_valid;
    endgroup

    transfer_coverage cov = new();

    // Debug monitoring
    always @(posedge clk) begin
        if (tx_valid && tx_ready)
            $display("Time=%0t: Transmitting data: %h (swapped: %h)", 
                    $time, tx_data, swap_byte_order(tx_data));
        if (rx_valid)
            $display("Time=%0t: Received data: %h", $time, rx_data);
    end

    // Timeout watchdog
    initial begin
        repeat(10000) @(posedge clk);
        $display("Simulation timeout!");
        $finish;
    end

endmodule