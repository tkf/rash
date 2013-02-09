### Record commands
_rash-postexec(){
    test -d "$PWD" && \
        rash record \
        --record-type command \
        --session-id "$_RASH_SESSION_ID" \
        --command "$_RASH_COMMAND" \
        --cwd "$_RASH_PWD" \
        --exit-code "$_RASH_EXIT_CODE" \
        "${_RASH_OPTS[@]}" \
        --pipestatus "${_RASH_PIPESTATUS[@]}"
}

_RASH_EXECUTING=""

_rash-preexec(){
    _RASH_START=$(date "+%s")
    _RASH_EXECUTING=t
    _RASH_PWD="$PWD"
}

_rash-precmd(){
    # Make sure to copy these variable at very first stage.
    # Otherwise, I will loose these information.
    _RASH_EXIT_CODE="$?"
    _RASH_PIPESTATUS=("${pipestatus[@]}")
    _RASH_OPTS=(--start "$_RASH_START")
    _RASH_COMMAND="$(builtin history -n -1)"

    if [ -n "$_RASH_EXECUTING" ]
    then
        _rash-postexec
        _RASH_EXECUTING=""
    fi
}

preexec_functions+=(_rash-preexec)
precmd_functions+=(_rash-precmd)


### Record session initialization
if [ -z "$_RASH_SESSION_ID" ]
then
    _RASH_SESSION_ID=$(rash record --record-type init --print-session-id)
fi


### Record session exit
_rash-before-exit(){
    rash record --record-type exit --session-id "$_RASH_SESSION_ID"
}

trap "_rash-before-exit" EXIT TERM


### zle isearch widget
rash-zle-isearch(){
    BUFFER=$(rash isearch --query "$LBUFFER")
    CURSOR=$#BUFFER
    zle -R -c
}
zle -N rash-zle-isearch
