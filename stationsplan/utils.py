from random import choice
import string


def random_string(length, allowed_chars=string.printable):
    return "".join([choice(allowed_chars) for i in range(length)])
