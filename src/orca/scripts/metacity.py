# Orca
#
# Copyright 2005-2006 Sun Microsystems Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

"""Custom script for metacity."""

__id__        = "$Id$"
__version__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2005-2006 Sun Microsystems Inc."
__license__   = "LGPL"

import orca.braille as braille
import orca.default as default
import orca.rolenames as rolenames
import orca.orca as orca
import orca.speech as speech
import orca.util as util

from orca.orca_i18n import _

########################################################################
#                                                                      #
# The Metacity script class.                                           #
#                                                                      #
########################################################################

class Script(default.Script):

    def __init__(self, app):
        """Creates a new script for the given application.

        Arguments:
        - app: the application to create a script for.
        """
        default.Script.__init__(self, app)

    def onNameChanged(self, event):
        """The status bar in metacity tells us what toplevel window will be
        activated when tab is released.  We will key off the name changed
        event to determine when to say something, as it seems to be the
        more reliable event.

        Arguments:
        - event: the name changed Event
        """

        # Do the default thing if this is not the status bar.
        #
        if event.source.role != rolenames.ROLE_STATUSBAR:
            default.Script.onNameChanged(self, event)
            return

        # Let's make sure the name really changed.  Metacity seems
        # to like to give us multiple name changed events.
        #
        if event.source.__dict__.has_key("oldName"):
            oldName = event.source.oldName
        else:
            oldName = None

        name = event.source.name
        if name == oldName:
            return
        else:
            event.source.oldName = name

        # We have to stop speech, as Metacity has a key grab and we're not
        # getting keys
        #
        speech.stop()

        # Do we know about this window?  Traverse through our list of apps
        # and go through the toplevel windows in each to see if we know
        # about this one.  If we do, it's accessible.  If we don't, it is
        # not.
        #
        found = False
        for app in util.getKnownApplications():
            i = 0
            while i < app.childCount:
                win = app.child(i)
                if win is None:
                    print "app error " + app.name
                elif win.name == name:
                    found = True
                i = i + 1

        text = name

        # Note to translators:  the "Workspace " string is the
        # prefix of what metacity shows when you press Ctrl+Alt
        # and the left or right arrow keys to switch between
        # workspaces.  The goal here is to find a match with
        # that prefix.
        #
        if (not found) and (not text.startswith(_("Workspace "))):
            text += ". " + _("inaccessible")

        braille.displayMessage(text)
        speech.speak(text)

    def onStateChanged(self, event):
        """The status bar in metacity tells us what toplevel window will be
        activated when tab is released.

        Arguments:
        - event: the object:state-changed: Event
        """

        # Ignore changes on the status bar.  We handle them in onNameChanged.
        #
        if event.source.role != rolenames.ROLE_STATUSBAR:
            default.Script.onStateChanged(self, event)

    def onTextInserted(self, event):
        """Called whenever text is inserted into an object.

        Arguments:
        - event: the Event
        """

        # Ignore changes on the status bar.  We handle them in onNameChanged.
        #
        if event.source.role != rolenames.ROLE_STATUSBAR:
            default.Script.onTextInserted(self, event)

    def onTextDeleted(self, event):
        """Called whenever text is deleted from an object.

        Arguments:
        - event: the Event
        """

        # Ignore changes on the status bar.  We handle them in onNameChanged.
        #
        if event.source.role != rolenames.ROLE_STATUSBAR:
            default.Script.onTextDeleted(self, event)

    def onCaretMoved(self, event):
        """Called whenever the caret moves.

        Arguments:
        - event: the Event
        """

        # Ignore changes on the status bar.  We handle them in onNameChanged.
        #
        if event.source.role != rolenames.ROLE_STATUSBAR:
            default.Script.onCaretMoved(self, event)
