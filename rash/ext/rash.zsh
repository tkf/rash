# Copyright (C) 2013-  Takafumi Arakaki

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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

_rash-zshaddhistory(){
    _RASH_COMMAND="${1%%$'\n'}"
    _RASH_DEBUG_COMMAND_LOG_TYPE=zshaddhistory  # SOMEDAY: remove this
}

_rash-history-fallback(){
    # reading "$(builtin history -n -1)" directly does not work when
    # command contains newlines.
    local num command
    read -r num command <<< "$(builtin history -1)"
    _RASH_COMMAND="$history[$num]"
    _RASH_DEBUG_COMMAND_LOG_TYPE=history-array

    # `$history' may not work as it is not documented.  In that case,
    # fallback to $(builtin history -n -1):
    if [ -z "$_RASH_COMMAND" -a -n "$command" ]
    then
        _RASH_COMMAND="$(builtin history -n -1)"
        _RASH_DEBUG_COMMAND_LOG_TYPE=history-builtin
    fi
}

_rash-precmd(){
    # Make sure to copy these variable at very first stage.
    # Otherwise, I will loose these information.
    _RASH_EXIT_CODE="$?"
    _RASH_PIPESTATUS=("${pipestatus[@]}")
    _RASH_OPTS=(--start "$_RASH_START")

    if [ -z "$_RASH_COMMAND" ]
    then
        # Some old zsh (< 4.3?) does not support zshaddhistory.
        _rash-history-fallback
    fi

    if [ -n "$_RASH_EXECUTING" ]
    then
        _rash-postexec
        _RASH_EXECUTING=""
        _RASH_COMMAND=""
    fi
}

preexec_functions+=(_rash-preexec)
precmd_functions+=(_rash-precmd)
zshaddhistory_functions+=(_rash-zshaddhistory)


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
    local result="$(rash isearch --query "$BUFFER" "$@")"
    if [ -n "$result" ]
    then
        BUFFER="$result"
        CURSOR=$#BUFFER
    fi
    zle -R -c
}
zle -N rash-zle-isearch
