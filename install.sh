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
# NOTES : Not tested.
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

echo "This install script is only for devs !"
read -p "[Enter] to continue"

echo "The folder <stocklinux> will be created at the root of your home folder"
cd ~ && mkdir stocklinux && cd stocklinux

git clone https://github.com/stock-linux/squirrel.git && git clone https://github.com/stock-linux/sappy.git

ln -s squirrel/squirrel /bin/ && ln -s sappy/sappy /bin/

echo -e "#!/bin/sh\npython3 $PWD/sappy/main.py $@" | tee sappy/sappy
echo -e "#!/bin/sh\npython3 $PWD/squirrel/main.py $@" | tee squirrel/squirrel

pip3 install docopt pyaml # one left

mkdir /etc/sappy \
echo 'host: 'stocklinux.hopto.org:8080'
release: 'main'
branches:
- main
workdir: ${PWD}
produceBinaries: true' | tee /etc/sappy/sappy.conf
