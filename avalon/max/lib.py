'''
Created on 2017.9.26

Standalone helper functions

@author: noflame
'''
import MaxPlus as MP


def unique_namespace(namespace, format="%02d", prefix="", suffix=""):
    unique = prefix + (namespace + format % 1)
    MXS = 'uniqueName "%s" numDigits:%s' % (unique, format[2])
    rel = MP.Core.EvalMAXScript(MXS)
    unique = rel.Get()
    return unique + suffix


def maxversion():
    major, minor, patch = MP.Core.EvalMAXScript("maxversion()").Get()
    major = int("20{}".format((major / 1000 - 2)))
    return (major, minor, patch)
