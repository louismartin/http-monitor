# -*-coding:Latin-1 -*

import unittest


class LogEntry:

    def __init__(ip, time, method, section, size):
        self.ip = ip
        self.time = time
        self.method = method
        self.section = section
        self.size = size

class TestMonitor(unittest.TestCase):

    def test_log_entry:
        print("TODO: test log entry")

if __name__ == '__main__':
    unittest.main()
    #        self.logPath = "C:/Louis/Programming/Web/wamp/logs/access.log"

    
    
