#!/bin/sh

sudo umount mnt
sudo pkill secfs-
rm -rf mnt server.sock 

sudo umount mnt2
sudo pkill secfs-
rm -rf mnt2 server.sock
