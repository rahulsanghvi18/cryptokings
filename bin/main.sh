#!/bin/bash

source ~/envs/webdevDjango/bin/activate
export PYTHONPATH=$PYTHONPATH:"$(dirname "$(pwd)")"


source $PWD/bin/run.sh &
source $PWD/bin/redis.sh &
source $PWD/bin/worker.sh &
source $PWD/bin/beat.sh


wait
echo "Exiting..."