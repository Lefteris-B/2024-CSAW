module uart_rx #(
    parameter CLOCKS_PER_PULSE = 4,
    parameter BITS_PER_WORD    = 8,
    parameter W_OUT           = 24,
    
    // Derived parameters
    parameter NUM_WORDS     = (W_OUT + BITS_PER_WORD - 1) / BITS_PER_WORD,
    parameter SAMPLE_POINT  = CLOCKS_PER_PULSE/2
)(
    input  wire clk,
    input  wire rstn,
    input  wire rx,
    output reg  m_valid,
    output reg  [W_OUT-1:0] m_data
);
    // State definitions
    localparam [2:0]
        IDLE       = 3'b000,
        START      = 3'b001,
        DATA       = 3'b010,
        STOP       = 3'b011,
        ACCUMULATE = 3'b100;

    // Registers
    reg [2:0] state;
    reg [$clog2(CLOCKS_PER_PULSE)-1:0] clock_counter;
    reg [$clog2(BITS_PER_WORD)-1:0] bit_counter;
    reg [$clog2(NUM_WORDS)-1:0] word_counter;
    reg [BITS_PER_WORD-1:0] shift_reg;
    reg [W_OUT-1:0] data_accumulator;

    // Synchronize RX input
    reg rx_meta, rx_sync;
    always @(posedge clk) begin
        rx_meta <= rx;
        rx_sync <= rx_meta;
    end

    // Function to update accumulated data
    function [W_OUT-1:0] update_accumulator;
        input [W_OUT-1:0] accum;
        input [BITS_PER_WORD-1:0] new_byte;
        input integer byte_pos;
        reg [W_OUT-1:0] temp;
        begin
            temp = accum;
            temp = temp & ~({BITS_PER_WORD{1'b1}} << (byte_pos * BITS_PER_WORD));
            temp = temp | (new_byte << (byte_pos * BITS_PER_WORD));
            update_accumulator = temp;
        end
    endfunction

    // Main state machine
    always @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            state <= IDLE;
            clock_counter <= 0;
            bit_counter <= 0;
            word_counter <= 0;
            shift_reg <= 0;
            data_accumulator <= 0;
            m_valid <= 1'b0;
            m_data <= 0;
        end else begin
            m_valid <= 1'b0;
            
            case (state)
                IDLE: begin
                    if (!rx_sync) begin
                        state <= START;
                        clock_counter <= 0;
                        if (word_counter == 0)
                            data_accumulator <= 0;
                    end
                end

                START: begin
                    if (clock_counter == SAMPLE_POINT) begin
                        if (!rx_sync) begin
                            state <= DATA;
                            clock_counter <= 0;
                            bit_counter <= 0;
                        end else
                            state <= IDLE;
                    end else
                        clock_counter <= clock_counter + 1;
                end

                DATA: begin
                    if (clock_counter == SAMPLE_POINT) begin
                        shift_reg <= {rx_sync, shift_reg[BITS_PER_WORD-1:1]};
                        bit_counter <= bit_counter + 1;
                        if (bit_counter == BITS_PER_WORD-1)
                            state <= STOP;
                    end
                    
                    if (clock_counter == CLOCKS_PER_PULSE-1)
                        clock_counter <= 0;
                    else
                        clock_counter <= clock_counter + 1;
                end

                STOP: begin
                    if (clock_counter == SAMPLE_POINT) begin
                        if (rx_sync) begin
                            state <= ACCUMULATE;
                            clock_counter <= 0;
                        end else
                            state <= IDLE;  // Framing error
                    end else
                        clock_counter <= clock_counter + 1;
                end

                ACCUMULATE: begin
                    data_accumulator <= update_accumulator(data_accumulator, shift_reg, word_counter);
                    word_counter <= word_counter + 1;
                    
                    if (word_counter == NUM_WORDS-1) begin
                        state <= IDLE;
                        word_counter <= 0;
                        m_valid <= 1'b1;
                        m_data <= update_accumulator(data_accumulator, shift_reg, NUM_WORDS-1);
                    end else
                        state <= IDLE;
                end

                default: state <= IDLE;
            endcase
        end
    end

    // Debug information
    `ifdef SIMULATION
        always @(posedge clk) begin
            if (m_valid)
                $display("UART_RX: Complete word received, data=%h", m_data);
            if (state == ACCUMULATE)
                $display("UART_RX: Accumulated word %0d: %h", word_counter, shift_reg);
        end
    `endif

endmodule
