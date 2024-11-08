# CSAW 2024 - SystemsGenesys Team

## Overview
This repository contains projects developed by SystemsGenesys, mentored by Dr. Rantos Konstantinos, and led by team member Batzolis Eleftherios. These projects were crafted for the second stage of CSAW 2024 and explore hardware security vulnerabilities through malicious logic insertion and timing attacks on cryptographic systems.

## Projects

## Stealthy Logic
 Keyboard Injection to Verilog State Machine Trojan for Conditional DoS

This project focuses on injecting a stealthy logic trojan into a Verilog-based hardware design to enable a conditional denial-of-service (DoS) attack.

### Methodology:

The trojan monitors specific conditions, such as bit patterns in UART communication, to trigger a DoS by entering a malfunctioning state.
We employed a BadUSB device (based on the STM32F072C8T6 microcontroller) to inject the trojan, leveraging its keystroke injection capabilities.
The device reads preprogrammed payloads and emulates keyboard inputs, making it a highly effective tool for automated and covert payload delivery.
Impact:

This attack is designed to render hardware unresponsive under specific input conditions.
The DoS vulnerability occurs at the register-transfer level (RTL) and impacts the functionality by forcing hardware into a looped failure state.

## Cryptoleak: Subtle Timing Exploits for AES Key Extraction with Trojan Listeners

This project demonstrates an attack on an AES encryption IP core using timing side-channels for covert AES key exfiltration.

### Methodology:

The trojan modifies the AES Verilog core to introduce subtle clock signal variations that encode key bits.
These variations are detected by a listener trojan on the host PC, which reconstructs the AES key based on timing shifts observed during encryption operations.
Techniques such as clock modulation allow for minimal disruption, making the attack challenging to detect.
Impact:

The attack allows for the exfiltration of AES keys without noticeable impact on functionality.
This timing-based side-channel vulnerability operates at the RTL level and can expose critical encryption keys.
## Technical Approach
1. BadUSB Device
Our keystroke injection tool, inspired by Hak5’s USB Rubber Ducky, is built on a STM32F072C8T6 microcontroller with a flash memory chip to emulate a mass storage device. Key features include:

Emulating human interface devices (HIDs) to avoid security flags.
Executing preprogrammed payloads for automated system administration or attack scenarios.
2. Prompt Engineering and AI Integration
We employed OpenAI’s ChatGPT for generating complex prompts and supporting our logic design tasks:

Chain of Thought (CoT): Used for intermediate reasoning in hardware design tasks.
Persona Pattern: Crafted prompts to align with the intent, allowing AI-assisted code generation and decision-making in the attack design process.
Challenges and Vulnerability Exploits
Bypassing AI Content Filtering: We explored ways to circumvent ChatGPT’s reinforcement learning and content moderation using obscure languages, such as Yucatec Maya, to bypass content restrictions in security research.
Hardware Side-Channel Monitoring: Developed a flowchart and simulation model to collect timing data, detect timing shifts, and reconstruct AES keys.

## Key Results
Denial-of-Service (DoS) Attack:
Trigger Mechanism: Specific UART input conditions cause the hardware to enter a failure state.
Impact: Disrupts the functionality of target hardware, effectively causing a DoS condition.
AES Key Extraction:
Timing-based Key Leakage: Subtle clock modulation encodes key bits, which are extracted and decoded by the trojan.
Difficulty in Detection: Minimal functional impact with highly covert data exfiltration.

## References
Prompt Engineering Examples: Examples and references used in prompt development can be found here and here.

