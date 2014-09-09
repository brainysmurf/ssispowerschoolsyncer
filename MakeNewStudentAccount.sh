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
