# The LogEntry object represents an entry in the log

from datetime import datetime


class LogEntry:
    """Represents an entry in the log"""

    def __init__(self, entryLine):
        """Constructor
        Parses string assuming it is a line of a w3c-formatted log
        http://httpd.apache.org/docs/2.2/logs.html#accesslog
        example: 127.0.0.1 - - [30/May/2015:14:13:09 +1000]
        "GET /icons/blank.gif HTTP/1.1" 403 301"
        :param entryLine: String representing a log entry to be parsed
        """

        # If string is not well formatted, errors occur
        try:
            entryValues = entryLine.split(' ')
            self.ip = entryValues[0]

            # 3rd item is the time,
            # we don't take the zone into account though (4th item)
            timeString = entryValues[3].strip("[]")
            self.time = datetime.strptime(timeString, "%d/%b/%Y:%H:%M:%S")

            self.method = entryValues[5].strip("\"")

            # Split path on / to get different sections:
            # "/icons/blank.gif" will yield ['', 'icons', 'blank.gif']
            sections = entryValues[6].split('/')
            # If 3 items or more (2 slashes or more), take the second item
            if len(sections) > 2:
                self.section = sections[1]
            else:    # else the path was root of the website (only one /)
                self.section = "root"

            self.code = entryValues[8]

            sizeString = entryValues[9].strip("\n")
            # if size is not provided, there is a dash instead
            if sizeString == "-":
                self.size = 0
            else:
                self.size = int(sizeString)
            # no errors -> string was parsed correctly
            self.parsed = True
        except:
            # errors -> string was not parsed
            self.parsed = False
            # Set the time to now so that it does not stop
            # the LogHandlerreading process
            self.time = datetime.now()

    def __str__(self):
        """toString method, provides a readable String representation
        of the attributes of the object"""
        return self.ip + " " + str(self.time) + " " + self.method + " " + \
            self.section+" "+str(self.size)

    def __eq__(self, other):
        """Method to compare two LogEntry objects
        They are equal if all their attributes are the equal"""
        return self.__dict__ == other.__dict__
