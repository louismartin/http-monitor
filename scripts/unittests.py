# Unit tests that check if the classes and methods are working as intended

import unittest
from log_entry import LogEntry
from entry_generator import EntryGenerator
from log_handler import LogHandler
from time import sleep
from datetime import datetime
from datetime import timedelta
import os


class TestLogEntry(unittest.TestCase):
    """Tests the LogEntry class"""

    def test_log_entry(self):
        """Tests creation of a LogEntry instance from one line of the log"""
        print("********************************")
        print("test_log_entry()")
        now = datetime.now()
        now = datetime(now.year,
                       now.month,
                       now.day,
                       now.hour,
                       now.minute,
                       now.second)
        # Truncate current datetime to remove microseconds
        # (for the test to succeed)
        entryLine = '127.0.0.1 - - [%s +1000] "GET /icons/blank.gif HTTP/1.1" \
403 301' % now.strftime("%d/%b/%Y:%H:%M:%S")
        logEntry = LogEntry(entryLine)
        self.assertEqual(logEntry.ip, "127.0.0.1")
        self.assertEqual(logEntry.time, now)
        self.assertEqual(logEntry.method, "GET")
        self.assertEqual(logEntry.section, "icons")
        self.assertEqual(logEntry.size, 301)

    def test_not_formatted_entry(self):
        """Checks that non formatted input are handled correctly"""
        print("********************************")
        print("test_not_formatted_entry()")
        entryLine = "This is not a log entry!"
        logEntry = LogEntry(entryLine)
        self.assertFalse(logEntry.parsed)


class TestEntryGenerator(unittest.TestCase):
    """Test the EntryGenerator class"""

    def test_entry_generator(self):
        """Check that the generation process works"""
        print("********************************")
        print("test_entry_generator()")
        logPath = "tmp.log"
        entryGenerator = EntryGenerator(logPath, rate=600)
        entryGenerator.start()
        sleep(0.5)
        entryGenerator.stop()
        entryGenerator.join()
        with open(logPath, "r") as generatedLog:
            lines = generatedLog.readlines()
        self.assertTrue(len(lines) > 0)


class TestLogHandler(unittest.TestCase):
    """Test the LogHandler class"""

    def setUp(self):
        """Initialization of the tests"""
        # Create temporary log file for testing the methods
        self.logPath = "tmp.log"
        self.generatingRate = 60
        self.entryGenerator = EntryGenerator(self.logPath, self.generatingRate)
        now = datetime.now()
        # Add a 10 hours old entry
        self.entryGenerator.write_entry(now - timedelta(hours=10))
        # Add two entries to the current time
        self.entryGenerator.write_entry(now)
        self.entryGenerator.write_entry(now)

        # Setup the LogHandler object prior testing
        self.refreshPeriod = 2
        self.alertThreshold = 20
        self.monitorDuration = 10
        self.logHandler = LogHandler(self.logPath,
                                     self.refreshPeriod,
                                     self.alertThreshold,
                                     self.monitorDuration)
        # Disable logHandler console output for the tests
        self.logHandler.printStatus = False

    def test_add_entry(self):
        """Tests adding entries to the LogHandler"""
        print("********************************")
        print("test_add_entry()")
        unparsedEntry = self.entryGenerator.generate_entry(datetime.now())
        logEntry = LogEntry(unparsedEntry)
        self.logHandler.add_entry(logEntry)
        # Check that all the attributes of the entry have been processed
        self.assertEqual(self.logHandler.log[0], logEntry)
        self.assertEqual(self.logHandler.hits, 1)
        self.assertEqual(self.logHandler.size, logEntry.size)
        self.assertEqual(self.logHandler.sections, {logEntry.section: 1})
        self.assertEqual(self.logHandler.ips, {logEntry.ip: 1})
        self.assertEqual(self.logHandler.methods, {logEntry.method: 1})
        self.assertEqual(self.logHandler.codes, {logEntry.code: 1})
        # Put an entry that is not formatted
        # to check if it's correctly dropped
        logEntry = LogEntry("This is not a formatted entry\n")
        self.logHandler.add_entry(logEntry)
        self.assertEqual(len(self.logHandler.log), 1)
        self.assertEqual(self.logHandler.hits, 1)

    def test_delete_entry(self):
        """Tests deleting entries from the LogHandler"""
        print("********************************")
        print("test_delete_entry()")
        # Add 2 entries and delete the oldest
        unparsedEntry = self.entryGenerator.generate_entry(datetime.now())
        logEntry1 = LogEntry(unparsedEntry)
        unparsedEntry = self.entryGenerator.generate_entry(datetime.now())
        logEntry2 = LogEntry(unparsedEntry)

        self.logHandler.add_entry(logEntry1)
        self.logHandler.add_entry(logEntry2)
        self.logHandler.delete_entry()  # logEntry1 should be deleted (oldest)

        # Check that only logEntry2 is left
        self.assertEqual(self.logHandler.log[0], logEntry2)
        self.assertEqual(self.logHandler.hits, 1)
        self.assertEqual(self.logHandler.size, logEntry2.size)
        self.assertEqual(self.logHandler.sections, {logEntry2.section: 1})
        self.assertEqual(self.logHandler.ips, {logEntry2.ip: 1})
        self.assertEqual(self.logHandler.methods, {logEntry2.method: 1})
        self.assertEqual(self.logHandler.codes, {logEntry2.code: 1})

    def test_read(self):
        """Test that the LogHandler correctly reads the log
        and creates a corresponding list of LogEntry objects"""
        print("********************************")
        print("test_read()")
        # Add a non formatted line to the log to check if it's dropped
        self.entryGenerator.write("this is not a formatted entry\n")
        self.logHandler.read()

        # Check that only the two most recent entries have been processed
        self.assertEqual(len(self.logHandler.log), 2)
        self.assertEqual(self.logHandler.hits, 2)
        # Check that all entries are of type LogEntry
        for entry in self.logHandler.log:
            self.assertIsInstance(entry, LogEntry)

    def test_several_reads(self):
        """Test behaviour of LogHandler when reading several times in a row"""
        print("********************************")
        print("test_several_reads()")
        self.logHandler.read()
        # Check that only the two most recententries have been processed
        self.assertEqual(len(self.logHandler.log), 2)
        # Add a new entry
        self.entryGenerator.write_entry(datetime.now())
        self.logHandler.read()
        # Check that logHandler has 3 entries in total
        self.assertEqual(len(self.logHandler.log), 3)

    def test_run(self):
        """Test the main monitoring loop of the LogHandler"""
        print("********************************")
        print("test_run()")
        # Start the thread (checks the log every refreshPeriod)
        self.logHandler.start()
        # Wait a bit so that logHandler has time to read the log once
        sleep(0.1*self.refreshPeriod)
        updateTime1 = self.logHandler.lastReadTime
        # Let's wait one and a half refreshPeriod for another read to happen
        sleep(self.refreshPeriod*1.5)
        updateTime2 = self.logHandler.lastReadTime
        # Time between the 2 reads
        delta = (updateTime2 - updateTime1).total_seconds()
        self.logHandler.stop()
        self.logHandler.join()
        # Check delta between two log reads is within a 10% error margin
        # from the specified refreshPeriod
        self.assertTrue(abs((delta-self.refreshPeriod)
                            / self.refreshPeriod) < 0.1)

    def test_drop_old_entries(self):
        """Test the removal of entries older than the monitored period"""
        print("********************************")
        print("test_drop_old_entries()")
        # Create an old entry object in the log
        oldEntryStr = self.entryGenerator.generate_entry(datetime.now()
                                                         - timedelta(hours=10))
        oldEntry = LogEntry(oldEntryStr)
        # Create a recent entry
        newEntryString = self.entryGenerator.generate_entry(datetime.now())
        newEntry = LogEntry(newEntryString)
        # Add them manually to the LogHandler
        self.logHandler.add_entry(oldEntry)
        self.logHandler.add_entry(newEntry)
        self.assertEqual(len(self.logHandler.log), 2)
        self.logHandler.drop_old_entries()
        # Only one of the entries should be left
        self.assertEqual(len(self.logHandler.log), 1)
        self.assertEqual(self.logHandler.hits, 1)

    def test_alert(self):
        """Test alert triggering"""
        print("********************************")
        print("test_alert()")
        self.logHandler.refreshPeriod = 2
        self.logHandler.start()
        self.assertEqual(self.logHandler.alertStatus, False)
        # Add twice as much entries than the threshold to trigger the alert
        now = datetime.now()
        entryCount = int(2 * self.logHandler.alertThreshold
                         * self.logHandler.monitorDuration / 60)
        for i in range(0, entryCount):
            self.entryGenerator.write_entry(now)
        # Wait for the LogHandler to read the log
        sleep(1.5*self.logHandler.refreshPeriod)
        self.logHandler.stop()
        self.logHandler.join()
        self.assertTrue(self.logHandler.alertStatus)

    def test_end_alert(self):
        """Test the alert ending went traffic went back to normal"""
        print("********************************")
        print("test_end_alert()")
        # Set time frame of monitoring to 1 second to test faster
        self.logHandler.monitorDuration = 2
        self.logHandler.refreshPeriod = 1
        self.logHandler.start()
        self.assertEqual(self.logHandler.alertStatus, False)
        # Add twice as much entries than the threshold to trigger the alert
        now = datetime.now()
        entryCount = int(2 * self.logHandler.alertThreshold
                         * self.logHandler.monitorDuration / 60)
        for i in range(0, entryCount):
            self.entryGenerator.write_entry(now)
        # Wait for the LogHandler to read the log
        sleep(self.refreshPeriod)
        self.assertTrue(self.logHandler.alertStatus)
        # Wait for the LogHandler to remove the entries
        sleep(1.5*self.logHandler.monitorDuration)
        self.logHandler.stop()
        self.logHandler.join()
        self.assertFalse(self.logHandler.alertStatus)

    def test_summary(self):
        """Test the processing of information contained in the entries"""
        print("********************************")
        print("test_summary()")
        # Write some predefined entries to the log file
        self.logHandler.monitorDuration = 2
        now = datetime.now()
        # Truncate current datetime to remove microseconds
        # (for the test to succeed)
        now = datetime(now.year,
                       now.month,
                       now.day,
                       now.hour,
                       now.minute,
                       now.second)
        # Disposition required to satisfy PEP8
        entries = ('127.0.0.1 - - [%s +1000] "GET /icons/blank.gif HTTP/1.1" \
200 100\n' % now.strftime("%d/%b/%Y:%H:%M:%S")
                   + '289.8.42.1 - - [%s +1000] "POST /index.html HTTP/1.1" \
200 1000\n' % now.strftime("%d/%b/%Y:%H:%M:%S")
                   + '127.0.0.1 - - [%s +1000] "GET /icons/blank.gif HTTP/1.1" \
200 900\n' % now.strftime("%d/%b/%Y:%H:%M:%S")
                   + '289.8.42.1 - - [%s +1000] "GET /css/display.css HTTP/1.1" \
403 4000\n' % now.strftime("%d/%b/%Y:%H:%M:%S")
                   + '127.0.0.1 - - [%s +1000] "GET /index.php HTTP/1.1" \
404 1000\n' % now.strftime("%d/%b/%Y:%H:%M:%S")
                   + '289.8.42.1 - - [%s +1000] "POST /icons/blank.gif HTTP/1.1" \
200 9000\n' % now.strftime("%d/%b/%Y:%H:%M:%S")
                   + '127.0.0.1 - - [%s +1000] "GET /icons/blank.gif HTTP/1.1" \
403 4000\n' % now.strftime("%d/%b/%Y:%H:%M:%S"))
        self.entryGenerator.clear_log()
        self.entryGenerator.write(entries)
        self.logHandler.read()
        # Check that summary information are correct
        self.assertEqual(self.logHandler.hits, 7)
        self.assertEqual(self.logHandler.size, 20000)
        self.assertEqual(self.logHandler.sections, {"icons": 4,
                                                    "root": 2,
                                                    "css": 1})
        self.assertEqual(self.logHandler.ips, {"127.0.0.1": 4,
                                               "289.8.42.1": 3})
        self.assertEqual(self.logHandler.methods, {"GET": 5,
                                                   "POST": 2})
        self.assertEqual(self.logHandler.codes, {"200": 4,
                                                 "403": 2,
                                                 "404": 1})


def tearDownModule():
    """Deletes the temporary log after all the tests"""
    logPath = "tmp.log"
    if os.path.isfile(logPath):
        os.remove(logPath)

if __name__ == '__main__':
    unittest.main()
