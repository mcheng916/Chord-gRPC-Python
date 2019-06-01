import hashlib


def chordHash(ipAddr, sha1Bit = 160):
    return hashlib.sha1(ipAddr).hexidigest()



