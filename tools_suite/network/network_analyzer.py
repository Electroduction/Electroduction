#!/usr/bin/env python3
"""
Network Analysis Toolkit
========================

A comprehensive toolkit for network analysis, packet inspection, and traffic monitoring.
Provides tools for protocol analysis, network mapping, and security assessment.

Author: Electroduction Security Team
Version: 1.0.0

Features:
---------
- Protocol Analysis: Parse and analyze network protocols
- Traffic Analysis: Analyze network traffic patterns
- Network Mapping: Discover and map network topology
- Packet Analysis: Deep packet inspection and parsing
- Bandwidth Monitoring: Track network usage
- Connection Tracking: Monitor active connections

Usage:
------
    from network_analyzer import NetworkAnalyzer, PacketParser, TrafficMonitor

    # Parse packets
    parser = PacketParser()
    parsed = parser.parse_ethernet(raw_data)

    # Monitor traffic
    monitor = TrafficMonitor()
    stats = monitor.get_statistics()

Note: Some features require root/administrator privileges.
"""

import os
import re
import json
import socket
import struct
import time
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Set, Callable
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
import ipaddress


# =============================================================================
# CONSTANTS AND PROTOCOL DEFINITIONS
# =============================================================================

# Ethernet Types
ETHERNET_TYPES = {
    0x0800: 'IPv4',
    0x0806: 'ARP',
    0x86DD: 'IPv6',
    0x8100: 'VLAN',
    0x88A8: 'QinQ',
    0x8847: 'MPLS',
    0x8848: 'MPLS Multicast',
    0x88CC: 'LLDP',
    0x88E5: 'MACsec',
    0x88F7: 'PTP',
}

# IP Protocol Numbers
IP_PROTOCOLS = {
    1: 'ICMP',
    2: 'IGMP',
    6: 'TCP',
    17: 'UDP',
    41: 'IPv6',
    47: 'GRE',
    50: 'ESP',
    51: 'AH',
    58: 'ICMPv6',
    89: 'OSPF',
    132: 'SCTP',
}

# Well-Known Ports
WELL_KNOWN_PORTS = {
    20: 'FTP-DATA', 21: 'FTP', 22: 'SSH', 23: 'TELNET', 25: 'SMTP',
    53: 'DNS', 67: 'DHCP-S', 68: 'DHCP-C', 69: 'TFTP', 80: 'HTTP',
    110: 'POP3', 119: 'NNTP', 123: 'NTP', 135: 'RPC', 137: 'NetBIOS-NS',
    138: 'NetBIOS-DGM', 139: 'NetBIOS-SSN', 143: 'IMAP', 161: 'SNMP',
    162: 'SNMP-TRAP', 389: 'LDAP', 443: 'HTTPS', 445: 'SMB',
    465: 'SMTPS', 514: 'SYSLOG', 520: 'RIP', 587: 'SUBMISSION',
    636: 'LDAPS', 993: 'IMAPS', 995: 'POP3S', 1433: 'MSSQL',
    1521: 'ORACLE', 3306: 'MYSQL', 3389: 'RDP', 5432: 'POSTGRESQL',
    5900: 'VNC', 6379: 'REDIS', 8080: 'HTTP-PROXY', 8443: 'HTTPS-ALT',
    27017: 'MONGODB',
}

# TCP Flags
TCP_FLAGS = {
    'FIN': 0x01,
    'SYN': 0x02,
    'RST': 0x04,
    'PSH': 0x08,
    'ACK': 0x10,
    'URG': 0x20,
    'ECE': 0x40,
    'CWR': 0x80,
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class EthernetFrame:
    """Parsed Ethernet frame."""
    dst_mac: str
    src_mac: str
    ether_type: int
    ether_type_name: str
    payload: bytes
    vlan_id: Optional[int] = None


@dataclass
class IPv4Packet:
    """Parsed IPv4 packet."""
    version: int
    ihl: int
    dscp: int
    ecn: int
    total_length: int
    identification: int
    flags: int
    fragment_offset: int
    ttl: int
    protocol: int
    protocol_name: str
    checksum: int
    src_ip: str
    dst_ip: str
    options: bytes
    payload: bytes


@dataclass
class IPv6Packet:
    """Parsed IPv6 packet."""
    version: int
    traffic_class: int
    flow_label: int
    payload_length: int
    next_header: int
    next_header_name: str
    hop_limit: int
    src_ip: str
    dst_ip: str
    payload: bytes


@dataclass
class TCPSegment:
    """Parsed TCP segment."""
    src_port: int
    dst_port: int
    src_service: str
    dst_service: str
    seq_num: int
    ack_num: int
    data_offset: int
    flags: Dict[str, bool]
    window_size: int
    checksum: int
    urgent_pointer: int
    options: bytes
    payload: bytes


@dataclass
class UDPDatagram:
    """Parsed UDP datagram."""
    src_port: int
    dst_port: int
    src_service: str
    dst_service: str
    length: int
    checksum: int
    payload: bytes


@dataclass
class ICMPPacket:
    """Parsed ICMP packet."""
    type: int
    type_name: str
    code: int
    checksum: int
    rest_of_header: bytes
    payload: bytes


@dataclass
class ARPPacket:
    """Parsed ARP packet."""
    hardware_type: int
    protocol_type: int
    hw_addr_len: int
    proto_addr_len: int
    operation: int
    operation_name: str
    sender_mac: str
    sender_ip: str
    target_mac: str
    target_ip: str


@dataclass
class DNSPacket:
    """Parsed DNS packet."""
    transaction_id: int
    flags: int
    is_response: bool
    opcode: int
    questions: List[Dict[str, Any]]
    answers: List[Dict[str, Any]]
    authority: List[Dict[str, Any]]
    additional: List[Dict[str, Any]]


@dataclass
class NetworkFlow:
    """Represents a network flow (connection)."""
    src_ip: str
    src_port: int
    dst_ip: str
    dst_port: int
    protocol: str
    start_time: datetime
    last_seen: datetime = None
    packets_sent: int = 0
    packets_recv: int = 0
    bytes_sent: int = 0
    bytes_recv: int = 0
    state: str = "ACTIVE"

    def __post_init__(self):
        if self.last_seen is None:
            self.last_seen = self.start_time

    @property
    def duration(self) -> float:
        """Get flow duration in seconds."""
        return (self.last_seen - self.start_time).total_seconds()

    @property
    def flow_key(self) -> str:
        """Get unique flow identifier."""
        return f"{self.src_ip}:{self.src_port}->{self.dst_ip}:{self.dst_port}/{self.protocol}"


# =============================================================================
# PACKET PARSER
# =============================================================================

class PacketParser:
    """
    Parse network packets at various protocol layers.

    Supports parsing of:
    - Ethernet frames
    - IPv4/IPv6 packets
    - TCP/UDP segments
    - ICMP packets
    - ARP packets
    - DNS packets

    Example:
        >>> parser = PacketParser()
        >>> eth = parser.parse_ethernet(raw_frame)
        >>> if eth.ether_type == 0x0800:  # IPv4
        ...     ip = parser.parse_ipv4(eth.payload)
        ...     if ip.protocol == 6:  # TCP
        ...         tcp = parser.parse_tcp(ip.payload)
    """

    # ICMP Type names
    ICMP_TYPES = {
        0: 'Echo Reply',
        3: 'Destination Unreachable',
        4: 'Source Quench',
        5: 'Redirect',
        8: 'Echo Request',
        9: 'Router Advertisement',
        10: 'Router Solicitation',
        11: 'Time Exceeded',
        12: 'Parameter Problem',
        13: 'Timestamp Request',
        14: 'Timestamp Reply',
    }

    def format_mac(self, mac_bytes: bytes) -> str:
        """Format MAC address bytes to string."""
        return ':'.join(f'{b:02x}' for b in mac_bytes)

    def parse_ethernet(self, data: bytes) -> EthernetFrame:
        """
        Parse an Ethernet frame.

        Args:
            data: Raw Ethernet frame bytes

        Returns:
            Parsed EthernetFrame object
        """
        if len(data) < 14:
            raise ValueError("Data too short for Ethernet frame")

        dst_mac = self.format_mac(data[0:6])
        src_mac = self.format_mac(data[6:12])
        ether_type = struct.unpack('!H', data[12:14])[0]

        vlan_id = None
        payload_start = 14

        # Check for VLAN tag
        if ether_type == 0x8100:
            if len(data) < 18:
                raise ValueError("Data too short for VLAN tag")
            vlan_tci = struct.unpack('!H', data[14:16])[0]
            vlan_id = vlan_tci & 0x0FFF
            ether_type = struct.unpack('!H', data[16:18])[0]
            payload_start = 18

        return EthernetFrame(
            dst_mac=dst_mac,
            src_mac=src_mac,
            ether_type=ether_type,
            ether_type_name=ETHERNET_TYPES.get(ether_type, f'Unknown (0x{ether_type:04x})'),
            vlan_id=vlan_id,
            payload=data[payload_start:]
        )

    def parse_ipv4(self, data: bytes) -> IPv4Packet:
        """
        Parse an IPv4 packet.

        Args:
            data: Raw IPv4 packet bytes

        Returns:
            Parsed IPv4Packet object
        """
        if len(data) < 20:
            raise ValueError("Data too short for IPv4 header")

        version_ihl = data[0]
        version = version_ihl >> 4
        ihl = (version_ihl & 0x0F) * 4  # Header length in bytes

        if version != 4:
            raise ValueError(f"Not an IPv4 packet (version={version})")

        dscp_ecn = data[1]
        dscp = dscp_ecn >> 2
        ecn = dscp_ecn & 0x03

        total_length = struct.unpack('!H', data[2:4])[0]
        identification = struct.unpack('!H', data[4:6])[0]

        flags_fragment = struct.unpack('!H', data[6:8])[0]
        flags = flags_fragment >> 13
        fragment_offset = flags_fragment & 0x1FFF

        ttl = data[8]
        protocol = data[9]
        checksum = struct.unpack('!H', data[10:12])[0]

        src_ip = socket.inet_ntoa(data[12:16])
        dst_ip = socket.inet_ntoa(data[16:20])

        options = data[20:ihl] if ihl > 20 else b''
        payload = data[ihl:total_length]

        return IPv4Packet(
            version=version,
            ihl=ihl,
            dscp=dscp,
            ecn=ecn,
            total_length=total_length,
            identification=identification,
            flags=flags,
            fragment_offset=fragment_offset,
            ttl=ttl,
            protocol=protocol,
            protocol_name=IP_PROTOCOLS.get(protocol, f'Unknown ({protocol})'),
            checksum=checksum,
            src_ip=src_ip,
            dst_ip=dst_ip,
            options=options,
            payload=payload
        )

    def parse_ipv6(self, data: bytes) -> IPv6Packet:
        """
        Parse an IPv6 packet.

        Args:
            data: Raw IPv6 packet bytes

        Returns:
            Parsed IPv6Packet object
        """
        if len(data) < 40:
            raise ValueError("Data too short for IPv6 header")

        first_word = struct.unpack('!I', data[0:4])[0]
        version = first_word >> 28
        traffic_class = (first_word >> 20) & 0xFF
        flow_label = first_word & 0xFFFFF

        if version != 6:
            raise ValueError(f"Not an IPv6 packet (version={version})")

        payload_length = struct.unpack('!H', data[4:6])[0]
        next_header = data[6]
        hop_limit = data[7]

        src_ip = socket.inet_ntop(socket.AF_INET6, data[8:24])
        dst_ip = socket.inet_ntop(socket.AF_INET6, data[24:40])

        return IPv6Packet(
            version=version,
            traffic_class=traffic_class,
            flow_label=flow_label,
            payload_length=payload_length,
            next_header=next_header,
            next_header_name=IP_PROTOCOLS.get(next_header, f'Unknown ({next_header})'),
            hop_limit=hop_limit,
            src_ip=src_ip,
            dst_ip=dst_ip,
            payload=data[40:40 + payload_length]
        )

    def parse_tcp(self, data: bytes) -> TCPSegment:
        """
        Parse a TCP segment.

        Args:
            data: Raw TCP segment bytes

        Returns:
            Parsed TCPSegment object
        """
        if len(data) < 20:
            raise ValueError("Data too short for TCP header")

        src_port = struct.unpack('!H', data[0:2])[0]
        dst_port = struct.unpack('!H', data[2:4])[0]
        seq_num = struct.unpack('!I', data[4:8])[0]
        ack_num = struct.unpack('!I', data[8:12])[0]

        offset_reserved_flags = struct.unpack('!H', data[12:14])[0]
        data_offset = (offset_reserved_flags >> 12) * 4  # Header length in bytes
        flags_value = offset_reserved_flags & 0x1FF

        # Parse flags
        flags = {
            name: bool(flags_value & value)
            for name, value in TCP_FLAGS.items()
        }

        window_size = struct.unpack('!H', data[14:16])[0]
        checksum = struct.unpack('!H', data[16:18])[0]
        urgent_pointer = struct.unpack('!H', data[18:20])[0]

        options = data[20:data_offset] if data_offset > 20 else b''
        payload = data[data_offset:]

        return TCPSegment(
            src_port=src_port,
            dst_port=dst_port,
            src_service=WELL_KNOWN_PORTS.get(src_port, str(src_port)),
            dst_service=WELL_KNOWN_PORTS.get(dst_port, str(dst_port)),
            seq_num=seq_num,
            ack_num=ack_num,
            data_offset=data_offset,
            flags=flags,
            window_size=window_size,
            checksum=checksum,
            urgent_pointer=urgent_pointer,
            options=options,
            payload=payload
        )

    def parse_udp(self, data: bytes) -> UDPDatagram:
        """
        Parse a UDP datagram.

        Args:
            data: Raw UDP datagram bytes

        Returns:
            Parsed UDPDatagram object
        """
        if len(data) < 8:
            raise ValueError("Data too short for UDP header")

        src_port = struct.unpack('!H', data[0:2])[0]
        dst_port = struct.unpack('!H', data[2:4])[0]
        length = struct.unpack('!H', data[4:6])[0]
        checksum = struct.unpack('!H', data[6:8])[0]

        return UDPDatagram(
            src_port=src_port,
            dst_port=dst_port,
            src_service=WELL_KNOWN_PORTS.get(src_port, str(src_port)),
            dst_service=WELL_KNOWN_PORTS.get(dst_port, str(dst_port)),
            length=length,
            checksum=checksum,
            payload=data[8:length]
        )

    def parse_icmp(self, data: bytes) -> ICMPPacket:
        """
        Parse an ICMP packet.

        Args:
            data: Raw ICMP packet bytes

        Returns:
            Parsed ICMPPacket object
        """
        if len(data) < 8:
            raise ValueError("Data too short for ICMP header")

        icmp_type = data[0]
        code = data[1]
        checksum = struct.unpack('!H', data[2:4])[0]

        return ICMPPacket(
            type=icmp_type,
            type_name=self.ICMP_TYPES.get(icmp_type, f'Unknown ({icmp_type})'),
            code=code,
            checksum=checksum,
            rest_of_header=data[4:8],
            payload=data[8:]
        )

    def parse_arp(self, data: bytes) -> ARPPacket:
        """
        Parse an ARP packet.

        Args:
            data: Raw ARP packet bytes

        Returns:
            Parsed ARPPacket object
        """
        if len(data) < 28:
            raise ValueError("Data too short for ARP packet")

        hardware_type = struct.unpack('!H', data[0:2])[0]
        protocol_type = struct.unpack('!H', data[2:4])[0]
        hw_addr_len = data[4]
        proto_addr_len = data[5]
        operation = struct.unpack('!H', data[6:8])[0]

        operation_names = {1: 'Request', 2: 'Reply'}

        sender_mac = self.format_mac(data[8:14])
        sender_ip = socket.inet_ntoa(data[14:18])
        target_mac = self.format_mac(data[18:24])
        target_ip = socket.inet_ntoa(data[24:28])

        return ARPPacket(
            hardware_type=hardware_type,
            protocol_type=protocol_type,
            hw_addr_len=hw_addr_len,
            proto_addr_len=proto_addr_len,
            operation=operation,
            operation_name=operation_names.get(operation, f'Unknown ({operation})'),
            sender_mac=sender_mac,
            sender_ip=sender_ip,
            target_mac=target_mac,
            target_ip=target_ip
        )

    def parse_dns(self, data: bytes) -> DNSPacket:
        """
        Parse a DNS packet.

        Args:
            data: Raw DNS packet bytes

        Returns:
            Parsed DNSPacket object
        """
        if len(data) < 12:
            raise ValueError("Data too short for DNS header")

        transaction_id = struct.unpack('!H', data[0:2])[0]
        flags = struct.unpack('!H', data[2:4])[0]
        qd_count = struct.unpack('!H', data[4:6])[0]
        an_count = struct.unpack('!H', data[6:8])[0]
        ns_count = struct.unpack('!H', data[8:10])[0]
        ar_count = struct.unpack('!H', data[10:12])[0]

        is_response = bool(flags & 0x8000)
        opcode = (flags >> 11) & 0x0F

        # Parse questions
        offset = 12
        questions = []
        for _ in range(qd_count):
            name, offset = self._parse_dns_name(data, offset)
            qtype = struct.unpack('!H', data[offset:offset+2])[0]
            qclass = struct.unpack('!H', data[offset+2:offset+4])[0]
            offset += 4
            questions.append({
                'name': name,
                'type': qtype,
                'class': qclass
            })

        # Parse answers
        answers = []
        for _ in range(an_count):
            record, offset = self._parse_dns_record(data, offset)
            answers.append(record)

        # Parse authority
        authority = []
        for _ in range(ns_count):
            record, offset = self._parse_dns_record(data, offset)
            authority.append(record)

        # Parse additional
        additional = []
        for _ in range(ar_count):
            record, offset = self._parse_dns_record(data, offset)
            additional.append(record)

        return DNSPacket(
            transaction_id=transaction_id,
            flags=flags,
            is_response=is_response,
            opcode=opcode,
            questions=questions,
            answers=answers,
            authority=authority,
            additional=additional
        )

    def _parse_dns_name(self, data: bytes, offset: int) -> Tuple[str, int]:
        """Parse a DNS name from data."""
        labels = []
        original_offset = offset
        jumped = False

        while True:
            if offset >= len(data):
                break

            length = data[offset]

            if length == 0:
                offset += 1
                break
            elif (length & 0xC0) == 0xC0:
                # Compression pointer
                if not jumped:
                    original_offset = offset + 2
                pointer = struct.unpack('!H', data[offset:offset+2])[0] & 0x3FFF
                offset = pointer
                jumped = True
            else:
                offset += 1
                labels.append(data[offset:offset+length].decode('utf-8', errors='replace'))
                offset += length

        if jumped:
            offset = original_offset

        return '.'.join(labels), offset

    def _parse_dns_record(self, data: bytes, offset: int) -> Tuple[Dict, int]:
        """Parse a DNS resource record."""
        name, offset = self._parse_dns_name(data, offset)
        rtype = struct.unpack('!H', data[offset:offset+2])[0]
        rclass = struct.unpack('!H', data[offset+2:offset+4])[0]
        ttl = struct.unpack('!I', data[offset+4:offset+8])[0]
        rdlength = struct.unpack('!H', data[offset+8:offset+10])[0]
        rdata = data[offset+10:offset+10+rdlength]
        offset += 10 + rdlength

        # Parse common record types
        rdata_parsed = None
        if rtype == 1 and rdlength == 4:  # A record
            rdata_parsed = socket.inet_ntoa(rdata)
        elif rtype == 28 and rdlength == 16:  # AAAA record
            rdata_parsed = socket.inet_ntop(socket.AF_INET6, rdata)
        elif rtype in (2, 5, 12):  # NS, CNAME, PTR
            rdata_parsed, _ = self._parse_dns_name(data, offset - rdlength)

        return {
            'name': name,
            'type': rtype,
            'class': rclass,
            'ttl': ttl,
            'rdata': rdata_parsed if rdata_parsed else rdata.hex()
        }, offset


# =============================================================================
# TRAFFIC ANALYZER
# =============================================================================

class TrafficAnalyzer:
    """
    Analyze network traffic patterns and statistics.

    Tracks:
    - Protocol distribution
    - Port usage
    - IP address activity
    - Bandwidth usage
    - Connection patterns

    Example:
        >>> analyzer = TrafficAnalyzer()
        >>> analyzer.process_packet(parsed_packet)
        >>> stats = analyzer.get_statistics()
    """

    def __init__(self):
        """Initialize the traffic analyzer."""
        self.reset()

    def reset(self):
        """Reset all statistics."""
        self.start_time = datetime.now()

        # Counters
        self.total_packets = 0
        self.total_bytes = 0

        # Protocol stats
        self.protocols = Counter()
        self.eth_types = Counter()

        # IP stats
        self.src_ips = Counter()
        self.dst_ips = Counter()
        self.ip_pairs = Counter()

        # Port stats
        self.src_ports = Counter()
        self.dst_ports = Counter()

        # TCP flags
        self.tcp_flags = Counter()

        # Time series data (per-second)
        self.packets_per_second = defaultdict(int)
        self.bytes_per_second = defaultdict(int)

        # Flows
        self.flows: Dict[str, NetworkFlow] = {}

    def process_packet(self, packet_data: Dict[str, Any], size: int = 0):
        """
        Process a parsed packet and update statistics.

        Args:
            packet_data: Dictionary containing parsed packet info
            size: Size of packet in bytes
        """
        self.total_packets += 1
        self.total_bytes += size

        # Time tracking
        current_second = int(time.time())
        self.packets_per_second[current_second] += 1
        self.bytes_per_second[current_second] += size

        # Protocol tracking
        if 'protocol' in packet_data:
            self.protocols[packet_data['protocol']] += 1

        if 'eth_type' in packet_data:
            self.eth_types[packet_data['eth_type']] += 1

        # IP tracking
        src_ip = packet_data.get('src_ip')
        dst_ip = packet_data.get('dst_ip')

        if src_ip:
            self.src_ips[src_ip] += 1
        if dst_ip:
            self.dst_ips[dst_ip] += 1
        if src_ip and dst_ip:
            self.ip_pairs[(src_ip, dst_ip)] += 1

        # Port tracking
        src_port = packet_data.get('src_port')
        dst_port = packet_data.get('dst_port')

        if src_port:
            self.src_ports[src_port] += 1
        if dst_port:
            self.dst_ports[dst_port] += 1

        # TCP flag tracking
        if 'tcp_flags' in packet_data:
            for flag, is_set in packet_data['tcp_flags'].items():
                if is_set:
                    self.tcp_flags[flag] += 1

        # Flow tracking
        if src_ip and dst_ip and src_port and dst_port:
            protocol = packet_data.get('protocol', 'UNKNOWN')
            flow_key = f"{src_ip}:{src_port}->{dst_ip}:{dst_port}/{protocol}"

            if flow_key not in self.flows:
                self.flows[flow_key] = NetworkFlow(
                    src_ip=src_ip,
                    src_port=src_port,
                    dst_ip=dst_ip,
                    dst_port=dst_port,
                    protocol=protocol,
                    start_time=datetime.now()
                )

            flow = self.flows[flow_key]
            flow.packets_sent += 1
            flow.bytes_sent += size
            flow.last_seen = datetime.now()

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive traffic statistics."""
        duration = (datetime.now() - self.start_time).total_seconds()

        return {
            'summary': {
                'total_packets': self.total_packets,
                'total_bytes': self.total_bytes,
                'duration_seconds': duration,
                'packets_per_second': self.total_packets / max(duration, 1),
                'bytes_per_second': self.total_bytes / max(duration, 1),
                'active_flows': len(self.flows)
            },
            'protocols': dict(self.protocols.most_common(20)),
            'ethernet_types': dict(self.eth_types.most_common(10)),
            'top_source_ips': dict(self.src_ips.most_common(20)),
            'top_dest_ips': dict(self.dst_ips.most_common(20)),
            'top_source_ports': dict(self.src_ports.most_common(20)),
            'top_dest_ports': dict(self.dst_ports.most_common(20)),
            'tcp_flags_distribution': dict(self.tcp_flags),
            'top_ip_pairs': [
                {'src': pair[0], 'dst': pair[1], 'count': count}
                for pair, count in self.ip_pairs.most_common(20)
            ]
        }

    def get_bandwidth_timeline(self, granularity: int = 1) -> List[Dict[str, Any]]:
        """
        Get bandwidth usage over time.

        Args:
            granularity: Time bucket size in seconds

        Returns:
            List of time buckets with packet and byte counts
        """
        if not self.packets_per_second:
            return []

        min_time = min(self.packets_per_second.keys())
        max_time = max(self.packets_per_second.keys())

        timeline = []
        for t in range(min_time, max_time + 1, granularity):
            bucket_packets = sum(
                self.packets_per_second.get(t + i, 0)
                for i in range(granularity)
            )
            bucket_bytes = sum(
                self.bytes_per_second.get(t + i, 0)
                for i in range(granularity)
            )

            timeline.append({
                'timestamp': datetime.fromtimestamp(t).isoformat(),
                'packets': bucket_packets,
                'bytes': bucket_bytes,
                'bits_per_second': (bucket_bytes * 8) / granularity
            })

        return timeline

    def get_active_flows(self, timeout: int = 60) -> List[NetworkFlow]:
        """Get flows that were active within the timeout period."""
        cutoff = datetime.now() - timedelta(seconds=timeout)
        return [
            flow for flow in self.flows.values()
            if flow.last_seen > cutoff
        ]


# =============================================================================
# CONNECTION TRACKER
# =============================================================================

class ConnectionTracker:
    """
    Track and analyze network connections.

    Features:
    - TCP state machine tracking
    - Connection statistics
    - Anomaly detection

    Example:
        >>> tracker = ConnectionTracker()
        >>> tracker.process_tcp_packet(src_ip, src_port, dst_ip, dst_port, flags)
        >>> connections = tracker.get_active_connections()
    """

    # TCP states
    TCP_STATES = {
        'LISTEN', 'SYN_SENT', 'SYN_RECEIVED', 'ESTABLISHED',
        'FIN_WAIT_1', 'FIN_WAIT_2', 'CLOSE_WAIT', 'CLOSING',
        'LAST_ACK', 'TIME_WAIT', 'CLOSED'
    }

    def __init__(self, timeout: int = 300):
        """
        Initialize connection tracker.

        Args:
            timeout: Connection timeout in seconds
        """
        self.timeout = timeout
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()

    def _get_connection_key(self, src_ip: str, src_port: int,
                            dst_ip: str, dst_port: int) -> str:
        """Generate bidirectional connection key."""
        # Sort endpoints to make key bidirectional
        ep1 = (src_ip, src_port)
        ep2 = (dst_ip, dst_port)
        if ep1 < ep2:
            return f"{src_ip}:{src_port}<=>{dst_ip}:{dst_port}"
        return f"{dst_ip}:{dst_port}<=>{src_ip}:{src_port}"

    def process_tcp_packet(self, src_ip: str, src_port: int,
                          dst_ip: str, dst_port: int,
                          flags: Dict[str, bool], payload_size: int = 0):
        """
        Process a TCP packet and update connection state.

        Args:
            src_ip: Source IP address
            src_port: Source port
            dst_ip: Destination IP address
            dst_port: Destination port
            flags: TCP flags dictionary
            payload_size: Size of TCP payload
        """
        key = self._get_connection_key(src_ip, src_port, dst_ip, dst_port)
        now = datetime.now()

        with self.lock:
            if key not in self.connections:
                # New connection
                self.connections[key] = {
                    'endpoints': [(src_ip, src_port), (dst_ip, dst_port)],
                    'state': 'NEW',
                    'created': now,
                    'last_seen': now,
                    'packets': 0,
                    'bytes': 0,
                    'syn_count': 0,
                    'fin_count': 0,
                    'rst_count': 0
                }

            conn = self.connections[key]
            conn['last_seen'] = now
            conn['packets'] += 1
            conn['bytes'] += payload_size

            # Track flags
            if flags.get('SYN'):
                conn['syn_count'] += 1
            if flags.get('FIN'):
                conn['fin_count'] += 1
            if flags.get('RST'):
                conn['rst_count'] += 1

            # Update state machine
            self._update_state(conn, flags)

    def _update_state(self, conn: Dict[str, Any], flags: Dict[str, bool]):
        """Update connection state based on TCP flags."""
        current = conn['state']

        if flags.get('RST'):
            conn['state'] = 'CLOSED'
            return

        if current == 'NEW':
            if flags.get('SYN') and not flags.get('ACK'):
                conn['state'] = 'SYN_SENT'
        elif current == 'SYN_SENT':
            if flags.get('SYN') and flags.get('ACK'):
                conn['state'] = 'SYN_RECEIVED'
        elif current == 'SYN_RECEIVED':
            if flags.get('ACK') and not flags.get('SYN'):
                conn['state'] = 'ESTABLISHED'
        elif current == 'ESTABLISHED':
            if flags.get('FIN'):
                conn['state'] = 'FIN_WAIT_1'
        elif current == 'FIN_WAIT_1':
            if flags.get('FIN') and flags.get('ACK'):
                conn['state'] = 'TIME_WAIT'
            elif flags.get('ACK'):
                conn['state'] = 'FIN_WAIT_2'
        elif current == 'FIN_WAIT_2':
            if flags.get('FIN'):
                conn['state'] = 'TIME_WAIT'

    def get_active_connections(self) -> List[Dict[str, Any]]:
        """Get all active connections."""
        cutoff = datetime.now() - timedelta(seconds=self.timeout)

        with self.lock:
            # Cleanup old connections
            expired = [
                key for key, conn in self.connections.items()
                if conn['last_seen'] < cutoff or conn['state'] == 'CLOSED'
            ]
            for key in expired:
                del self.connections[key]

            return list(self.connections.values())

    def get_statistics(self) -> Dict[str, Any]:
        """Get connection statistics."""
        connections = self.get_active_connections()

        state_counts = Counter(c['state'] for c in connections)
        total_packets = sum(c['packets'] for c in connections)
        total_bytes = sum(c['bytes'] for c in connections)

        return {
            'total_connections': len(connections),
            'state_distribution': dict(state_counts),
            'total_packets': total_packets,
            'total_bytes': total_bytes,
            'avg_packets_per_connection': total_packets / max(len(connections), 1),
            'avg_bytes_per_connection': total_bytes / max(len(connections), 1)
        }

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect connection anomalies."""
        anomalies = []

        with self.lock:
            for key, conn in self.connections.items():
                # Check for SYN flood indicators
                if conn['syn_count'] > 10 and conn['state'] != 'ESTABLISHED':
                    anomalies.append({
                        'type': 'SYN_FLOOD_SUSPECT',
                        'connection': key,
                        'syn_count': conn['syn_count'],
                        'severity': 'HIGH'
                    })

                # Check for RST flood
                if conn['rst_count'] > 10:
                    anomalies.append({
                        'type': 'RST_FLOOD_SUSPECT',
                        'connection': key,
                        'rst_count': conn['rst_count'],
                        'severity': 'MEDIUM'
                    })

                # Check for long-lived connections with no data
                age = (datetime.now() - conn['created']).total_seconds()
                if age > 300 and conn['bytes'] < 100:
                    anomalies.append({
                        'type': 'IDLE_CONNECTION',
                        'connection': key,
                        'age_seconds': age,
                        'severity': 'LOW'
                    })

        return anomalies


# =============================================================================
# NETWORK SCANNER HELPER
# =============================================================================

class NetworkScanner:
    """
    Network scanning and discovery utilities.

    Note: Full scanning requires appropriate permissions.

    Example:
        >>> scanner = NetworkScanner()
        >>> hosts = scanner.ping_sweep("192.168.1.0/24")
        >>> ports = scanner.port_scan("192.168.1.1", range(1, 1025))
    """

    def __init__(self, timeout: float = 1.0):
        """
        Initialize network scanner.

        Args:
            timeout: Socket timeout in seconds
        """
        self.timeout = timeout

    def resolve_hostname(self, hostname: str) -> Optional[str]:
        """Resolve hostname to IP address."""
        try:
            return socket.gethostbyname(hostname)
        except socket.gaierror:
            return None

    def reverse_lookup(self, ip: str) -> Optional[str]:
        """Perform reverse DNS lookup."""
        try:
            return socket.gethostbyaddr(ip)[0]
        except (socket.herror, socket.gaierror):
            return None

    def check_port(self, ip: str, port: int) -> Tuple[bool, Optional[str]]:
        """
        Check if a port is open.

        Args:
            ip: Target IP address
            port: Port number to check

        Returns:
            Tuple of (is_open, service_name)
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)

            result = sock.connect_ex((ip, port))
            sock.close()

            if result == 0:
                service = WELL_KNOWN_PORTS.get(port, None)
                return True, service
            return False, None

        except socket.error:
            return False, None

    def get_local_interfaces(self) -> List[Dict[str, Any]]:
        """Get information about local network interfaces."""
        interfaces = []

        try:
            # Get hostname and addresses
            hostname = socket.gethostname()
            addresses = socket.getaddrinfo(hostname, None)

            seen = set()
            for addr in addresses:
                ip = addr[4][0]
                if ip not in seen and not ip.startswith('127.'):
                    seen.add(ip)
                    interfaces.append({
                        'address': ip,
                        'family': 'IPv4' if addr[0] == socket.AF_INET else 'IPv6',
                        'hostname': hostname
                    })

        except socket.error:
            pass

        return interfaces

    def calculate_network_range(self, cidr: str) -> List[str]:
        """
        Calculate all IP addresses in a CIDR range.

        Args:
            cidr: CIDR notation (e.g., "192.168.1.0/24")

        Returns:
            List of IP addresses
        """
        try:
            network = ipaddress.ip_network(cidr, strict=False)
            # Limit to avoid memory issues
            if network.num_addresses > 65536:
                raise ValueError("Network too large (max /16)")
            return [str(ip) for ip in network.hosts()]
        except ValueError as e:
            raise ValueError(f"Invalid CIDR notation: {e}")

    def get_service_banner(self, ip: str, port: int) -> Optional[str]:
        """
        Attempt to grab service banner from a port.

        Args:
            ip: Target IP address
            port: Port number

        Returns:
            Banner string if successful
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))

            # Send probe for certain services
            if port in (80, 8080):
                sock.send(b"HEAD / HTTP/1.0\r\n\r\n")
            elif port == 21:
                pass  # FTP sends banner automatically
            elif port == 22:
                pass  # SSH sends banner automatically
            else:
                sock.send(b"\r\n")

            banner = sock.recv(1024).decode('utf-8', errors='replace')
            sock.close()
            return banner.strip()

        except (socket.error, UnicodeDecodeError):
            return None


# =============================================================================
# MAIN NETWORK ANALYZER CLASS
# =============================================================================

class NetworkAnalyzer:
    """
    Main class combining all network analysis capabilities.

    Provides a unified interface for:
    - Packet parsing
    - Traffic analysis
    - Connection tracking
    - Network scanning

    Example:
        >>> analyzer = NetworkAnalyzer()
        >>>
        >>> # Parse a packet
        >>> parsed = analyzer.parse_packet(raw_data)
        >>>
        >>> # Get traffic statistics
        >>> stats = analyzer.traffic.get_statistics()
        >>>
        >>> # Scan a port
        >>> is_open, service = analyzer.scanner.check_port("192.168.1.1", 80)
    """

    def __init__(self):
        """Initialize the network analyzer."""
        self.parser = PacketParser()
        self.traffic = TrafficAnalyzer()
        self.connections = ConnectionTracker()
        self.scanner = NetworkScanner()

    def parse_packet(self, raw_data: bytes) -> Dict[str, Any]:
        """
        Parse a raw packet and return structured data.

        Automatically determines protocol and parses all layers.
        """
        result = {'raw_size': len(raw_data)}

        try:
            # Parse Ethernet
            eth = self.parser.parse_ethernet(raw_data)
            result['ethernet'] = {
                'src_mac': eth.src_mac,
                'dst_mac': eth.dst_mac,
                'type': eth.ether_type_name,
                'vlan': eth.vlan_id
            }

            # Parse network layer
            if eth.ether_type == 0x0800:  # IPv4
                ip = self.parser.parse_ipv4(eth.payload)
                result['ip'] = {
                    'version': 4,
                    'src': ip.src_ip,
                    'dst': ip.dst_ip,
                    'protocol': ip.protocol_name,
                    'ttl': ip.ttl
                }
                result['src_ip'] = ip.src_ip
                result['dst_ip'] = ip.dst_ip
                result['protocol'] = ip.protocol_name

                # Parse transport layer
                if ip.protocol == 6:  # TCP
                    tcp = self.parser.parse_tcp(ip.payload)
                    result['tcp'] = {
                        'src_port': tcp.src_port,
                        'dst_port': tcp.dst_port,
                        'flags': tcp.flags,
                        'seq': tcp.seq_num,
                        'ack': tcp.ack_num
                    }
                    result['src_port'] = tcp.src_port
                    result['dst_port'] = tcp.dst_port
                    result['tcp_flags'] = tcp.flags

                elif ip.protocol == 17:  # UDP
                    udp = self.parser.parse_udp(ip.payload)
                    result['udp'] = {
                        'src_port': udp.src_port,
                        'dst_port': udp.dst_port,
                        'length': udp.length
                    }
                    result['src_port'] = udp.src_port
                    result['dst_port'] = udp.dst_port

                    # Check for DNS
                    if udp.src_port == 53 or udp.dst_port == 53:
                        try:
                            dns = self.parser.parse_dns(udp.payload)
                            result['dns'] = {
                                'is_response': dns.is_response,
                                'questions': dns.questions,
                                'answers': dns.answers
                            }
                        except:
                            pass

                elif ip.protocol == 1:  # ICMP
                    icmp = self.parser.parse_icmp(ip.payload)
                    result['icmp'] = {
                        'type': icmp.type,
                        'type_name': icmp.type_name,
                        'code': icmp.code
                    }

            elif eth.ether_type == 0x0806:  # ARP
                arp = self.parser.parse_arp(eth.payload)
                result['arp'] = {
                    'operation': arp.operation_name,
                    'sender_mac': arp.sender_mac,
                    'sender_ip': arp.sender_ip,
                    'target_mac': arp.target_mac,
                    'target_ip': arp.target_ip
                }
                result['protocol'] = 'ARP'

            elif eth.ether_type == 0x86DD:  # IPv6
                ip6 = self.parser.parse_ipv6(eth.payload)
                result['ip'] = {
                    'version': 6,
                    'src': ip6.src_ip,
                    'dst': ip6.dst_ip,
                    'next_header': ip6.next_header_name,
                    'hop_limit': ip6.hop_limit
                }
                result['src_ip'] = ip6.src_ip
                result['dst_ip'] = ip6.dst_ip
                result['protocol'] = 'IPv6'

        except Exception as e:
            result['parse_error'] = str(e)

        return result

    def process_packet(self, raw_data: bytes):
        """Parse and process a packet through all analyzers."""
        parsed = self.parse_packet(raw_data)

        # Update traffic analyzer
        self.traffic.process_packet(parsed, len(raw_data))

        # Update connection tracker for TCP
        if 'tcp' in parsed:
            self.connections.process_tcp_packet(
                parsed.get('src_ip', ''),
                parsed.get('src_port', 0),
                parsed.get('dst_ip', ''),
                parsed.get('dst_port', 0),
                parsed.get('tcp_flags', {}),
                len(raw_data)
            )

        return parsed

    def get_statistics(self) -> Dict[str, Any]:
        """Get combined statistics from all analyzers."""
        return {
            'traffic': self.traffic.get_statistics(),
            'connections': self.connections.get_statistics(),
            'anomalies': self.connections.detect_anomalies()
        }


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """Command-line interface for the Network Analyzer."""
    print("=" * 60)
    print("NETWORK ANALYSIS TOOLKIT")
    print("=" * 60)
    print()

    # Initialize analyzer
    analyzer = NetworkAnalyzer()

    # Demo: Packet Parsing
    print("1. PACKET PARSING DEMO")
    print("-" * 40)

    # Create sample Ethernet + IPv4 + TCP packet
    sample_packet = bytes([
        # Ethernet header (14 bytes)
        0xff, 0xff, 0xff, 0xff, 0xff, 0xff,  # Dst MAC
        0x00, 0x11, 0x22, 0x33, 0x44, 0x55,  # Src MAC
        0x08, 0x00,                          # EtherType (IPv4)

        # IPv4 header (20 bytes)
        0x45, 0x00,                          # Version, IHL, DSCP
        0x00, 0x28,                          # Total length
        0x00, 0x01,                          # ID
        0x00, 0x00,                          # Flags, Fragment
        0x40,                                # TTL
        0x06,                                # Protocol (TCP)
        0x00, 0x00,                          # Checksum (not calculated)
        0xc0, 0xa8, 0x01, 0x01,              # Src IP (192.168.1.1)
        0xc0, 0xa8, 0x01, 0x02,              # Dst IP (192.168.1.2)

        # TCP header (20 bytes)
        0x00, 0x50,                          # Src port (80)
        0xc0, 0x01,                          # Dst port (49153)
        0x00, 0x00, 0x00, 0x01,              # Seq num
        0x00, 0x00, 0x00, 0x01,              # Ack num
        0x50, 0x12,                          # Data offset, flags (SYN+ACK)
        0x72, 0x10,                          # Window
        0x00, 0x00,                          # Checksum
        0x00, 0x00,                          # Urgent pointer
    ])

    parsed = analyzer.parse_packet(sample_packet)
    print("Parsed packet:")
    print(f"  Ethernet: {parsed.get('ethernet', {}).get('src_mac')} -> "
          f"{parsed.get('ethernet', {}).get('dst_mac')}")
    print(f"  IPv4: {parsed.get('ip', {}).get('src')} -> "
          f"{parsed.get('ip', {}).get('dst')}")
    print(f"  Protocol: {parsed.get('protocol')}")
    if 'tcp' in parsed:
        flags = [k for k, v in parsed['tcp']['flags'].items() if v]
        print(f"  TCP Ports: {parsed['tcp']['src_port']} -> {parsed['tcp']['dst_port']}")
        print(f"  TCP Flags: {flags}")
    print()

    # Demo: Network Scanner
    print("2. NETWORK SCANNER DEMO")
    print("-" * 40)

    scanner = analyzer.scanner

    # Get local interfaces
    print("Local interfaces:")
    interfaces = scanner.get_local_interfaces()
    for iface in interfaces:
        print(f"  {iface['address']} ({iface['family']})")

    # Resolve hostname
    hostname = "localhost"
    ip = scanner.resolve_hostname(hostname)
    print(f"\nResolved '{hostname}' -> {ip}")

    # Calculate network range
    print("\nNetwork range for 192.168.1.0/30:")
    try:
        hosts = scanner.calculate_network_range("192.168.1.0/30")
        for host in hosts[:5]:
            print(f"  {host}")
    except ValueError as e:
        print(f"  Error: {e}")
    print()

    # Demo: Traffic Analysis
    print("3. TRAFFIC ANALYSIS DEMO")
    print("-" * 40)

    # Process multiple packets
    for i in range(10):
        # Vary source/dest
        src_ip = f"192.168.1.{(i % 5) + 1}"
        dst_ip = f"192.168.1.{((i + 1) % 5) + 1}"

        packet_data = {
            'protocol': 'TCP' if i % 2 == 0 else 'UDP',
            'eth_type': 'IPv4',
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'src_port': 1024 + i,
            'dst_port': 80 if i % 3 == 0 else 443,
            'tcp_flags': {'SYN': i == 0, 'ACK': i > 0, 'FIN': False, 'RST': False}
        }
        analyzer.traffic.process_packet(packet_data, 100 + i * 10)

    stats = analyzer.traffic.get_statistics()
    print(f"Total packets processed: {stats['summary']['total_packets']}")
    print(f"Total bytes: {stats['summary']['total_bytes']}")
    print(f"Protocols: {stats['protocols']}")
    print(f"Top destination ports: {stats['top_dest_ports']}")
    print()

    # Demo: Port service lookup
    print("4. PORT SERVICE LOOKUP")
    print("-" * 40)
    for port in [22, 80, 443, 3306, 5432, 27017]:
        service = WELL_KNOWN_PORTS.get(port, 'Unknown')
        print(f"  Port {port}: {service}")
    print()

    print("=" * 60)
    print("Network Analysis Toolkit Demo Complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
