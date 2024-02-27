# /bin/bash

DEST="jetson@172.16.3.79"

ssh "${DEST}"  "rm -rf ~/pulse_generator"
scp -r ../pulse_generator "${DEST}":~/pulse_generator

