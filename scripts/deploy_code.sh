# /bin/bash

IP=${IP:-192.168.8.228}
DEST="jetson@${IP}"

echo "IP = $IP"
ssh "${DEST}"  "rm -rf ~/pulse_generator"
scp -r ../pulse_generator "${DEST}":~/pulse_generator

