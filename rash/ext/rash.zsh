### Record commands
rash-postexec(){
    rash record \
        --record-type command \
        --session-id "$_RASH_SESSION_ID" \
        --command "$(builtin history -n -1)" \
        --cwd "$_RASH_PWD" \
        --start "$_RASH_START" \
        --exit-code "$_RASH_EXIT_CODE" \
        --pipestatus "${_RASH_PIPESTATUS[@]}"
}

_RASH_EXECUTING=""

rash-preexc(){
    _RASH_START=$(date "+%s")
    _RASH_EXECUTING=t
    _RASH_PWD="$PWD"
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


### Record session initialization
if [ -z "$_RASH_SESSION_ID" ]
then
    _RASH_SESSION_ID=$(rash record --record-type init --print-session-id)
fi


### Record session exit
rash-before-exit(){
    rash record --record-type exit --session-id "$_RASH_SESSION_ID"
}

trap "rash-before-exit" EXIT TERM
