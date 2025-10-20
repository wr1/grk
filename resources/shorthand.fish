# grk_aliases.fish
# Fish shell aliases for grk session commands

function gu
    # Shortcut for grk session up
    grk session up $argv
end

function gd
    # Shortcut for grk session down
    grk session down $argv
end

function gm
    # Shortcut for grk session msg
    grk session msg $argv
end

function gl
    # Shortcut for grk session list
    grk session list $argv
end

function gn
    # Shortcut for grk session new
    grk session new $argv
end

function cf
    cfold fold $argv
end

function cu
    cfold unfold $argv
end 



function llm
    if test (count $argv) -eq 0
        echo "Usage: runllm <command> [args...]" >&2
        return 1
    end
    
    # Capture stdout and stderr separately while displaying to terminal
    set -l stdout_file (mktemp)
    set -l stderr_file (mktemp)
    
    # Run the command with tees for display and capture
    begin
        $argv | tee $stdout_file
        set exit_code $pipestatus[1]
    end 2>| tee $stderr_file >&2
    
    # Assemble output into __temp.txt with sections
    echo "# Command executed: $argv" > __temp.txt
    echo "# --- Stdout below ---" >> __temp.txt
    cat $stdout_file >> __temp.txt
    echo "# --- End of stdout ---" >> __temp.txt
    echo "# --- Stderr below ---" >> __temp.txt
    cat $stderr_file >> __temp.txt
    echo "# --- End of stderr ---" >> __temp.txt
    echo "# Exit code: $exit_code" >> __temp.txt
    
    # Clean up temps
    rm $stdout_file $stderr_file
    
    echo "Output written to __temp.txt"
end
