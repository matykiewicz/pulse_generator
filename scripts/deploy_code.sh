# /bin/bash

DEST="jetson@192.168.8.228"

ssh "${DEST}"  "rm -rf ~/pulse_generator"
scp -r ../pulse_generator "${DEST}":~/pulse_generator

