#!/usr/bin/env python3
#
#   Copyright 2023 Google
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#
# Usage: python3 tldr_fail_test.py ${HOSTNAME}
#
# You can optionally pass the destination IP with --addr
#
# Author: davidben [at] chromium [dot] org

import argparse
import socket
import time

def u8_prefix(b):
    assert len(b) < (1 << 8)
    return len(b).to_bytes(1, byteorder='big') + b

def u16_prefix(b):
    assert len(b) < (1 << 16)
    return len(b).to_bytes(2, byteorder='big') + b

def u24_prefix(b):
    assert len(b) < (1 << 24)
    return len(b).to_bytes(3, byteorder='big') + b


# A sample ClientHello body up to the extension list.
CLIENT_HELLO_PREFIX = bytes.fromhex(
    "030381bd99579ae1430858bb32549d4d3d53fbd49946fc76eb1627db" +
    "73f36a71ce8220a1faacf5f53904ca5399c27b7e9816b110dbea1578" +
    "56572c942bf2314d3256240022130113021303c02bc02fc02cc030cc" +
    "a9cca8c009c013c00ac014009c009d002f00350100")

# Sample keys.
X25519_KEY = bytes.fromhex(
    "53db02a3c0178ceef2d76cab96e45160a0e934a3122989edb7f1972f28e0e241")
X25519_KYBER768_KEY = bytes.fromhex(
    "8b782040433f595488fcfccb1f9e708f669409b40261" +
    "29290a605b79e3fbf704ad414f5d17586ac6c1057bad1f89b48c9a00e4b0" +
    "1ecf929dfd341339b0556440039af86ba17a58fb9797d9d993f2b586a4c8" +
    "0a6b1b031fa8c36cd97757d4536d446ef6da428d38b3f4ab585b32021555" +
    "19b9c4391505940a1566152b76f53903c2c3b5e5f2a67d0041c2206eb524" +
    "182880097e3ca636424baac29db08151e4b62cc6aa15ca5b67890b5cb1c6" +
    "3091772fdef29bb81815f4e2c871f736bcf04bac4a8650a091b769359909" +
    "b436c81348aba3b2b815699048df605a8c124e1843278ea5cdc1369d8094" +
    "9e0798b6544a599eb8a02b583b7e82115fb0c7430c925a7919b9dab7dbe8" +
    "5c8e799ca033ab18da6e1d5b3da8facf9b4b63e478100dc274a281387519" +
    "92222459a1317bd146bc5e34b346c99e17a8ad3558734dc993844c83e7e6" +
    "b5edec11b8249f54cb84ee36253682a90f951829b8b55a54409a62459514" +
    "1eeb9b9da2162b00c6436459753b087782f828e56c4cad226811d810df80" +
    "4262aa9f4c371799b27e9725830868859075506c364ad02518dd61c79865" +
    "1534b7a051f815bc8912b9b60efad57fb9a71f0eb422d731cc6df706e03a" +
    "b8bc6988d8b6854002ce18f98ac16069a63054cdc8c6a5b264c8a144f1b1" +
    "b3beb7818d48b38372905df2002120c7d26258c13a3f06d08e8b4a0227f2" +
    "7945119598a6642d52ab1fa02b715b080dd92a66aa072d61b31782bcb195" +
    "13ac593098dc306ae81eb31342c4fba821f056552729ca70b9ebfcbcb27a" +
    "2f9e169374987b83b73107918cbe467a8ca82ded47618967ad87d85ac1bb" +
    "5fd318cb647bc68b397b3cb50fca1a7c97641ec09c36f3eb2e500a63c201" +
    "c83f3a9a468207deec2ffa59c715f52541a1142f679ee485c9c1f5601ad8" +
    "4bf3b01e6ad7918ce3c7be0a995248a8bb27756b874985e62b845994d5c0" +
    "37ce8855fd75627dc0a0b2a8c9b29a01015c9276e2caac5918febb1652e9" +
    "0e6d39ce6fe46693cb8d2baa44896a55ff24713816ad82b5ce125c34fd14" +
    "13f33b138df997c9b5cdee78b2ab09220384adb9816fd7527e5b27bb1132" +
    "a76d8a8c6406884bd916178c984e2877dae1871c39cd566a56e075408b00" +
    "c23bc739fe521a217b00054b0c86e8094ff4af9687cbf403165fb4989dd0" +
    "47efc5b9e71a277070c4a2a98aaba08d57b0515f71bcfbfa5eeca892c569" +
    "a95b180fdc393d79dc045ed459df6218df093c9f328a17c15717793d8822" +
    "cf31b07ac6c9a8b0ac2b2e28bbaeecbe365036d88c3d9429b45c6191dd55" +
    "29433abaebf803d6572b9517cf8ec39d8388a17f20b9e9517b3a199325f2" +
    "936f79ccadf02b90c609ee46b74c911cd3c8c45d9066af029845b0186444" +
    "60643a8b4123cf61713799fa40f11708f427253829b2f6288d301220d112" +
    "567a865f284c6b98c98fea3a9b5251bf8ed39d6ee776f95348ef279be227" +
    "01b6b4a602d39b416c0d42512b68437b72845d3272cb3b7c30d696abb341" +
    "0c7e400afd563f4825bd64827598423268b42ee6753f7f997329aa82f8e2" +
    "517b0987cac18ae3f65ca556783b6308b8883553f29ea0233ca2c60d9dcc" +
    "0bf4abc36c41b7bbeaacc7b78007a35a9afcb398fa863ca3175ea1cd7c75" +
    "c86db7bb81f552f6c472a62439e326c933bcacfff364e9b1b2bbabc637ff" +
    "00116e3f1ecce8a68ebbb2edd867a3ce351831d999d38d11")

# EMS, RI, ec_point_formats, session_ticket, signature_algorithms,
# psk_key_exchange_modes, and supported_versions from a sample ClientHello.
OTHER_EXTENSIONS = bytes.fromhex(
    "00170000ff01000100000b0002010000230000000d00140012040308" +
    "040401050308050501080606010201002d00020101002b0009080304" +
    "030303020301")

def make_extension(typ, body):
    return typ.to_bytes(2, byteorder='big') + u16_prefix(body)

def make_server_name(name):
    body = u16_prefix(b"\x00" + u16_prefix(name.encode("ascii")))
    return make_extension(0, body)

def make_supported_groups(groups):
    body = u16_prefix(b"".join(g.to_bytes(2, byteorder='big') for g in groups))
    return make_extension(10, body)

def make_key_share_entry(group, val):
    return group.to_bytes(2, byteorder='big') + u16_prefix(val)

def make_key_share(entries):
    body = u16_prefix(
        b"".join(make_key_share_entry(group, val) for group, val in entries))
    return make_extension(51, body)

def make_client_hello(name, kyber):
    # X25519, P-256, P-384
    groups = [29, 23, 24]
    entries = [(29, X25519_KEY)]
    if kyber:
        groups = [0x6399] + groups
        entries = [(0x6399, X25519_KYBER768_KEY)] + entries

    extensions = u16_prefix(
        make_supported_groups(groups) + make_key_share(entries) +
        make_server_name(name) + OTHER_EXTENSIONS)

    client_hello = b"\x01" + u24_prefix(CLIENT_HELLO_PREFIX + extensions)    
    return b"\x16\x03\x01" + u16_prefix(client_hello)

parser = argparse.ArgumentParser(prog="fragmented_client_hello")
parser.add_argument("host")
parser.add_argument("--addr")
parser.add_argument("--port", type=int, default=443)
args = parser.parse_args()

if args.addr is None:
    addr = (args.host, args.port)
else:
    addr = (args.addr, args.port)

client_hello = make_client_hello(args.host, kyber=True)

print(f"About to send a large TLS ClientHello ({len(client_hello)} bytes) to {addr[0]}:{addr[1]}.")
print()
print("The server should respond with a TLS ServerHello, which will be some")
print("byte string beginning with b'\\x16\\x03\\x03'. If it closes the")
print("connection or sends something else, the server is misbehaving.")
print()

print("Sending the ClientHello in a single write:")
sock = socket.create_connection(addr)
try:
    sock.send(client_hello)
    print(sock.recv(256))
except Exception as e:
    print(e)
print()

print("Sending the ClientHello in two separate writes:")
sock = socket.create_connection(addr)
try:
    half = len(client_hello)//2
    sock.send(client_hello[:half])
    time.sleep(1)
    sock.send(client_hello[half:])
    print(sock.recv(256))
except Exception as e:
    print(e)
print()

client_hello = make_client_hello(args.host, kyber=False)

print(f"Repeating the process with a smaller ClientHello ({len(client_hello)} bytes).")
print("This ClientHello would usually be sent in a single packet, but it")
print("demonstrates that the bug is not triggered by the size of the")
print("ClientHello, but whether it comes in across multiple reads.")
print("(Note this ClientHello is smaller than a ClientHello from browsers")
print("today. This script does not reproduce some padding behavior.)")
print()

print("Sending the ClientHello in a single write:")
sock = socket.create_connection(addr)
sock.send(client_hello)
try:
    print(sock.recv(256))
except Exception as e:
    print(e)
print()

print("Sending the ClientHello in two separate writes:")
sock = socket.create_connection(addr)
try:
    half = len(client_hello)//2
    sock.send(client_hello[:half])
    time.sleep(1)
    sock.send(client_hello[half:])
    print(sock.recv(256))
except Exception as e:
    print(e)
