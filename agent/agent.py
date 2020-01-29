import docker
import subprocess
import logging
import docker.errors


# TODO: add exception handling and logging
# TODO: add status report generation
class Docker(object):
    __docker_client = docker.from_env()

    def __init__(self, name='docker'):
        self.name = name

    def run(self, container_image, container_name):
        self.__docker_client.containers.run(image=container_image, name=container_name, detach=True,
                                            cpuset_cpus="0",
                                            mem_limit="256m")

    def update_memory_limit(self, container_name, mem_limit):
        """
        Update the memory limit by container name.
        :param container_name:
        :param mem_limit:
        :return:
        """
        try:
            container = self.__docker_client.containers.get(container_name)
            container.update(mem_limit=mem_limit, memswap_limit=mem_limit)
        except docker.errors.NotFound:
            logging.warning(container_name + ": not found on this host")
        except docker.errors.APIError as err:
            logging.warning("Failed to update " + container_name, err)

    def update_cpu_shares(self, container_name, cpu_shares):
        """
        Update the cpu shares by container name.

        :param container_name:
        :param cpu_shares:
            Set this flag to a value greater or less than the default of 1024 to increase or reduce the container’s
            weight, and give it access to a greater or lesser proportion of the host machine’s CPU cycles.
            This is only enforced when CPU cycles are constrained.
            When plenty of CPU cycles are available, all containers use as much CPU as they need.
            In that way, this is a soft limit. --cpu-shares does not prevent containers from being scheduled in
            swarm mode. It prioritizes container CPU resources for the available CPU cycles.
            It does not guarantee or reserve any specific CPU access.
            Specification from https://docs.docker.com/config/containers/resource_constraints/
        :return:
        """
        try:
            container = self.__docker_client.containers.get(container_name)
            container.update(cpu_shares=cpu_shares)
        except docker.errors.NotFound:
            logging.warning(container_name + ": not found on this host")
        except docker.errors.APIError as err:
            logging.warning("Failed to update " + container_name, err)

    def connect(self, docker_network, container_name):
        """
        Connect the container to specified network.
        :param docker_network: default is bridge
        :param container_name:
        :return:
        """
        try:
            network = self.__docker_client.networks.get(docker_network)
            network.connect(container=container_name)
        except docker.errors.NotFound:
            logging.warning(docker_network + ": not found")
        except docker.errors.APIError as err:
            logging.warning("Failed to connect " + container_name + " to " + docker_network, err)

    def disconnect(self, docker_network, container_name):
        """
        Disconnect the container from specified network.
        :param docker_network: default is bridge
        :param container_name:
        :return:
        """
        try:
            network = self.__docker_client.networks.get(docker_network)
            network.disconnect(container=container_name)
        except docker.errors.NotFound:
            logging.warning(docker_network + ": not found")
        except docker.errors.APIError as err:
            logging.warning("Failed to disconnect " + container_name + " to " + docker_network, err)

    def networks(self):
        for network in self.__docker_client.networks.list():
            print(network.name + ':')
            for container in network.containers:
                print(container.name)

    def stop_all_containers(self):
        for container in self.__docker_client.containers.list():
            container.stop()


class Tc(object):
    def __init__(self, name='tc'):
        self.name = name

    def interface(self, interface, **kwargs):
        """
        Add interface configuration.
        :param interface:
        :param kwargs:

        Args:
            bandwidth (str): network bandwidth rate [bit per second]. the minimum
                bandwidth rate is 8 bps. valid units are either: bps,
                bit/s, [kK]bps, [kK]bit/s, [kK]ibps, [kK]ibit/s,
                [mM]bps, [mM]bit/s, [mM]ibps, [mM]ibit/s, [gG]bps,
                [gG]bit/s, [gG]ibps, [gG]ibit/s, [tT]bps, [tT]bit/s,
                [tT]ibps, [tT]ibit/s. e.g. tcset eth0 --rate 10Mbps
            delay (str): round trip network delay. the valid range is from 0ms
                to 60min. valid time units are: d/day/days,
                h/hour/hours, m/min/mins/minute/minutes,
                s/sec/secs/second/seconds,
                ms/msec/msecs/millisecond/milliseconds,
                us/usec/usecs/microsecond/microseconds. if no unit
                string found, considered milliseconds as the time
                unit. default "0ms"
            loss (str): round trip packet loss rate [%]. the valid range is
                from 0 to 100. default "0"

        :return:
        """
        bandwidth = kwargs.pop('bandwidth', None)
        delay = kwargs.pop('delay', None)
        loss = kwargs.pop('loss', None)

        interface_args = ["tcset", interface]
        if bandwidth:
            interface_args.extend(["--rate", bandwidth])
        if delay:
            interface_args.extend(["--delay", delay])
        if loss:
            interface_args.extend(["--loss", loss])
        # add overwrite flag to be able to update existing rules.
        interface_args.append("--overwrite")
        try:
            subprocess.run(interface_args, check=True)
        except subprocess.CalledProcessError as err:
            logging.error(err)

    # TODO: There seems to be an issue with the "--change" flag. It overrides the whole rule instead of updating one
    #  field.
    def update_bandwidth(self, interface, bandwidth):
        """
        Configure the available bandwidth for the default docker0 interface.

        :param interface:
        :param bandwidth:
        :return:
        """
        subprocess.run(["tcset", interface, "--rate", bandwidth, "--change"], check=True)

    def show_rules(self, interface):
        print(subprocess.run(["tcshow", interface], check=True))

    def reset_interface(self, interface):
        try:
            subprocess.run(["tcdel", interface, "--all"], check=True)
        except subprocess.CalledProcessError:
            # TODO: add explanation on why we pass the error here.
            pass

    def disable(self, interface):
        """
        Disable interface. Requires root permission.
        :param interface:
        :return:
        """
        try:
            subprocess.run(["ip", "link", "set", interface, "down"], check=True)
        except subprocess.CalledProcessError:
            logging.warning("Insufficient permissions")

    def enable(self, interface):
        """
        Enable interface. Requires root permission.

        :param interface:
        :return:
        """
        try:
            subprocess.run(["ip", "link", "set", interface, "up"], check=True)
        except subprocess.CalledProcessError:
            logging.warning("Insufficient permissions")

    # TODO: We could limit traffic on ip and port granularity


class Agent(object):

    def __init__(self, name='agent'):
        self.name = name
        self.docker = Docker()
        self.tc = Tc()


def main():
    agent = Agent()
    interface = "docker0"
    agent.tc.interface(interface, bandwidth="10Mbps", delay="10ms", loss="0.1")
    agent.tc.show_rules(interface)
    agent.tc.reset_interface(interface)
    agent.tc.show_rules(interface)
    agent.tc.interface(interface, bandwidth="10Mbps", delay="1min", loss="0.9")
    agent.tc.show_rules(interface)
    agent.tc.disable(interface)


if __name__ == '__main__':
    main()
