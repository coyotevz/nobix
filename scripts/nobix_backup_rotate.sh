#!/bin/bash

PGDATABASE='nobix'
DEFAULT_COUNT=5

if [ -z "$LOCAL_COUNT" ]; then
  LOCAL_COUNT=$DEFAULT_COUNT
fi

if [ -z "$REMOTE_COUNT" ]; then
  REMOTE_COUNT=$DEFAULT_COUNT
fi

purge () {
  CMD=$1
  COUNT=$2
  counter=0
  toremove=()
  for bkp_file in `$CMD "ls -t ~/.backups/$PGDATABASE-*.sql.xz"`; do
    let ++counter
    [ "$counter" -gt "$COUNT" ] && toremove[${#toremove[@]}]=$bkp_file
  done
  [ ${#toremove[@]} -gt 0 ] && $CMD "rm ${toremove[@]} &> /dev/null"
}

purge 'eval' $LOCAL_COUNT
[ -n "$REMOTE" ] && purge "ssh $REMOTE" $REMOTE_COUNT
