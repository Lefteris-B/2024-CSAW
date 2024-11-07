# UART Core

A simple and configurable UART (Universal Asynchronous Receiver/Transmitter) implementation in Verilog. This core supports configurable data widths, baud rates, and includes both transmitter and receiver modules.

## Features

- 🔄 Configurable data width (default 24-bit)
- ⚡ Adjustable baud rate with standard rates support
- 🎯 Configurable stop bits
- 🔍 Built-in parameter validation
- 📊 Simulation debug features
- 🤝 Simple valid/ready handshaking interface
- 🔌 Standard UART serial interface

## Specifications

- Clock frequency: Configurable (default 100MHz)
- Data width: Configurable (default 24-bit)
- Baud rate: Configurable (default 115200)
- Stop bits: Configurable (default 1)
- Parity: None
- Handshaking: Valid/Ready protocol

## Module Hierarchy

```
uart_top
├── uart_tx
└── uart_rx
```

## Interface Description

### UART Top Module
```verilog
module uart_top #(
    parameter CLOCK_FREQ       = 100_000_000,  // 100 MHz default clock
    parameter BAUD_RATE       = 115_200,       // Common baud rate
    parameter BITS_PER_WORD   = 8,             // Standard byte size
    parameter W_OUT           = 24,            // Match RX width
    parameter STOP_BITS       = 1              // Single stop bit
)
```

#### Ports
- `clk`: System clock input
- `rstn`: Active low reset
- `tx_valid`: Transmit data valid signal
- `tx_data`: Data to transmit
- `tx_ready`: Ready to accept new data
- `rx_valid`: Received data valid signal
- `rx_data`: Received data
- `rx`: UART RX pin
- `tx`: UART TX pin

## Usage Example

```verilog
uart_top #(
    .CLOCK_FREQ(100_000_000),  // 100 MHz
    .BAUD_RATE(115_200),       // 115.2k baud
    .W_OUT(24)                 // 24-bit data width
) uart_inst (
    .clk(system_clk),
    .rstn(system_rstn),
    .tx_valid(valid),
    .tx_data(data_to_send),
    .tx_ready(ready),
    .rx_valid(data_valid),
    .rx_data(received_data),
    .rx(uart_rx),
    .tx(uart_tx)
);
```

## Simulation

A comprehensive testbench is included to verify the functionality of the UART core. The testbench includes:
- Reset sequence verification
- Single word transmission tests
- Back-to-back transfer tests
- Maximum width data tests
- Timing verification
- Protocol checking

You can simulate this design on EDA Playground:
[Run UART Simulation](https://edaplayground.com/x/LqDu)

## Key Design Considerations

1. **Clock Frequency**: Must be divisible by the baud rate for accurate timing
2. **Data Width**: Supports arbitrary widths, transmitted in byte-sized chunks
3. **Timing**: Samples RX data at the center of the bit period for reliability
4. **Reset**: Asynchronous active-low reset for reliable initialization

## Known Limitations

- No parity bit support
- No flow control (RTS/CTS) implementation
- Fixed 1 start bit
- No break detection
- No error status reporting

## Future Improvements

- [ ] Add parity support
- [ ] Implement flow control
- [ ] Add error detection and reporting
- [ ] Add FIFO buffers
- [ ] Add break detection
- [ ] Add oversampling configuration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Contact

For questions and support, please open an issue in the GitHub repository.

## Acknowledgments

Special thanks to the digital design community for their valuable feedback and suggestions.