import docker
import subprocess


# TODO: add exception handling
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
        container = self.__docker_client.containers.get(container_name)
        container.update(mem_limit=mem_limit, memswap_limit=mem_limit)

    def update_cpu_shares(self, container_name, cpu_shares):
        """
                    Update the cpu shares by container name.

                    :param container_name:
                    :param cpu_shares:
                    Set this flag to a value greater or less than the default of 1024 to increase or reduce the container’s weight,
                    and give it access to a greater or lesser proportion of the host machine’s CPU cycles.
                    This is only enforced when CPU cycles are constrained.
                    When plenty of CPU cycles are available, all containers use as much CPU as they need.
                    In that way, this is a soft limit. --cpu-shares does not prevent containers from being scheduled in swarm mode.
                    It prioritizes container CPU resources for the available CPU cycles.
                    It does not guarantee or reserve any specific CPU access.
                    Specification from https://docs.docker.com/config/containers/resource_constraints/
                    :return:
                    """
        container = self.__docker_client.containers.get(container_name)
        container.update(cpu_shares=cpu_shares)

    def connect(self, docker_network, container_name):
        """
        Connect the container to specified network.
        :param docker_network: default is bridge
        :param container_name:
        :return:
        """
        network = self.__docker_client.networks.get(docker_network)
        network.connect(container=container_name)

    def disconnect(self, docker_network, container_name):
        """
        Disconnect the container from specified network.
        :param docker_network: default is bridge
        :param container_name:
        :return:
        """
        network = self.__docker_client.networks.get(docker_network)
        network.disconnect(container=container_name)

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

    def bandwidth(self, bandwidth):
        """
        Configure the available bandwidth for the default docker0 interface.

        :param bandwidth:
        :return:
        """
        subprocess.run(["tcset", "docker0", "--rate", bandwidth])

    def bandwidth(self, container_name, bandwidth):
        """
        Configure the available bandwidth for the specified container.

        :param container_name:
        :param bandwidth:
            network bandwidth rate [bit per second]. the minimum
            bandwidth rate is 8 bps. valid units are either: bps,
            bit/s, [kK]bps, [kK]bit/s, [kK]ibps, [kK]ibit/s,
            [mM]bps, [mM]bit/s, [mM]ibps, [mM]ibit/s, [gG]bps,
            [gG]bit/s, [gG]ibps, [gG]ibit/s, [tT]bps, [tT]bit/s,
            [tT]ibps, [tT]ibit/s. e.g. tcset eth0 --rate 10Mbps
        :return:
        """
        subprocess.run(["tcset", container_name, "--docker", "--rate", bandwidth])

    def latency(self, latency):
        """
                Configure the round tip network delay for the specified container.

                :param latency:
                    round trip network delay. the valid range is from 0ms
                    to 60min. valid time units are: d/day/days,
                    h/hour/hours, m/min/mins/minute/minutes,
                    s/sec/secs/second/seconds,
                    ms/msec/msecs/millisecond/milliseconds,
                    us/usec/usecs/microsecond/microseconds. if no unit
                    string found, considered milliseconds as the time
                    unit.
                :return:
                """
        subprocess.run(["tcset", "docker0", "--delay", latency])

    def latency(self, container_name, latency):
        """
        Configure the round tip network delay for the default docker0 interface.

        :param container_name:
        :param latency:
            round trip network delay. the valid range is from 0ms
            to 60min. valid time units are: d/day/days,
            h/hour/hours, m/min/mins/minute/minutes,
            s/sec/secs/second/seconds,
            ms/msec/msecs/millisecond/milliseconds,
            us/usec/usecs/microsecond/microseconds. if no unit
            string found, considered milliseconds as the time
            unit.
        :return:
        """
        subprocess.run(["tcset", container_name, "--docker", "--delay", latency])

    def show_tc_rules(self):
        print(subprocess.run(["tcshow", "docker0"]))

    def reset_default_interface(self):
        subprocess.run(["tcdel", "docker0", "--all"])

    # TODO: kwargs?

    def packet_loss(self, container_name, packet_loss):
        """
        Configure the packet loss rate for the specified container.

        :param container_name:
        :param packet_loss:
            round trip packet loss rate [%]. the valid range is
            from 0 to 100.
        :return:
        """
        subprocess.run(("tcset", container_name, "--docker", "--loss", packet_loss))

    # TODO: We could limit traffic on ip and port granularity


class Agent(object):

    def __init__(self, name='agent'):
        self.name = name
        self.docker = Docker()
        self.tc = Tc()


def main():
    agent = Agent()
    agent.docker.run("angryeinstein/backend", "backend")
    agent.tc.latency("10s")
    agent.tc.bandwidth("10Mbps")
    agent.tc.show_tc_rules()
    agent.tc.reset_default_interface()


if __name__ == '__main__':
    main()
