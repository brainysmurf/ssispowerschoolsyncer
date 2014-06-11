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

mailfile="/usr/local/squirrelmail/data/"$username".pref"
touch $mailfile
chown www-data:www-data $mailfile
echo "Adding webmail user info into their preferences"
echo "full_name="$fullname >> $mailfile
echo "email_address="$username"@student.ssis-suzhou.net" >> $mailfile
echo "-------------------------"
