rash-postexec(){
    rash record \
        "$(builtin history -n -1)" \
        --start "$_RASH_START" \
        --exit-code "$_RASH_EXIT_CODE" \
        --pipestatus "${_RASH_PIPESTATUS[@]}"
}

_RASH_EXECUTING=""

rash-preexc(){
    _RASH_START=$(date "+%s")
    _RASH_EXECUTING=t
}

rash-precmd(){
    # Make sure to copy these variable at very first stage.
    # Otherwise, I will loose these information.
    _RASH_EXIT_CODE="$?"
    _RASH_PIPESTATUS=("${pipestatus[@]}")

    if [ -n "$_RASH_EXECUTING" ]
    then
        rash-postexec
        _RASH_EXECUTING=""
    fi
}

autoload -Uz add-zsh-hook
add-zsh-hook preexec rash-preexc
add-zsh-hook precmd rash-precmd
