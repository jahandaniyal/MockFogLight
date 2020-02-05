from http.server import HTTPServer, BaseHTTPRequestHandler
from io import BytesIO
import logging
logging.warning("ASD")
import json
import docker
import subprocess
import sched, time

import docker.errors


class ContainerStatus:
    def __init__(self, name):
        self.name = name
        self.memory_limit = "256"
        self.cpu_shares = "1024"
        self.connections = {}

        self.bandwidth = ""
        self.latency = "0.0ms"
        self.packet_loss = "0"

    def get_name(self):
        return self.name

    def get_memory_limit(self):
        return self.memory_limit

    def set_memory_limit(self, memory_limit):
        self.memory_limit = memory_limit

    def get_cpu_shares(self):
        return self.cpu_shares

    def set_cpu_shares(self, cpu_shares):
        self.cpu_shares = cpu_shares

    def get_bandwidth(self):
        return self.bandwidth

    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth

    def get_connection_status(self, connection_name):
        if not (connection_name in self.connections):
            self.connections[connection_name] = "disconnected"

        return self.connections[connection_name]

    def set_connection_status(self, connection_name, status):
        self.connections[connection_name] = status

    def get_latency(self):
        return self.latency

    def set_latency(self, latency):
        self.latency = latency

    def get_packet_loss(self):
        return self.packet_loss

    def set_packet_loss(self, packet_loss):
        self.packet_loss = packet_loss

    def update_values(self):
        """ The result of tcshow looks like the following """
        """ {
            "docker0": {
                "outgoing": {
                    "dst-network=192.168.0.10/32, dst-port=8080, protocol=ip": {
                        "filter_id": "800::800",
                        "delay": "10.0ms",
                        "delay-distro": "2.0ms",
                        "loss": "0.01%",
                        "rate": "250Kbps"
                    }
                },
                "incoming": {
                    "protocol=ip": {
                        "filter_id": "800::800",
                        "delay": "1.0ms",
                        "loss": "0.02%",
                        "rate": "500Kbps"
                    }
                }
            }
        }"""

        try:
            result = subprocess.run(["tcshow", self.name], stdout=subprocess.PIPE)
            data = json.loads(result.stdout)
            for _, values in data[self.name]["outgoing"].items():
                if "delay" in values:
                    self.latency = values["delay"]
                if "loss" in values:
                    self.packet_loss = values["loss"]
                if "rate" in values:
                    self.bandwidth = values["rate"]
        except:
            print("'tcshow' failed, using saved values")

    def to_json(self):
        self.update_values()

        connections_json = "{"
        i = 0

        for conn_name, conn_status in self.connections.items():
            if i != 0:
                connections_json += ','

            connections_json += '"%s": "%s"' % (conn_name, conn_status)
            i += 1

        connections_json += "}"

        return """{
        "memory_limit": "%s",
        "cpu_shares": "%s",
        "bandwidth": "%s",
        "latency": "%s",
        "packet_loss": "%s",
        "connections": %s
    }""" % (self.memory_limit, self.cpu_shares, self.bandwidth, self.latency, self.packet_loss, connections_json)


class AgentStatus:
    def __init__(self):
        self.containers = {
            'docker0': ContainerStatus('docker0')
        }

    def get_container(self, container_name):
        if not (container_name in self.containers):
            self.containers[container_name] = ContainerStatus(container_name)

        return self.containers[container_name]

    def to_json(self):
        json = "{\n    "
        i = 0

        for name, container in self.containers.items():
            if i != 0:
                json += ',\n    '

            json += '"%s": ' % (name)
            json += container.to_json()
            i += 1

        json += "\n}"
        return json


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
            Set this flag to a value greater or less than the default of 1024 to increase or reduce the container's
            weight, and give it access to a greater or lesser proportion of the host machine's CPU cycles.
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


class WebServerHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        self.send_response(200)
        content_length = int(self.headers['Content-Length'])
        content_type = self.headers['Content-Type']

        if content_type != 'application/json':
            print("Wrong content type,json expected!")
            return

        body = self.rfile.read(content_length)
        response = BytesIO()
        response.write(b'Received: ' + body + b'\n')
        self.end_headers()
        self.wfile.write(response.getvalue())

        content_string = body.decode('utf-8')
        content_json_array = json.loads(content_string)

        agent = Agent()
        # s = sched.scheduler(time.localtime(), time.sleep())
        # s.enterabs(time.strptime(content_json_array[0]['timestamp']), 0,
        #            scheduler(self.path, self.agent, content_json_array))
        scheduler(self.path, agent, content_json_array)


def endpoint_application(content_json_array):
    content_dict = {}
    try:
        content_dict['timestamp'] = content_json_array[0]['timestamp']
        content_dict['name'] = content_json_array[0]['data']['name']
        content_dict['cpu'] = content_json_array[0]['data']['cpu']
        content_dict['memory'] = content_json_array[0]['data']['memory']
        content_dict['active'] = content_json_array[0]['data']['active']
    except KeyError:
        pass

    return content_dict


def endpoint_interface(content_json_array):
    content_dict = {}
    try:
        content_dict['timestamp'] = content_json_array[0]['timestamp']
        content_dict['id'] = content_json_array[0]['data']['id']
        content_dict['active'] = content_json_array[0]['data']['active']
        content_dict['bandwidth'] = content_json_array[0]['data']['bandwidth']
    except KeyError:
        pass

    return content_dict


def scheduler(path, agent, content_json_array):
    if path == "/application":
        content_dict = endpoint_application(content_json_array)
        schedule_application(agent, content_dict)

    if path == "/interface":
        content_dict = endpoint_interface(content_json_array)
        schedule_interface(agent, content_dict)

    if path == "/reports/":
        print(agent.status.to_json())


def schedule_application(agent, content_dict):
    if 'cpu' in content_dict:
        agent.docker.update_cpu_shares(content_dict['name'], content_dict['cpu'])
        print("New cpu limit has been setup")

    if 'memory' in content_dict:
        agent.docker.update_memory_limit(content_dict['name'], content_dict['memory'])
        print("New memory has been setup")


def schedule_interface(agent, content_dict):
    if 'bandwidth' in content_dict:
        agent.tc.bandwidth(content_dict['id'], content_dict['bandwidth'])
        print("New bandwidth setup")


class Agent(object):

    def __init__(self, name='agent'):
        self.status = AgentStatus()
        self.name = name
        self.docker = Docker(self.status)
        self.tc = Tc(self.status)


def main():
    try:
        port = 8080
        server = HTTPServer(('', port), WebServerHandler)
        print("Web server is running on port {}".format(port))
        server.serve_forever()

    except KeyboardInterrupt:
        print(" ^C entered, stopping web server....")
        server.socket.close()


if __name__ == '__main__':
    main()
