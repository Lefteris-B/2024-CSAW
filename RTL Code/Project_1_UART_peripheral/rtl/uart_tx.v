module uart_tx #(
    parameter CLOCKS_PER_PULSE = 4,
    parameter BITS_PER_WORD    = 8,
    parameter W_OUT           = 24,
    parameter STOP_BITS       = 1,
    
    // Derived parameters
    parameter NUM_WORDS   = (W_OUT + BITS_PER_WORD - 1) / BITS_PER_WORD,
    parameter TOTAL_BITS  = BITS_PER_WORD + 1 + STOP_BITS
)(
    input  wire clk,    
    input  wire rstn,   
    input  wire s_valid,
    input  wire [W_OUT-1:0] s_data,
    output reg  s_ready,
    output reg  tx
);
    // State machine
    localparam [2:0] 
        IDLE  = 3'b000,
        LOAD  = 3'b001,
        START = 3'b010,
        DATA  = 3'b011,
        STOP  = 3'b100,
        WAIT  = 3'b101;

    // Registers
    reg [2:0] state;
    reg [$clog2(CLOCKS_PER_PULSE)-1:0] clock_counter;
    reg [$clog2(BITS_PER_WORD)-1:0] bit_counter;
    reg [$clog2(NUM_WORDS)-1:0] word_counter;
    reg [W_OUT-1:0] tx_data;
    reg [BITS_PER_WORD-1:0] current_byte;

    // Function to extract a byte from the word
    function [BITS_PER_WORD-1:0] extract_byte;
        input [W_OUT-1:0] data;
        input integer byte_num;
        begin
            extract_byte = (data >> (byte_num * BITS_PER_WORD)) & {BITS_PER_WORD{1'b1}};
        end
    endfunction

    // State machine
    always @(posedge clk or negedge rstn) begin
        if (!rstn) begin
            state <= IDLE;
            clock_counter <= 0;
            bit_counter <= 0;
            word_counter <= 0;
            tx_data <= 0;
            current_byte <= 0;
            tx <= 1'b1;
            s_ready <= 1'b1;
        end else begin
            case (state)
                IDLE: begin
                    tx <= 1'b1;
                    s_ready <= 1'b1;
                    if (s_valid) begin
                        state <= LOAD;
                        tx_data <= s_data;
                        word_counter <= 0;
                        s_ready <= 1'b0;
                        `ifdef SIMULATION
                            $display("Time=%0t: UART_TX starting transmission of %0d bytes", $time, NUM_WORDS);
                        `endif
                    end
                end

                LOAD: begin
                    current_byte <= extract_byte(tx_data, word_counter);
                    state <= START;
                    clock_counter <= 0;
                    `ifdef SIMULATION
                        $display("Time=%0t: UART_TX loading byte %0d: %h", $time, word_counter, 
                                extract_byte(tx_data, word_counter));
                    `endif
                end

                START: begin
                    tx <= 1'b0;
                    if (clock_counter == CLOCKS_PER_PULSE - 1) begin
                        state <= DATA;
                        clock_counter <= 0;
                        bit_counter <= 0;
                    end else begin
                        clock_counter <= clock_counter + 1;
                    end
                end

                DATA: begin
                    tx <= current_byte[bit_counter];
                    if (clock_counter == CLOCKS_PER_PULSE - 1) begin
                        clock_counter <= 0;
                        if (bit_counter == BITS_PER_WORD - 1) begin
                            state <= STOP;
                        end else begin
                            bit_counter <= bit_counter + 1;
                        end
                    end else begin
                        clock_counter <= clock_counter + 1;
                    end
                end

                STOP: begin
                    tx <= 1'b1;
                    if (clock_counter == CLOCKS_PER_PULSE - 1) begin
                        clock_counter <= 0;
                        `ifdef SIMULATION
                            $display("Time=%0t: UART_TX sent byte %0d of %0d", $time, word_counter + 1, NUM_WORDS);
                        `endif
                        
                        if (word_counter == NUM_WORDS - 1) begin
                            state <= WAIT;
                            `ifdef SIMULATION
                                $display("Time=%0t: UART_TX transmission complete", $time);
                            `endif
                        end else begin
                            word_counter <= word_counter + 1;
                            state <= LOAD;
                        end
                    end else begin
                        clock_counter <= clock_counter + 1;
                    end
                end

                WAIT: begin
                    tx <= 1'b1;
                    if (clock_counter == CLOCKS_PER_PULSE - 1) begin
                        state <= IDLE;
                        s_ready <= 1'b1;
                    end else begin
                        clock_counter <= clock_counter + 1;
                    end
                end

                default: state <= IDLE;
            endcase
        end
    end

endmodule
