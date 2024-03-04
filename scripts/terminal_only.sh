
sudo systemctl set-default multi-user.target

#NAutoVTs
#ReserveVT

/etc/systemd/logind.conf
sudo mkdir /etc/systemd/system/getty@tty1.service.d/
sudo nano /etc/systemd/system/getty@tty1.service.d/override.conf

[Service]
ExecStart=
ExecStart=-/sbin/agetty --noissue --autologin ostechnix %I $TERM
Type=idle


