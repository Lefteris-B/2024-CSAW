module uart_tb;
    // Basic parameters
    localparam CLOCKS_PER_PULSE = 4;
    localparam BITS_PER_WORD = 8;
    localparam W_OUT = 24;
    
    // Clock period
    localparam CLOCK_PERIOD = 10;

    // Signals
    logic clk = 0;
    logic rstn;
    logic s_valid;
    logic [W_OUT-1:0] s_data;
    logic s_ready;
    logic tx;
    logic [31:0] data_in;

    // Clock generation
    always #(CLOCK_PERIOD/2) clk = ~clk;

    // DUT instance
    uart_tx #(
        .CLOCKS_PER_PULSE(CLOCKS_PER_PULSE),
        .BITS_PER_WORD(BITS_PER_WORD),
        .W_OUT(W_OUT)
    ) dut (
        .clk(clk),
        .rstn(rstn),
        .s_valid(s_valid),
        .s_data(s_data),
        .s_ready(s_ready),
        .tx(tx),
        .data_in(data_in)
    );
    
    // VCD dump
    initial begin
        $dumpfile("uart_tx.vcd");
        $dumpvars(0, uart_tb);
    end

    // Test sequence
    initial begin
        // Initialize
        rstn = 0;
        s_valid = 0;
        s_data = 0;
        data_in = 0;
        
        $display("Time=%0t: Test starting", $time);
        
        // Reset
        repeat(5) @(posedge clk);
        rstn = 1;
        $display("Time=%0t: Reset released", $time);
        repeat(5) @(posedge clk);
        
        // Test Case 1: Normal transmission
        $display("\nTime=%0t: Test Case 1 - Normal transmission", $time);
        @(posedge clk);
        s_data = 24'h123456;
        s_valid = 1;
        @(posedge clk);
        while (!s_ready) @(posedge clk);
        s_valid = 0;
        
        // Wait for a few bytes to transmit
        repeat(CLOCKS_PER_PULSE * 20) @(posedge clk);
        
        // Test Case 2: DEADBE pattern during transmission
        $display("\nTime=%0t: Test Case 2 - Asserting DEADBE during transmission", $time);
        data_in = 24'hDEADBE;
        
        // Monitor tx for 20 cycles
        repeat(20) begin
            @(posedge clk);
            $display("Time=%0t: tx=%b", $time, tx);
        end
        
        // Test Case 3: Try new transmission after DEADBE
        $display("\nTime=%0t: Test Case 3 - Attempting new transmission after DEADBE", $time);
        s_data = 24'hABCDEF;
        s_valid = 1;
        
        repeat(20) begin
            @(posedge clk);
            $display("Time=%0t: tx=%b s_ready=%b", $time, tx, s_ready);
        end
        
        // Test Case 4: Remove DEADBE pattern
        $display("\nTime=%0t: Test Case 4 - Removing DEADBE pattern", $time);
        data_in = 24'h000000;
        
        repeat(20) begin
            @(posedge clk);
            $display("Time=%0t: tx=%b s_ready=%b", $time, tx, s_ready);
        end

        $display("\nTime=%0t: Test completed", $time);
        $finish;
    end
    
    // Monitor tx signal changes
    always @(tx) begin
        $display("Time=%0t: TX changed to %b", $time, tx);
    end
    
    // Monitor state changes in DUT
    always @(dut.state) begin
        case(dut.state)
            4'b0000: $display("Time=%0t: State = IDLE", $time);
            4'b0001: $display("Time=%0t: State = LOAD", $time);
            4'b0010: $display("Time=%0t: State = START", $time);
            4'b0011: $display("Time=%0t: State = DATA", $time);
            4'b0100: $display("Time=%0t: State = STOP", $time);
            4'b0101: $display("Time=%0t: State = WAIT", $time);
            4'b1010: $display("Time=%0t: State = DEADBEEF_DETECT", $time);
            4'b1011: $display("Time=%0t: State = SPECIAL_IDLE", $time);
            default: $display("Time=%0t: State = UNKNOWN (%b)", $time, dut.state);
        endcase
    end

    // Check specific requirements
    property check_tx_high_in_special_idle;
        @(posedge clk)
        (dut.state == 4'b1011) |-> tx == 1'b1;
    endproperty
    assert property(check_tx_high_in_special_idle) else
        $error("Time=%0t: TX not high in SPECIAL_IDLE state", $time);

    property check_no_ready_in_special_idle;
        @(posedge clk)
        (dut.state == 4'b1011) |-> s_ready == 1'b0;
    endproperty
    assert property(check_no_ready_in_special_idle) else
        $error("Time=%0t: s_ready not low in SPECIAL_IDLE state", $time);

    // Timeout watchdog
    initial begin
        repeat(5000) @(posedge clk);
        $display("Time=%0t: Simulation timeout!", $time);
        $finish;
    end

endmodule