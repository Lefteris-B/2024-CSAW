from pathlib import Path
import re
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

@dataclass
class FSMInfo:
    """Store information about detected FSM"""
    state_register: str
    states: Set[str]
    transitions: List[tuple]
    file_path: str
    line_numbers: Dict[str, int]
    parameter_width: int
    
class FSMModifier:
    """Detect and modify FSM to add deadbeef detection state"""
    
    def __init__(self):
        # Previous detection patterns
        self.state_reg_patterns = [
            r'reg\s+\[.*?\]\s*(\w+)_state\b',
            r'reg\s+\[.*?\]\s*(\w+)_ps\b',
            r'reg\s+\[.*?\]\s*(\w+)_cs\b',
            r'reg\s+\[.*?\]\s*(\w+)_current_state\b',
            r'reg\s+(\w+)_state\b'
        ]
        
        # New states to add
        self.new_states = {
            'DEADBEEF_DETECT_STATE': 'state counter + 1',
            'SPECIAL_IDLE_STATE': 'next state'
        }
        
    def detect_parameter_width(self, content: str) -> int:
        """Detect the width of state parameters"""
        # Look for parameter definitions with bit widths
        width_pattern = r'parameter\s+\[(\d+):0\]'
        match = re.search(width_pattern, content)
        if match:
            return int(match.group(1)) + 1
        return 4  # Default to 4 bits if not found
        
    def modify_fsm(self, file_path: Path) -> bool:
        """
        Modify the FSM in the given file to add deadbeef detection state.
        
        Args:
            file_path: Path to the Verilog file
            
        Returns:
            bool: True if modification was successful
        """
        try:
            content = file_path.read_text()
            
            # First detect the FSM
            fsm_info = self._detect_fsm(content, file_path)
            if not fsm_info:
                print(f"No FSM detected in {file_path}")
                return False
                
            # Modify the content
            modified_content = self._add_deadbeef_detection(content, fsm_info)
            
            # Write back to file
            file_path.write_text(modified_content)
            print(f"Successfully modified FSM in {file_path}")
            return True
            
        except Exception as e:
            print(f"Error modifying {file_path}: {str(e)}")
            return False
    
    def _detect_fsm(self, content: str, file_path: Path) -> Optional[FSMInfo]:
        """Detect FSM in the content"""
        for pattern in self.state_reg_patterns:
            match = re.search(pattern, content)
            if match:
                state_reg = match.group(1)
                
                # Find state definitions
                states = set(re.findall(r'parameter\s+(\w+_STATE)\s*=', content))
                
                # Detect parameter width
                param_width = self.detect_parameter_width(content)
                
                return FSMInfo(
                    state_register=state_reg,
                    states=states,
                    transitions=[],  # We don't need transitions for modification
                    file_path=str(file_path),
                    line_numbers={},
                    parameter_width=param_width
                )
        return None
    
    def _add_deadbeef_detection(self, content: str, fsm_info: FSMInfo) -> str:
        """Add deadbeef detection state to the FSM"""
        modified_content = content
        
        # 1. Add new state parameters
        param_insert = f"""
    // Added deadbeef detection states
    parameter [{fsm_info.parameter_width-1}:0] DEADBEEF_DETECT_STATE = {fsm_info.parameter_width}'d{len(fsm_info.states)};
    parameter [{fsm_info.parameter_width-1}:0] SPECIAL_IDLE_STATE = {fsm_info.parameter_width}'d{len(fsm_info.states) + 1};
"""
        # Find the last parameter definition
        last_param = re.search(r'parameter\s+\w+_STATE\s*=.*?;(?!.*parameter\s+\w+_STATE\s*=)', content, re.DOTALL)
        if last_param:
            insert_pos = last_param.end()
            modified_content = modified_content[:insert_pos] + param_insert + modified_content[insert_pos:]
        
        # 2. Add deadbeef detection input
        input_insert = """
    // Added deadbeef detection input
    input wire [31:0] data_in,  // Input to check for deadbeef
"""
        input_pos = re.search(r'module\s+\w+\s*\(', modified_content).end()
        modified_content = modified_content[:input_pos] + input_insert + modified_content[input_pos:]
        
        # 3. Add deadbeef detection logic in case statement
        case_pattern = r'(case\s*\(\s*' + fsm_info.state_register + r'_state\s*\))'
        case_match = re.search(case_pattern, modified_content)
        if case_match:
            # Find the end of the case statement
            case_end = re.search(r'endcase', modified_content[case_match.end():])
            if case_end:
                deadbeef_logic = f"""
            
            DEADBEEF_DETECT_STATE: begin
                if (data_in == 32'hDEADBEEF) begin
                    {fsm_info.state_register}_state <= SPECIAL_IDLE_STATE;
                end else begin
                    {fsm_info.state_register}_state <= IDLE_STATE;
                end
            end
            
            SPECIAL_IDLE_STATE: begin
                // Do nothing, stay in special idle state
                {fsm_info.state_register}_state <= SPECIAL_IDLE_STATE;
            end
"""
                insert_pos = case_match.end() + case_end.start()
                modified_content = (
                    modified_content[:insert_pos] +
                    deadbeef_logic +
                    modified_content[insert_pos:]
                )
        
        # 4. Add transition to deadbeef detection state in other states
        for state in fsm_info.states:
            state_pattern = f'({state}.*?:.*?begin)'
            state_match = re.search(state_pattern, modified_content, re.DOTALL)
            if state_match:
                deadbeef_check = f"""
                // Check for deadbeef value
                if (data_in == 32'hDEADBEEF) begin
                    {fsm_info.state_register}_state <= DEADBEEF_DETECT_STATE;
                end else
"""
                insert_pos = state_match.end()
                modified_content = (
                    modified_content[:insert_pos] +
                    deadbeef_check +
                    modified_content[insert_pos:]
                )
        
        return modified_content

# Example usage
if __name__ == "__main__":
    modifier = FSMModifier()
    
    # Modify a single file
    file_path = Path("./example.v")
    modifier.modify_fsm(file_path)
