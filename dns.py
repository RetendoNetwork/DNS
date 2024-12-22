import os
import signal
from dnslib import DNSRecord, RR, A, QTYPE
from dnslib.server import DNSServer
from dotenv import load_dotenv
from tabulate import tabulate
from termcolor import colored

load_dotenv()

def handle_sigterm(signum, frame):
    exit()

signal.signal(signal.SIGTERM, handle_sigterm)

address_map = {}

for variable, value in os.environ.items():
    if variable.startswith("DNS_MAP_"):
        hostname = variable.split("DNS_MAP_")[1]
        address_map[hostname] = value

if "conntest.nintendowifi.net" not in address_map:
    default_address = os.getenv("DNS_DEFAULT_ADDRESS")
    if not default_address:
        print(colored(
            "Mapping for conntest.nintendowifi.net not found and no default address set. "
            "Set either DNS_DEFAULT_ADDRESS or DNS_MAP_conntest.nintendowifi.net",
            "red",
            attrs=["bold"]
        ))
        exit()
    address_map["conntest.nintendowifi.net"] = default_address

if "account.nintendo.net" not in address_map:
    default_address = os.getenv("DNS_DEFAULT_ADDRESS")
    if not default_address:
        print(colored(
            "Mapping for account.nintendo.net not found and no default address set. "
            "Set either DNS_DEFAULT_ADDRESS or DNS_MAP_account.nintendo.net",
            "red",
            attrs=["bold"]
        ))
        exit()
    address_map["account.nintendo.net"] = default_address

udp_port = int(os.getenv("UDP_PORT", 0))
tcp_port = int(os.getenv("TCP_PORT", 0))

if udp_port == 0 and tcp_port == 0:
    print(colored("No server port set. Set one of SSSL_UDP_PORT or SSSL_TCP_PORT", "red", attrs=["bold"]))
    exit()

if udp_port == tcp_port:
    print(colored("UDP and TCP ports cannot match", "red", attrs=["bold"]))
    exit()

if udp_port == 0:
    print(colored("UDP port not set. One will be randomly assigned", "yellow", attrs=["bold"]))

if tcp_port == 0:
    print(colored("TCP port not set. One will be randomly assigned", "yellow", attrs=["bold"]))

class DNSHandler:
    def __call__(self, request, handler):
        query = DNSRecord.parse(request)
        question = query.q.qname

        name = str(question).rstrip(".")
        if name in address_map:
            response = query.reply()
            response.add_answer(RR(name, QTYPE.A, rdata=A(address_map[name]), ttl=300))
            return response.pack()
        return query.reply().pack()

udp_server = None
tcp_server = None

if udp_port != 0:
    udp_server = DNSServer(DNSHandler(), port=udp_port, address="0.0.0.0", tcp=False)

if tcp_port != 0:
    tcp_server = DNSServer(DNSHandler(), port=tcp_port, address="0.0.0.0", tcp=True)

table_data = [["Protocol", "Address"]]
if udp_server:
    table_data.append(["UDP", f"0.0.0.0:{udp_port}"])
if tcp_server:
    table_data.append(["TCP", f"0.0.0.0:{tcp_port}"])

print(colored("DNS listening on the following addresses", "green", attrs=["bold"]))
print(tabulate(table_data, headers="firstrow", tablefmt="grid"))

if udp_server:
    udp_server.start_thread()

if tcp_server:
    tcp_server.start_thread()

try:
    print(colored("Press Ctrl+C to stop DNS Server.", "yellow", attrs=["bold"]))
    while True:
        signal.signal(signal.SIGINT, handle_sigterm)
        signal.signal(signal.SIGTERM, handle_sigterm)
except KeyboardInterrupt:
    print(colored("\nServer shutting down", "red", attrs=["bold"]))

except KeyboardInterrupt:
    print(colored("\nServer shutting down", "red", attrs=["bold"]))