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
