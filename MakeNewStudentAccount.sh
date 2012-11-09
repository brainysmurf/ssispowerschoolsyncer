#!/bin/bash

defaultpassword=changeme
newuserspath=/usr/sbin/newusers

echo
echo "-------------------------"
echo "NEW STUDENT"
idnumber=$1
username=$2
fullname=$3
echo "$2: $1"
echo "- - - - - - - - - - - - -"
echo "$2"":""$defaultpassword"":::""$1"":/home/$2:/bin/bash" | $newuserspath

mailfile="/var/lib/squirrelmail/data/$username"".pref"
echo "Adding static webmail preferences to $mailfile"
touch $mailfile
chown www-data:www-data $mailfile
cat /var/lib/squirrelmail/data/default_pref > $mailfile
echo "Adding dynamic webmail preferences"
echo "full_name=$fullname" >> $mailfile
echo "-------------------------"