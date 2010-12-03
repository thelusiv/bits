#!/bin/bash

# script to startup mencoder to capture from a video device (written for a
# Pinnacle Dazzle DVC 100 USB capture device, will probably work for a lot of
# other things)

recorder=/usr/bin/mencoder
datestring=`date +%Y%m%d-%H%M`
videodir=/data/media/video/recorded
options="tv:// -tv driver=v4l2:norm=NTSC-M:audiorate=48000:immediatemode=0:device=/dev/video0:forceaudio:adevice=/dev/dsp2 -o $videodir/$datestring.avi lavc -lavcopts vcodec=mjpeg:aspect=4/3 -aspect 4:3 -noautoexpand -oac lavc -ovc copy"
logfile=$videodir/logs/$datestring.log

$recorder $options > $logfile
