#!/bin/bash

# Poner como job de cron ej:
#01 * * * * REMOTE="t01@t01" /usr/bin/nobix_backup.sh

# Update database backup
PGHOST="localhost"
PGUSER='nobix'
PGDATABASE='nobix'

date=`date '+%Y-%m-%d_%H%M'`

BKP=$PGDATABASE-$date.sql.xz

/usr/bin/pg_dump -c -O -h $PGHOST -U $PGUSER $PGDATABASE | xz > ~/.backups/$BKP

[ -n "$REMOTE" ] && scp ~/.backups/$BKP $REMOTE:.backups/$BKP &>/dev/null

# Mega upload copy
/usr/bin/megaput --no-progress --config ~/.megarc --path /Root/bkp_nobix/$BKP ~/.backups/$BKP >> /tmp/bkp_mega.log 2>&1
