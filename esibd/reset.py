"""Reset settings saved in registry. Use to test fresh deployment.
Call using: python -m esibd.reset"""
from esibd.const import qSet

def reset():
    qSet.clear()

if __name__ == '__main__':
    reset()
