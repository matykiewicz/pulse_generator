# /bin/bash

DEST="pawelm@172.16.3.76"

ssh "${DEST}"  "rm -rf ~/pulse_generator"
scp -r ../pulse_generator "${DEST}":~/pulse_generator

