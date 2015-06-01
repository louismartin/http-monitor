# Thread object which generates random entries
# and writes to a simulation log to test the LogHandler

from time import sleep
from datetime import datetime
from threading import Thread
import random


class EntryGenerator(Thread):
    """Generates random entries and writes to a simulation log"""

    def __init__(self, logPath, rate):
        """Constructor:
        :param logPath: path of the simulation log
        :param rate: entry generation rate in number of entries per second"""
        Thread.__init__(self)
        self.logPath = logPath
        # Set to False to stop the generation loop and end the thread (stop())
        self.running = True
        # Set to False to stop generating whithout ending the thread
        self.generating = True
        self.ips = ["::1", "192.168.0.110", "127.0.0.1", "60.242.26.14"]
        self.methods = ["GET", "GET", "GET", "POST", "POST", "PUT", "DELETE"]
        self.sections = ["/img", "/captcha", "/css", "/foo", "/foo", "/bar"]
        self.codes = ["200", "200", "200", "200", "200", "304", "403", "404"]
        # Number of entries generated per seconds
        self.rate = rate

    def generate_entry(self, entryTime):
        """Returns a random entry string at the time given in parameter
        :param entryTime: Time of the generated entry"""
        # Chooses randomly between predefined ips or a random one
        ip = random.choice([random.choice(self.ips), self.random_ip()])
        method = random.choice(self.methods)
        # Randomize section choose first part as random
        # and then choose if it's a file or if there will be another section
        section = random.choice(self.sections) \
            + random.choice([".html",
                            random.choice(self.sections)+".html"])
        code = random.choice(self.codes)
        size = random.randint(10, 100000)
        return ('%s - - [%s +1000] "%s %s HTTP/1.1" %s %d\n'
                % (ip,
                   entryTime.strftime("%d/%b/%Y:%H:%M:%S"),
                   method,
                   section,
                   code,
                   size))

    def write_entry(self, entryTime):
        """Write a random entry to the simulation log file
        :param entryTime: Time of the generated entry"""
        try:
            with open(self.logPath, "a") as generatedLog:
                    generatedLog.write(self.generate_entry(entryTime))
        except:
            print("ERROR: Cannot write to the log file")

    def write(self, entry):
        """Writes pre-written entry given in parameter to simulation log file
        :param entry: Formatted string representing an entry"""
        try:
            with open(self.logPath, "a") as generatedLog:
                    generatedLog.write(entry)
        except:
            print("ERROR: Cannot write to the log file")

    def clear_log(self):
        """Clear simulation log of all entries"""
        try:
            open(self.logPath, "w").close()
        except:
            print("ERROR: Cannot open the log file")

    def random_ip(self):
        """Returns a random IP as a string"""
        return str(random.randint(0, 255)) + "." + str(random.randint(0, 255)) \
            + "." + str(random.randint(0, 255)) + "." \
            + str(random.randint(0, 255))

    def stop(self):
        """Stops the generation loop and thus stop the thread"""
        self.running = False

    def stop_generating(self):
        """Stops generating but the loop and thread keep running"""
        self.generating = False

    def start_generating(self):
        """Start generating (again)"""
        self.generating = True

    def run(self):
        """Main generation loop"""
        while(self.running):
            if self.generating:
                now = datetime.now()
                self.write_entry(now)
            # Sleep on average during (1/rate) seconds
            sleep(random.random()*2/self.rate)
