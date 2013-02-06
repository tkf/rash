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
    _RASH_EXECUTING=t
    _RASH_PWD="$PWD"
}

_rash-precmd(){
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
        _rash-postexec
        _RASH_EXECUTING=""
    fi
    _rash-preexec
}

export PROMPT_COMMAND="_rash-precmd \${?} \${PIPESTATUS[@]}"


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
