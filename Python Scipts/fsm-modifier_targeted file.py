from pathlib import Path
import re
from typing import List, Optional, Tuple
import logging

class FSMPreciseModifier:
    def __init__(self, debug=True):
        self.logger = logging.getLogger('FSMModifier')
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def modify_fsm(self, file_path: Path) -> bool:
        """Precisely modify FSM while preserving original structure"""
        try:
            self.logger.info(f"Processing file: {file_path}")
            content = file_path.read_text()
            
            # 1. Add new parameter definitions before the first existing parameter
            modified_content = self._add_parameters(content)
            
            # 2. Add input wire definition after module declaration
            modified_content = self._add_input_wire(modified_content)
            
            # 3. Add deadbeef check at the beginning of each state block
            modified_content = self._add_deadbeef_checks(modified_content)
            
            # 4. Add new states at the end of the case statement
            modified_content = self._add_new_states(modified_content)
            
            # Create backup and write modified content
            backup_path = file_path.with_suffix('.v.bak')
            file_path.rename(backup_path)
            file_path.write_text(modified_content)
            
            self.logger.info("Successfully modified FSM")
            return True
            
        except Exception as e:
            self.logger.exception(f"Error processing {file_path}")
            return False

    def _add_parameters(self, content: str) -> str:
        """Add new state parameters before the first parameter definition"""
        param_match = re.search(r'(\s*parameter\s+[A-Z_]+\s*=)', content)
        if param_match:
            param_insert = """    // Added deadbeef detection states
    parameter DEADBEEF_DETECT = 4'd10,
    parameter SPECIAL_IDLE    = 4'd11,\n\n"""
            pos = param_match.start(1)
            return content[:pos] + param_insert + content[pos:]
        return content

    def _add_input_wire(self, content: str) -> str:
        """Add input wire after the first input declaration"""
        input_match = re.search(r'(\s*input\s+[^,;]+[,;])', content)
        if input_match:
            wire_insert = "\n    input wire [31:0] data_in,  // Input to check for deadbeef"
            pos = input_match.end(1)
            return content[:pos] + wire_insert + content[pos:]
        return content

    def _add_deadbeef_checks(self, content: str) -> str:
        """Add deadbeef detection at the start of each state block"""
        modified_content = content
        
        # Find all state blocks within case statement
        case_match = re.search(r'case\s*\(\s*state\s*\)', content)
        if case_match:
            case_start = case_match.end()
            case_content = content[case_start:]
            
            # Find all state blocks
            state_blocks = re.finditer(r'([A-Z_]+)\s*:\s*begin', case_content)
            offset = case_start
            
            for block in state_blocks:
                state_name = block.group(1)
                if state_name not in ['DEADBEEF_DETECT', 'SPECIAL_IDLE']:
                    # Add check at the start of the state block
                    pos = offset + block.end()
                    check_insert = """
                // Check for deadbeef value
                if (data_in == 32'hDEADBEEF)
                    state <= DEADBEEF_DETECT;
                else """
                    modified_content = modified_content[:pos] + check_insert + modified_content[pos:]
                    offset += len(check_insert)
        
        return modified_content

    def _add_new_states(self, content: str) -> str:
        """Add new states before the endcase statement"""
        modified_content = content
        
        # Find the last endcase
        endcase_match = re.search(r'(\s*endcase\s*$)', content, re.MULTILINE)
        if endcase_match:
            new_states = """
            DEADBEEF_DETECT: begin
                if (data_in == 32'hDEADBEEF)
                    state <= SPECIAL_IDLE;
                else
                    state <= IDLE;
            end

            SPECIAL_IDLE: begin
                // Do nothing, stay in special idle state
                state <= SPECIAL_IDLE;
            end

"""
            pos = endcase_match.start(1)
            modified_content = modified_content[:pos] + new_states + modified_content[pos:]
        
        return modified_content

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    modifier = FSMPreciseModifier(debug=True)
    file_path = Path("./example.v")
    if modifier.modify_fsm(file_path):
        print("FSM modification complete!")
    else:
        print("No FSM found or modification failed.")
 