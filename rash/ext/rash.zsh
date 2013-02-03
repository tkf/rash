### Record commands
rash-postexec(){
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

rash-preexec(){
    _RASH_START=$(date "+%s")
    _RASH_EXECUTING=t
    _RASH_PWD="$PWD"
}

rash-precmd(){
    # Make sure to copy these variable at very first stage.
    # Otherwise, I will loose these information.
    _RASH_EXIT_CODE="$?"
    _RASH_PIPESTATUS=("${pipestatus[@]}")
    _RASH_OPTS=(--start "$_RASH_START")
    _RASH_COMMAND="$(builtin history -n -1)"

    if [ -n "$_RASH_EXECUTING" ]
    then
        rash-postexec
        _RASH_EXECUTING=""
    fi
}

autoload -Uz add-zsh-hook
add-zsh-hook preexec rash-preexec
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


### Start daemon
if [ -z "$RASH_INIT_NO_DAEMON" ]
then
    rash daemon --no-error ${=RASH_INIT_DAEMON_OPTIONS} \
        < /dev/null > /dev/null 2> /dev/null &
    RASH_DAEMON_PID="$!"
fi
