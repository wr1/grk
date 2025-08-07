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

