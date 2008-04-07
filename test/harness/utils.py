"""Utilities that can be imported by tests.  You need to make
sure your PYTHONPATH includes the directory containing this
file in order for the tests that use it to work.  The test
harness does that automatically for you."""

import dbus
bus = dbus.SessionBus()
dbusOrca = bus.get_object('org.gnome.Orca', '/')
dbusOrcaLogging = dbus.Interface(dbusOrca, 'org.gnome.Orca.Logging')

# Where to find Dojo tests.
#
#DojoURLPrefix="http://archive.dojotoolkit.org/nightly/dojotoolkit/dijit/tests/"
#DojoURLPrefix="http://localhost/apache2-default/dojo-release-1.1.0b2/dijit/tests/"
DojoURLPrefix="http://bashautomation.com/dojo-release-1.1.0b2/dijit/tests/"
# Where to find our local HTML tests.
#
import sys, os, re
wd = os.path.dirname(sys.argv[0])
fullPath = os.path.abspath(wd)
htmlDir = os.path.abspath(fullPath + "/../../html")
htmlURLPrefix = "file://" + htmlDir + "/"

createDiffs = True
try:
    # If the difflib module is not found, fall back to generating the
    # old-style EXPECTED/ACTUAL output.
    #
    import difflib
except:
    createDiffs = False

from macaroon.playback import *

enable_assert = \
    environ.get('HARNESS_ASSERT', 'yes') in ('yes', 'true', 'y', '1', 1)
errFilename = environ.get('HARNESS_ERR', None)
outFilename = environ.get('HARNESS_OUT', None)

if errFilename and len(errFilename):
    myErr = open(errFilename, 'a', 0)
else:
    myErr = sys.stderr

if outFilename and len(outFilename):
    if outFilename == errFilename:
        myOut = myErr
    else:
        myOut = open(outFilename, 'a', 0)
else:
    myOut = sys.stdout

class StartRecordingAction(AtomicAction):
    '''Tells Orca to log speech and braille output to a string which we
    can later obtain and use in an assertion (see AssertPresentationAction)'''

    def __init__(self):
        if enable_assert:
            AtomicAction.__init__(self, 1000, self._startRecording)
        else:
            AtomicAction.__init__(self, 0, lambda: None)

    def _startRecording(self):
        dbusOrcaLogging.startRecording()

    def __str__(self):
        return 'Start Recording Action'

def assertListEquality(rawOrcaResults, expectedList):
    '''Convert raw speech and braille output obtained from Orca into a
    list by splitting it at newline boundaries.  Compare it to the
    list passed in and return the actual results if they differ.
    Otherwise, return None to indicate an equality.'''

    results = rawOrcaResults.strip().split("\n")

    # Shoot for a string comparison first.
    #
    if results == expectedList:
        return None
    elif len(results) != len(expectedList):
        return results

    # If the string comparison failed, do a regex match item by item
    #
    for i in range(0, len(expectedList)):
	if results[i] == expectedList[i]:
            continue
        else:
            expectedResultRE = re.compile(expectedList[i])
            if expectedResultRE.match(results[i]):
                continue
            else:
                return results

    return None

class AssertPresentationAction(AtomicAction):
    '''Ask Orca for the speech and braille logged since the last use
    of StartRecordingAction and apply an assertion predicate.'''

    totalCount = 0
    totalSucceed = 0
    totalFail = 0
    totalExpectedToFail = 0

    def __init__(self, name, expectedResults, 
                 assertionPredicate=assertListEquality):
        '''name:               the name of the test
           expectedResults:    the results we want (typically a list of strings
                               that can be treated as regular expressions)
           assertionPredicate: method to compare actual results to expected
                               results
        '''
        # [[[WDW: the pause is to wait for Orca to process an event.
        # Probably should think of a better way to do this.]]]
        #
        if enable_assert:
            AtomicAction.__init__(self, 1000, self._stopRecording)
            self._name = sys.argv[0] + ":" + name
            self._expectedResults = expectedResults
            self._assertionPredicate = assertionPredicate
            AssertPresentationAction.totalCount += 1
            self._num = AssertPresentationAction.totalCount
        else:
            AtomicAction.__init__(self, 0, lambda: None)

    def printDiffs(self, results):
        """Compare the expected results with the actual results and print
        out a set of diffs.

        Arguments:
        - results: the actual results.

        Returns an indication of whether this test was expected to fail.
        """

        expectedToFail = False
        print >> myErr, "DIFFERENCES FOUND:"
        if isinstance(self._expectedResults, [].__class__):
            for result in self._expectedResults:
                if result.startswith("KNOWN ISSUE"):
                    expectedToFail = True
        else:
            if self._expectedResults.startswith("KNOWN ISSUE"):
                expectedToFail = True

        d = difflib.Differ()
        diffs = list(d.compare(self._expectedResults, results))
        print >> myErr, '\n'.join(list(diffs))
        return expectedToFail

    def printResults(self, results):
        """Print out the expected results and the actual results.

        Arguments:
        - results: the actual results.

        Returns an indication of whether this test was expected to fail.
        """

        expectedToFail = False
        print >> myErr, "EXPECTED:"
        if isinstance(self._expectedResults, [].__class__):
            for result in self._expectedResults:
                if result.startswith("KNOWN ISSUE"):
                    expectedToFail = True
                print >> myErr, '     "%s",' % result
        else:
            if self._expectedResults.startswith("KNOWN ISSUE"):
                expectedToFail = True
            print >> myErr, '     "%s"' % self._expectedResults
        print >> myErr, "ACTUAL:"
        if isinstance(results, [].__class__):
            for result in results:
                print >> myErr, '     "%s",' % result
        else:
            print >> myErr, '     "%s"' % results
        return expectedToFail

    def _stopRecording(self):
        result = dbusOrcaLogging.stopRecording()
        results = self._assertionPredicate(result, self._expectedResults)
        if not results:
            AssertPresentationAction.totalSucceed += 1
            print >> myOut, "Test %d of %d SUCCEEDED: %s" \
                            % (self._num, 
                               AssertPresentationAction.totalCount, 
                               self._name)
        else:
            AssertPresentationAction.totalFail += 1
            print >> myErr, "Test %d of %d FAILED: %s" \
                            % (self._num, 
                               AssertPresentationAction.totalCount, 
                               self._name)
            if createDiffs:
                expectedToFail = self.printDiffs(results)
            else:
                expectedToFail = self.printResults(results)

            if expectedToFail:
                AssertPresentationAction.totalExpectedToFail += 1
                print >> myErr, '[FAILURE WAS EXPECTED - ' \
                                'LOOK FOR KNOWN ISSUE IN EXPECTED RESULTS]'
            else:
                print >> myErr, '[FAILURE WAS UNEXPECTED]'

    def __str__(self):
        return 'Assert Presentation Action: %s' % self._name

class AssertionSummaryAction(AtomicAction):
    '''Output the summary of successes and failures of 
    AssertPresentationAction assertions.'''

    def __init__(self):
        AtomicAction.__init__(self, 0, self._printSummary)

    def _printSummary(self):
        print >> myOut, \
            "SUMMARY: %d SUCCEEDED and %d FAILED (%d UNEXPECTED) of %d for %s"\
            % (AssertPresentationAction.totalSucceed,
               AssertPresentationAction.totalFail,
               (AssertPresentationAction.totalFail \
               - AssertPresentationAction.totalExpectedToFail),
               AssertPresentationAction.totalCount,
               sys.argv[0])

    def __str__(self):
        return 'Start Recording Action'

