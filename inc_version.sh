#!/bin/bash

### Increments the part of the string
## $1: version itself
## $2: number of part: 0 – major, 1 – minor, 2 – patch

get_version() {
    sed -nE 's/^VERSION = "(.+)"$/\1/p' $1
}

increment_version() {
    declare -A type_dict
    type_dict['major']=0
    type_dict['minor']=1
    type_dict['patch']=2
    if [[ -z ${type_dict[$2]} ]]; then
        echo "Invalid revision type '$2' (use: major | minor | patch)"
        exit 1
    fi
    local delimiter=.
    local array=($(echo "$1" | tr $delimiter '\n'))
    local pos=($(echo ${type_dict[$2]}))
    array[$pos]=$((array[$pos]+1))
    if [ $pos -lt 2 ]; then array[2]=0; fi
    if [ $pos -lt 1 ]; then array[1]=0; fi
    echo $(local IFS=$delimiter ; echo "${array[*]}")
}

set_version() {
    sed -i "s/^VERSION = \".*\"$/VERSION = \"$1\"/" $2
}

CURRENT_VERSION=$(get_version $2)
NEW_VERSION=$(increment_version $CURRENT_VERSION $1)
if  [[ $? -eq 1 ]]; then
    echo $NEW_VERSION
    exit 1
fi
set_version $NEW_VERSION $2
echo $NEW_VERSION
