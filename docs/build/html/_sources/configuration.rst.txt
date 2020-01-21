Configuration
=============

To define a topology and deploy and configure an application, 3 configuration files are required:

* topology.yaml: This file only includes configuration of the virtual nodes themselves, i.e. their ID, their links to other nodes, their EC2 instance types as well as their image identifier. 
* application_definition.yaml: This file includes specifications for the different kinds of applications that will be deployed on the nodes. These include which docker container should be used as well as which ports should be openend and forwarded.
* application_configuration.yaml: This file defines one or more application configuration. These, among other things, will map application definitions to node ids, as well as provide a way to set environment variables.


Topology
========

The topology file specifies characteristics of the EC2 instances to be deployed. An example could look like this. ::


    Nodes:
    - name: generator1
      type: t2.nano
      image: ubuntu18.04

    - name: application1

    Edges:
    - u_of_edge: generator1
      v_of_edge: application1
      delay: 2


Application Definition
======================

The application_definition file specifies different kinds of applications to be deployed. An example could look like this. ::


    - name: generator
      remote_user: ec2-user
      become: yes
      vars:
        container_name: generators
        image_name: mockfogoverload/generators:mvp
        expose: 25252
        ports: 25252:8080

    - name: application
      remote_user: ec2-user
      become: yes
      vars:
        container_name: generators
        image_name: mockfogoverload/application:mvp
        expose: 25253
        ports: 25253:8080

Application Configuration
=========================

The application_configuration file allows users to create more fine grained application configurations in which he specifies which application definition is used and on which nodes the configuration should be deployed. An example could look like this. ::


    - name: genConf1
      applicaitonDefinition: generator
      nodes: generator1
      vars:
        env:
          - remote: $application1

    - name: appConf1
      applicaitonDefinition: application
      nodes: application1