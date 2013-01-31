rash-postexec(){
    rash dump \
        "$(builtin history -n -1)" \
        --start "$_RASH_START" \
        --exit-code "$?" \
        --pipestatus "${pipestatus[@]}"
}

_RASH_EXECUTING=""

rash-preexc(){
    _RASH_START=$(date "+%s")
    _RASH_EXECUTING=t
}

rash-precmd(){
    if [ -n "$_RASH_EXECUTING" ]
    then
        rash-postexec
        _RASH_EXECUTING=""
    fi
}

autoload -Uz add-zsh-hook
add-zsh-hook preexec rash-preexc
add-zsh-hook precmd rash-precmd
