#!/usr/bin/env bash
#
# FILE : install.sh
#
# USAGE : su -
#         ./install.sh
#
# DESCRIPTION : Devloppement install script for Sappy
#
# BUGS : ---
# NOTES : Work
# CONTRUBUTORS : Babilinx
# CREATED : october 2022
# REVISION: 25 october 2022
#
# LICENCE :
# Copyright (C) 2022 Skythrew, Babilinx
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along with
# this program. If not, see https://www.gnu.org/licenses/.


if [ "$EUID" -ne 0 ]; then
  echo "Needs to have roots rights."
  exit
fi

read - p "What is your username ? " USERNAME

echo "This install script is only for devs !"
read -p "[Enter] to continue"

echo "The folder <stocklinux> will be created at the root of your home folder"
mkdir stocklinux 
cd stocklinux

mkdir sappy-bin

git clone https://github.com/stock-linux/squirrel.git && git clone https://github.com/stock-linux/sappy.git

rm /bin/sappy && rm /bin/squirrel

ln -s $PWD/squirrel/squirrel /bin/ && ln -s $PWD/sappy/sappy /bin/

echo -e "#!/bin/sh\npython3 $PWD/sappy/main.py \$@" > sappy/sappy
echo -e "#!/bin/sh\npython3 $PWD/squirrel/main.py \$@" > squirrel/squirrel

pip3 install docopt pyaml requests

mkdir -p /etc/sappy/store

echo 'host: 'stocklinux.hopto.org:8080'' > /etc/sappy/sappy.conf
echo 'release: 'main'' >> /etc/sappy/sappy.conf
echo 'branches:' >> /etc/sappy/sappy.conf
echo '- main' >> /etc/sappy/sappy.conf
echo "workdir: $PWD/sappy-bin" >> /etc/sappy/sappy.conf
echo 'produceBinaries: true' >> /etc/sappy/sappy.conf

mkdir -p $PWD/squirrel/dev/etc/squirrel/ $PWD/squirrel/dev/var/squirrel/repos/dist/ $PWD/squirrel/dev/var/squirrel/repos/local/ $PWD/squirrel/dev/var/squirrel/repos/local/main/

echo "configPath = '$PWD/squirrel/dev/etc/squirrel/'" > squirrel/utils/config.py
echo "distPath = '$PWD/squirrel/dev/var/squirrel/repos/dist/'" >> squirrel/utils/config.py
echo "localPath = '$PWD/squirrel/dev/var/squirrel/repos/local/'" >> squirrel/utils/config.py

echo "main http://stocklinux.hopto.org:8080/main/main" >> squirrel/dev/etc/squirrel/branches

touch $PWD/squirrel/dev/var/squirrel/repos/local/main/INDEX

cd .. && chown -R $USERNAME:$USERNAME stocklinux/

echo "Everything is configured !"

exit
