The migration to postquantum cryptography is being held back by buggy servers
that do not correctly implement TLS. These servers reject connections that use
postquantum-secure cryptography, instead of negotiating classical cryptography
if they do not support the experiment postquantum algorithms.

## What is the bug?

The Internet is currently beginning a migration to post-quantum secure
cryptography. This migration is important because large-scale quantum computers
will be powerful enough to break most public-key cryptosystems currently in use
and compromise digital communications on the Internet and elsewhere. It is
important to migrate to cryptography that cannot be broken by a quantum computer
_before_ quantum computers exist.

Unfortunately, some buggy servers are not prepared for clients to start
supporting postquantum-secure cryptography. The TLS protocol contains a
mechanism for the server and client to negotiate the cryptographic algorithms
used for the connection based on which algorithms are mutally supported by both.
This means that correctly-implemented servers that have no yet added support for
the draft postquantum algorithms should silently ignore the postquantum option,
and select a different classical algorithm.

TLS ClientHello messages that offer postquantum cryptography are larger than
classical ClientHello messages, and exceed the threshold for transmission in a
single packet. This means that a single call to TCP `read()` might not return
the entire ClientHello packet. This has always been possible in TCP, but it is
exacerbated by the larger ClientHello messages. Most buggy servers are not
prepared to have to call `read()` more than once to read the entire ClientHello.
This is still a bug even prior to the postquantum migration, however, the bug is
much more commonly exposed when the larger postquantum cryptography is in use.

## What is postquantum-secure cryptography?

Modern public-key cryptography is secure in the face of a classical computer,
but can be broken by a quantum computer. Luckily, quantum computers don't exist
yet!

## Why is this happening now?

Future quantum computers pose a risk to current Internet traffic through
store-then-decrypt attacks, in which attackers harvest encrypted sensitive
information now, and then decrypt it later, once quantum computers exist.
Mitigating this threat requires deploying a postquantum key exchange mechanism
_now_.

## What about authentication?

Quantum computers are capable of breaking the digital signature algorithms used for authenticating
digital communications today. Postquantum signature algorithms exist, but still
have performance issues that make them difficult to integrate into existing
authentication systems, such as HTTPS certificates (X.509). Luckily, unlike key
exchange, the risk to authentication from a quantum computer requires a quantum
computer to actually exist, since connections are authenticated in realtime. The
store-then-decrypt attack does not apply to authentication algorithms.

This means the migration to postquantum secure authentication algorithms is less
urgent than key exchange. Due to the slow moving nature of the authentication
ecosystems on the Internet, such as the Web PKI, it is important to start this
migration soon.  However, there is no urgent threat to authentication, like
there is with key exchange.

## How do I patch the bug if I'm an implementor?

TLS messages contain a two-byte record length field at byte index 3. When
processing a ClientHello, servers should ensure they've called `read()` until
the connection has returned the full content of the message, as set in the
length field. If `read()` returns less bytes than the length of the message,
servers should loop until they've read the entire message.

## Does this bug apply to classical cryptography?

Servers that are not prepared for a ClientHello may incorrectly reject any
connection, especially if it split over two packets. This is less likely with
classical cryptography, but can happen. You can test for this by sending "half"
a ClientHello, and then waiting before sending the rest, and seeing if the
server correctly handles the connection, or if it resets the connection. This
bug is not specific to postquantum cryptography, but is exacerbated by it.

## How does this affect the migration to postquantum cryptography?

TODO

## I'm ot migrating to postquantum cryptography until later. Why do I need to do anything now?

TODO

## Why are you calling this `tldr.fail`?

The bug is that servers don't read the whole ClientHello, likely because it was
"too long" for a single packet.

## This isn't a vulnerability, why do you have a website?

This bug appears in a lot of servers and is holding back the Internet's
migration to postquantum secure cryptography. If things were operating
correctly, clients could deploy support for postquantum cryptography and then
servers would slowly opt-in. Instead, we're stuck, because properly implemented
clients that deploy postquantum cryptography can completely fail to open
connections to buggy servers.
