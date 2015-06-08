# The LogHandler object is a thread that handles
# the processing and monitoring of the log

from log_entry import LogEntry
from collections import deque, Counter
from time import sleep
from datetime import datetime
from datetime import timedelta
from threading import Thread
import os


class LogHandler(Thread):
    """Handles the processing and monitoring of the log"""

    def __init__(self,
                 logPath,
                 refreshPeriod,
                 alertThreshold,
                 monitorDuration):
        """Constructor
        :param logPath: path of the log file
        :param refreshPeriod: Period to check on the log in seconds
        :param alertThreshold: Number of hits/minute to trigger alarm
        :param monitorDuration: Data is only kept during this time in seconds
        """

        Thread.__init__(self)
        self.logPath = logPath
        self.refreshPeriod = refreshPeriod
        self.alertThreshold = alertThreshold
        self.monitorDuration = monitorDuration
        # initialize lastReadTime: current time - monitorDuration
        # (to only process this time frame)
        delta = timedelta(seconds=self.monitorDuration)
        self.lastReadTime = datetime.now() - delta
        # Attribute where we will store the log entries
        # (list-like container with fast appends and pops on either end)
        self.log = deque()
        # Set it to False to stop the monitoring loop (call stop())
        self.running = True
        self.hits = 0
        self.size = 0
        # Counter: dict subclass for counting hashable objects
        self.sections = Counter()
        self.ips = Counter()
        self.methods = Counter()
        self.codes = Counter()
        self.alertStatus = False
        # Set it to False to stop displaying messages in the console
        self.printStatus = True
        # Alerts messages will be stored in this string
        self.alerts = ""

    def add_entry(self, entry):
        """Adds an LogEntry to the handler and updates stats"""
        if entry.parsed:
            self.log.append(entry)
            self.hits += 1
            self.size += entry.size
            self.sections[entry.section] += 1
            self.ips[entry.ip] += 1
            self.methods[entry.method] += 1
            self.codes[entry.code] += 1

    def delete_entry(self):
        """Deletes oldest entry of the handler and updates stats"""
        entry = self.log.popleft()
        self.hits -= 1
        self.size -= entry.size

        # When a Counter key has a value of 0 I prefer removing it
        self.sections[entry.section] -= 1
        if self.sections[entry.section] == 0:
            del self.sections[entry.section]

        self.ips[entry.ip] -= 1
        if self.ips[entry.ip] == 0:
            del self.ips[entry.ip]

        self.methods[entry.method] -= 1
        if self.methods[entry.method] == 0:
            del self.methods[entry.method]

        self.codes[entry.code] -= 1
        if self.codes[entry.code] == 0:
            del self.codes[entry.code]

    def read(self):
        """Reads the log file and adds entries
        that happened during the monitored time frame"""
        # Store lastReadTime value temporarily (attribute updated next line)
        lastReadTime = self.lastReadTime
        # Update the lastReadTime before reading file
        # so as not to miss any value next time
        now = datetime.now()
        # Remove microseconds
        self.lastReadTime = datetime(now.year,
                                     now.month,
                                     now.day,
                                     now.hour,
                                     now.minute,
                                     now.second)
        try:
            with open(self.logPath, "r") as logFile:
                lines = logFile.readlines()

            # iterate over lines in reversed order (most recent first)
            # of entries in the monitored time frame
            i = 1
            while i <= len(lines) and LogEntry(lines[-i]).time >= lastReadTime:
                logEntry = LogEntry(lines[-i])
                if logEntry.time > lastReadTime:
                    self.add_entry(logEntry)

                # Entries dated at the same second might have been added
                elif logEntry.time == lastReadTime:
                    if logEntry not in self.log:
                        self.add_entry(logEntry)
                i += 1
        except:
            print("*** ERROR: LogHandler cannot read the log file ***\n\n")
            self.running = False
            input("PRESS ENTER TO EXIT")

    def drop_old_entries(self):
        """Remove entries older than the monitored duration"""
        # while first element (assuming it's the oldest) of log is too old,
        # remove it
        duration = timedelta(seconds=self.monitorDuration)
        limitTime = (self.lastReadTime - duration)
        while len(self.log) != 0 and self.log[0].time < limitTime:
            self.delete_entry()

    def alert(self):
        """Triggers an alert when hits are too high"""
        alert = ("[%s] HIGH TRAFFIC generated an alert - hits/min = %d\n"
                 % (datetime.now().strftime("%d/%b/%Y:%H:%M:%S"), self.hits/self.monitorDuration*60))
        # Add the alert message before all the other messages
        self.alerts = alert + self.alerts
        # Store this alert in a file to keep history
        try:
            with open("alerts.log", "a") as alertLog:
                alertLog.write(alert)
        except:
            print("Cannot write alerts to alerts.log")
        self.alertStatus = True

    def end_alert(self):
        """Ends the alert when traffic recovered"""
        alert = ("[%s] Traffic slowed down, the alert has recovered\n"
                 % (datetime.now().strftime("%d/%b/%Y:%H:%M:%S")))
        self.alerts = alert + self.alerts
        with open("alerts.log", "a") as alertLog:
            alertLog.write(alert)
        self.alertStatus = False

    def stop(self):
        """Stops the monitoring loop"""
        self.running = False

    def display_message(self):
        """Creates and displays all informations in the console"""
        msg = "**************************\nWelcome to HTTP Monitor\
                          \n**************************\n\n"
        msg += "Parameters:\n"
        msg += "Alert threshold = %d hits/min   " % self.alertThreshold
        msg += "Refresh period = %ds   " % self.refreshPeriod
        msg += "Monitor duration = %ds\n\n\n" % self.monitorDuration
        msg += "Summary:\n"
        msg += "Average hits/min: %d" % (self.hits/self.monitorDuration*60)
        if self.alertStatus:
            msg += (" > %d         **********ALERT**********\n"
                    % self.alertThreshold)
        else:
            msg += "                    Everything OK\n"
        if self.hits != 0:
            avgData = self.size/1000/self.hits
        else:
            avgData = 0
        msg += "\nAverage client data: %d Kb/hit" % avgData
        msg += "\nSections     -> " + self.summary(self.sections)
        msg += "\nClients      -> " + self.summary(self.ips)
        msg += "\nStatus codes -> " + self.summary(self.codes)
        msg += "\nMethods      -> " + self.summary(self.methods)
        msg += "\n\n\n"
        msg += "Alerts (Stored in real time in alerts.log):\n"
        msg += self.alerts
        # Clear the console of the previous message
        # so that it appears to be refreshed
        if os.name == "nt":
            os.system("cls")
            print(msg)
        elif os.name == "posix":
            os.system("clear")
            print(msg)
        else:
            print("OS not supported")
            input("PRESS ENTER TO EXIT")
            self.stop()

    def summary(self, items):
        """Returns a String summary of a particular Counter object
        :param items: Counter object to be summarized"""
        summary = ""
        for item in items.most_common(3):
            summary += str(item[0])+" (%d%%)   " % (item[1]/self.hits*100)
        return summary

    def run(self):
        """Method called when thread is started, main monitoring loop"""
        # Loop stops when stop() is called
        while self.running:
            self.read()
            # If log file cannot be accessed self.running is set to false
            if self.running:
                self.drop_old_entries()
                # if threshold is exceeded
                # but the alert was not activated before, call alert()
                hitRate = self.hits/self.monitorDuration*60
                if hitRate > self.alertThreshold and not self.alertStatus:
                    self.alert()
                # else, if the alert is on but hits went below the threshold,
                # end the alert
                elif hitRate < self.alertThreshold and self.alertStatus:
                    self.end_alert()
                # Check if the console output is enabled
                if self.printStatus:
                    self.display_message()
                sleep(self.refreshPeriod)
