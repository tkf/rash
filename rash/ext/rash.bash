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
    _RASH_EXECUTING=t
    _RASH_PWD="$PWD"
}

rash-precmd(){
    _RASH_EXIT_CODE="$1"
    shift
    _RASH_PIPESTATUS=("$@")
    _RASH_OPTS=()

    if [ -n "$_RASH_EXECUTING" ]
    then
        local num start command
        local hist="$(HISTTIMEFORMAT="%s " builtin history 1)"
        read -r num start command <<< "$hist"
        if [ -n "$start" ]
        then
            _RASH_OPTS=(--start "$start" "${_RASH_OPTS[@]}")
        fi
        _RASH_COMMAND="$command"
        rash-postexec
        _RASH_EXECUTING=""
    fi
    rash-preexec
}

export PROMPT_COMMAND="rash-precmd \${?} \${PIPESTATUS[@]}"


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
