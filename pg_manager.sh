#!/bin/bash
USER="user"
PASSWORD="password"
DB="db"
HOST="db"
POSTGRESQL_URL="postgres://$USER:$PASSWORD@$HOST:5432/$DB"
SAVES_DIR="db_saves"
export PGPASSWORD=$PASSWORD
if [ "$1" == "" ]
then
    printf '\033[1;31mNo parameter provided, choices are \033[4;33mdump\033[0m\033[1;31m or \033[4;33mload\033[0m\n'
elif [ "$1" == "dump" ]
then
    date_name=$(date '+%Y-%m-%d_%H.%M.%S')
    printf '\033[1;34mDo you want to give your save a cool name (empty = date) ?\033[0m\n'
    read filename
    if [ "$filename" != "" ]
    then
        filename=$filename"_"
    fi
    pg_dump $POSTGRESQL_URL --format=custom -f "$SAVES_DIR/$filename$date_name.dump" -v
    chmod -R 777 $SAVES_DIR"/"
    printf "\033[1;32mYour database has been saved successfully.\033[0m\n ______\n| |__| |\n|  ()  |\n|______|\n"
elif [ "$1" == "load" ]
then
    printf '\033[1;34mWhich database do you want to load ?\033[0m\n'
    printf '\033[1;31m/!\ Your current database will be destroyed. Save it with \033[4;33mdump_db\033[0m\033[1;31m if you do not want to lose any data.\033[0m\n'
    i=0
    for entry in "$SAVES_DIR"/*
    do
      printf "\033[1;33m$i)\033[0m $entry\n"
      i=$((i+1))
    done
    printf "\033[1;34mEnter number (q=quit):\033[0m\n"
    read c
    if [ "$c" == "q" ]
    then
        exit
    else
        i=0
        for entry in "$SAVES_DIR"/*
        do
          if [ "$c" == "$i" ]
          then
              pg_restore --verbose --clean --no-acl -U $USER --host $HOST --dbname $DB $entry
              printf "\033[1;32mDatabase \033[4;33m"$entry"\033[0m\033[1;32m has been loaded successfully.\033[0m\n"
              exit
          fi
          i=$((i+1))
        done
        printf '\033[1;31mInvalid database index '$c', please enter a valid index\033[0m\n'
        $0 $1
    fi
else
    printf '\033[1;31mInvalid parameter '$1', choices are \033[4;33mdump\033[0m\033[1;31m or \033[4;33mload\033[0m\n'
fi
