import pyshark
import os
import re
import socket


def get_interfaces():
    """
    Get the network connection on local machine.
    :return: interfaces is a list like: ['USBPcap1', 'USBPcap2', 'USBPcap3', 'Wireless Network Connection',
            'Local Area Connection', 'Wireless Network Connection 2', 'Wireless Network Connection 3']
    This function needs some protection, maybe.
    """
    tshark_path = pyshark.tshark.tshark.get_tshark_path()
    cmd = '"%s" -D' % tshark_path
    cmd_res = os.popen(cmd).readlines()
    interfaces = []
    for each_interface in cmd_res:
        res = re.findall('\((.*)\)', each_interface)
        interfaces.append(res[0])
    return interfaces


def capture_scpi(interface, ipaddress, port='24000'):
    """
    The generator to capture scpi.
    :param interface: network connections
    :param ipaddress: the ip address of iqxstream, like '192.168.1.254' or 'iqxs8499'
    :param port: port number. string type. like '24100'
    :return: yield the scpi captured each time
    """
    cap = pyshark.LiveCapture(interface=interface)
    # cap.bpf_filter = 'host 192.168.220.11'  # for debug
    cap.bpf_filter = 'tcp port %s and host %s' % (port, ipaddress)
    # cap.bpf_filter = '(tcp port 24000 or tcp port 24100 or tcp port 24200) and host %s' % ipaddress
    inst_ipaddress = socket.gethostbyname(ipaddress)
    for each_packet in cap.sniff_continuously():
        try:
            scpi_captured = each_packet.data.data.decode('hex').strip()
            if scpi_captured:
                # add timestamp
                scpi_captured = '[' + str(each_packet.sniff_time) + ']\t' + scpi_captured
                # add src
                if each_packet.ip.dst_host == inst_ipaddress:
                    scpi_captured = 'Send:  ' + scpi_captured
                else:
                    scpi_captured = 'Recv:  ' + scpi_captured
                print scpi_captured
                yield scpi_captured
        except AttributeError:
            pass


def capture_scpi_all_ports(interface, ipaddress):
    """
    The generator to capture scpi on all ports.
    :param interface: network connections
    :param ipaddress: the ip address of iqxstream, like '192.168.1.254' or 'iqxs8499'
    :return: yield the scpi captured each time
    """
    cap = pyshark.LiveCapture(interface=interface)
    # cap.bpf_filter = 'host 192.168.220.11'  # for debug
    port_list = ['24000', '24100', '24200']
    port_filter = ' or '.join(['tcp port %s' % each_port for each_port in port_list])
    cap.bpf_filter = '(%s) and host %s' % (port_filter, ipaddress)
    # cap.bpf_filter = '(tcp port 24000 or tcp port 24100) and host %s' % ipaddress
    inst_ipaddress = socket.gethostbyname(ipaddress)
    for each_packet in cap.sniff_continuously():
        try:
            scpi_captured = each_packet.data.data.decode('hex').strip()
            if scpi_captured:
                # add src
                if each_packet.ip.dst_host == inst_ipaddress:
                    scpi_captured = 'Send:  ' + scpi_captured
                else:
                    scpi_captured = 'Recv:  ' + scpi_captured
                # add port
                scpi_captured = ('Port%s ' % each_packet.tcp.dstport) + scpi_captured
                # add timestamp
                scpi_captured = '[' + str(each_packet.sniff_time) + ']\t' + scpi_captured
                print scpi_captured
                yield scpi_captured
        except AttributeError:
            pass


def main():
    # get_interfaces()
    capture_scpi(interface='Wireless Network Connection', ipaddress='192.168.220.11', port='8080')


if __name__ == '__main__':
    main()


