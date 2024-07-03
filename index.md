The migration to post-quantum cryptography is being held back by buggy servers
that do not correctly implement TLS. Due to a bug, these servers reject
connections that use post-quantum-secure cryptography, instead of negotiating
classical cryptography if they do not support post-quantum cryptography.

## What is the bug?

The Internet is currently beginning a migration to post-quantum secure
cryptography. This migration is important because large-scale quantum computers
will be powerful enough to break most public-key cryptosystems currently in use
and compromise digital communications on the Internet and elsewhere. It is
important to migrate to cryptography that cannot be broken by a quantum computer
_before_ quantum computers exist.

Unfortunately, some buggy servers are not prepared for clients to start
supporting post-quantum-secure cryptography. The TLS protocol contains a
mechanism for the server and client to negotiate the cryptographic algorithms
used for the connection based on which algorithms are mutally supported by both.
This means that correctly-implemented servers that have not yet added support
for the draft post-quantum algorithms should silently ignore the post-quantum
option, and select a different classical algorithm.

TLS ClientHello messages that offer post-quantum cryptography are larger than
classical ClientHello messages, and exceed the threshold for transmission in a
single packet. This means that a single call to TCP `read()` might not return
the entire ClientHello packet. This has always been possible in TCP, but it is
exacerbated by the larger ClientHello messages. Most buggy servers are not
prepared to have to call `read()` more than once to read the entire ClientHello.
This is still a bug even prior to the post-quantum migration, however, the bug is
much more commonly exposed when the larger post-quantum cryptography is in use.

## What is post-quantum-secure cryptography?

Modern public-key cryptography is secure in the face of a classical computer,
but can be broken by a quantum computer. Luckily, quantum computers don't exist
yet!

Post-quantum-secure cryptography (also shortened to post-quantum cryptography)
is cryptography that is resistant to quantum computers. Due to the power of
math, we can design, build, and verify this cryptography using only classical
(non-quantum) computers.

[NIST][nist] recently ran a [competition][nist-competition] to find the best
post-quantum cryptographic algorithms, and is in the process of standardizing
the winners. Some of the winning post-quantum cryptographic algorithms include
[Kyber][kyber] for key exchange and key encapsulation, and
[Dilithium][dilithium] for digital signatures. The IETF is
[standardizing][draft-kyber] how to integrate this cryptography into TLS.

## Why is this happening now?

Future quantum computers pose a risk to current Internet traffic through
store-then-decrypt attacks, in which attackers harvest encrypted sensitive
information now, and then decrypt it later, once quantum computers exist.
Mitigating this threat requires deploying a post-quantum key exchange mechanism
_now_.

To start mitigating the store-then-decrypt attack, [Chrome is in the
process][chrome-kyber] of rolling out a post-quantum key exchange.

## What is the status of post-quantum cryptography in browsers?

Post-quantum key exchange is rolling out in browsers. See
[Deployment](#deployment).

## What about authentication?

Quantum computers are capable of breaking the digital signature algorithms used
for authenticating digital communications today. Post-quantum signature
algorithms exist, but still have performance issues that make them difficult to
integrate into existing authentication systems, such as HTTPS certificates
(X.509). Luckily, unlike key exchange, the risk to authentication from a quantum
computer requires a sufficiently powerful quantum computer to actually exist,
since connections are authenticated in realtime. The store-then-decrypt attack
does not apply to authentication algorithms.

This means the migration to post-quantum secure authentication algorithms is less
urgent than key exchange. Due to the slow moving nature of the authentication
ecosystems on the Internet, such as the Web PKI, it is important to start this
migration soon.  However, there is no urgent threat to authentication, like
there is with key exchange.

## Does this bug apply to classical cryptography?

Servers that are not prepared for a ClientHello may incorrectly reject any
connection, especially if it split over two packets. This is less likely with
classical cryptography, but can happen. You can test for this by sending "half"
a ClientHello, and then waiting before sending the rest, and seeing if the
server correctly handles the connection, or if it resets the connection. This
bug is not specific to post-quantum cryptography, but is exacerbated by it.

## How does this affect the migration to post-quantum cryptography?

TLS contains a mechanism for negotiating the cryptographic algorithms used for
the connection. If things were working correctly, servers that don't support
postquantum cryptography would select a classical algorithm. Unfortunately,
these buggy servers fail on connections that _offer_ postquantum cryptography.
This means clients cannot start the rollout of postquantum cryptography without
risking breaking access to sites hosted on buggy servers.

## I'm not migrating to post-quantum cryptography until later. Why do I need to do anything now?

You should still [make sure][test-py] your server doesn't have this bug,
especially if you're a server implementor. Clients are starting to deploy
post-quantum cryptography, and while you don't need to update your server to
support draft standards, you don't want to prevent clients from being able to
start this transition, even if you aren't planning on participating right now.

## How can I tell if my server has this bug?

The best way to test your server is to use [this Python script][test-py] to test your server. Alternatively,
enable `chrome://flags/#enable-tls13-kyber` and then attempt to make an HTTPS
connection to your server from Chrome. If the connection fails with
ERR_CONNECTION_RESET or similar, the server is buggy. However, it is more likely
that network conditions may mask the bug when testing with Chrome, rather than
the Python script.

## Does this bug apply to QUIC?

The QUIC _protocol_ explicitly does not assume a single-packet ClientHello.
While it is technically possible to have this bug, it's much less likely due to
the nature of UDP. Also:
* QUIC is much newer so there's less long of a tail of buggy endpoints and
  middleware to worry about
* QUIC is typically deployed with a TCP fallback/race, so intolerance would look
  like a TCP fallback and be "fine"

## How do I patch the bug if I'm an implementor?

TLS messages contain a two-byte record length field at byte index 3. When
processing a ClientHello, servers should ensure they've called `read()` until
the connection has returned the full content of the message, as set in the
length field. If `read()` returns less bytes than the length of the message,
servers should loop until they've read the entire message.

## I'm a network administrator? How does this affect me?

You may be using a vendor that has buggy servers or a buggy middlebox. You
should contact your vendor and request that they patch their software. You can
provide this website for more information.

## Why are you calling this `tldr.fail`?

The bug is that servers "didn't read" the whole ClientHello, likely because it
was "too long" for a single packet, and then erroneously "fail" the connection.

## This isn't a vulnerability, why do you have a website?

This bug appears in a lot of servers and is holding back the Internet's
migration to post-quantum secure cryptography. If things were operating
correctly, clients could deploy support for post-quantum cryptography and then
servers would slowly opt-in. Instead, we're stuck, because buggy servers are
rejecting connections from properly implemented clients that deploy post-quantum
cryptography. These clients are then unable to load sites served by the buggy
server. This site serves as a reference for why the bug is important, and how to
identify and fix it.

---

## Deployment { id="deployment" }

Browser | Windows        | Mac           | Linux         | ChromeOS      | Android              | iOS
------- | -------------- | ------------- | ------------- | ------------- | -------------------- | -----------
Chrome  | Chrome 124     | Chrome 124    | Chrome 124    | Chrome 124    | 10% since Chrome 118 | n/a[^1]
Firefox | `about:config` |`about:config` |`about:config` | n/a[^2]       |`about:config`        | n/a[^1]
Safari  | Unavailable    | Unavailable   | Unavailable   | n/a[^2]       | n/a[^3]              | Unavailable

## Known Incompatibilities

Product | Status | Discovered | Via         | Patched | Links
------- | ------ | ---------- | ----------- | ------- | ------------------
Vercel  | ✅     | 2023-08-15 | Chrome Beta | 2023-08-23         | [Twitter][twitter-vercel]
ZScalar | ✅     | 2023-08-17 | Chrome Beta | 2023-09-28         |
Cisco   |        | 2024-04-23 | Chrome 124 | Unknown            | [Cisco Bug][cisco-bug]
Envoy   | ✅     | 2024-04-29 | Chrome 124  | n/a (config-only ) | [Github][envoy-github-issue]
Ingress Nginx | ❌ | 2024-06-03 | Chrome 124 |  | [Github][ingress-nginx-github-issue]

_Table last updated 2024-07-03_

[^1]: All browsers on iOS internally use WebKit, and so the rollout is dependent on Apple.
[^2]: There is no Firefox or Safari for ChromeOS.
[^3]: There is no Safari for Android.


[test-py]: https://github.com/dadrian/tldr.fail/blob/main/tldr_fail_test.py
[chrome-kyber]: https://blog.chromium.org/2023/08/protecting-chrome-traffic-with-hybrid.html
[draft-kyber]: https://datatracker.ietf.org/doc/html/draft-cfrg-schwabe-kyber
[kyber]: https://pq-crystals.org/kyber/
[dilithium]: https://pq-crystals.org/dilithium/index.shtml
[nist-competition]: https://csrc.nist.gov/projects/post-quantum-cryptography
[nist]: https://nist.gov

[twitter-vercel]: https://twitter.com/juliusrickert/status/1691023958999760896
[cisco-bug]: https://quickview.cloudapps.cisco.com/quickview/bug/CSCwj82736
[envoy-github-issue]: https://github.com/envoyproxy/envoy/issues/33850
[ingress-nginx-github-issue]: https://github.com/kubernetes/ingress-nginx/issues/11424#issue-2331992771