#!/bin/bash

# Update database backup
PGHOST="localhost"
PGUSER='nobix'
PGDATABASE='nobix'

date=`date '+%Y-%m-%d_%H%M'`

BKP=$PGDATABASE-$date.sql.xz

/usr/bin/pg_dump -c -O -h $PGHOST -U $PGUSER $PGDATABASE | xz > ~/.backups/$BKP

[ -n "$REMOTE" ] && scp ~/.backups/$BKP $REMOTE:.backups/$BKP &>/dev/null
