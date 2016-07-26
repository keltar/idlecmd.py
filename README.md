Execute specified command when computer is idle
====================

Note: depends on python psutil

Usage
-----

Shutdown when CPU load keeps low for 60 seconds

    ./idlecmd.py --cpu --time=60 --run="shutdown -h 0"

Echo "finished" when network load drops below 2 megabytes per second and keeps
low for 10 seconds (default value of `time`)

    ./idlecmd.py --net --net-rule="<2M" --run="echo finished"
