#!/bin/bash

uid=$(stat -c %u /persistent)
gid=$(stat -c %g /persistent)

echo $uid $gid
ls -alF $0

if [ -x $0 ]; then
    groupadd -g $gid tensorflow
    useradd -m -s /bin/bash -u $uid -g $gid tensorflow
    usermod -aG sudo tensorflow
    chmod -x $0
fi

su - tensorflow -c /bin/bash
