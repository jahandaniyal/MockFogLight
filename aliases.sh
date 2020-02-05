#!/bin/bash

mockfog_topology() {
  # params : key_file, task
  for ARGUMENT in "$@"
do

    KEY=$(echo $ARGUMENT | cut -f1 -d=)
    VALUE=$(echo $ARGUMENT | cut -f2 -d=)

    case "$KEY" in
            keyfile)              KEYFILE=${VALUE} ;;
            task)    TASK=${VALUE} ;;
            *)
    esac


done
    ansible-playbook --key-file="$KEYFILE" --ssh-common-args="-o StrictHostKeyChecking=no" mockfog_topology.yml --tags "$TASK"
}

mockfog_network() {
    # params : key_file
    ansible-playbook -i inventory/ec2.py --key-file="$1" --ssh-common-args="-o StrictHostKeyChecking=no" mockfog_network.yml
}

mockfog_application() {
  # params : key_file, task
  for ARGUMENT in "$@"
do

    KEY=$(echo $ARGUMENT | cut -f1 -d=)
    VALUE=$(echo $ARGUMENT | cut -f2 -d=)

    case "$KEY" in
            keyfile)              KEYFILE=${VALUE} ;;
            task)    TASK=${VALUE} ;;
            *)
    esac


done

#echo "KEYFILE = $KEYFILE"
#echo "TASK = $TASK"

ansible-playbook -i inventory/ec2.py --key-file="$KEYFILE" --ssh-common-args="-o StrictHostKeyChecking=no" mockfog_application.yml --tags "$TASK"
}

mockfog_facts() {
    # params : key_file
    ansible-playbook -i inventory/ec2.py --key-file="$1" --ssh-common-args="-o StrictHostKeyChecking=no" mockfog_info.yml
}
