#
# File to load the Qt toolkit module
#   - it is possible to load qt4, qt5 or qtside with this module
#
#
# Choice method:
#
#   1.  command line flag
#       The following flags are recognided if provided in the command line 
#         --pyside
#         --pyqt4
#         --pyqt5
#   2.  QT_API environment variable
#         If no flag is provided, the module will check the QT_API
#         environment variable for one of the following values
#            'pyside', 'pyqt4', 'pyqt5'
#   3.  Try and fail
#         If no flag is provided and the QT_API environment variable is
#         not set with any of the recognized values the module with try
#         to import in order PyQt5, PySide, PyQt4 until one is found
#
import sys
import os

qt_variant = None

env_api = os.environ.get('QT_API', 'pyqt')

if '--pyside' in sys.argv:
    qt_variant = 'PySide'
elif '--pyqt4' in sys.argv:
    qt_variant = 'PyQt4'
elif '--pyqt5' in sys.argv:
    qt_variant = 'PyQt5'
elif env_api == 'pyside':
    qt_variant = 'PySide'
elif env_api == 'pyqt4':
    qt_variant = 'PyQt4'
elif env_api == 'pyqt5':
    qt_variant = 'PyQt5'

qt_imported = False

if qt_variant == "PyQt5" or (not qt_variant and not qt_imported):
    try:
        from PyQt5.QtCore import *
        from PyQt5.QtGui import *
        from PyQt5.QtWidgets import *
        print("Using QT5")
        qt_imported = True
        qt_variant = "PyQt5"
        os.environ['QT_API'] = 'pyqt5'
    except:
        pass

if qt_variant == "PySide" or (not qt_variant and not qt_imported):
    try:
        from PySide.QtCore import *
        from PySide.QtGui import *
        print("Using PySide")
        pyqtSignal = Signal
        qt_imported = True
        qt_variant = "PySide"
        os.environ['QT_API'] = 'pyside'
    except:
        pass

if qt_variant == "PyQt4" or (not qt_variant and not qt_imported):
    try:
        import sip
        api2_classes = [
            'QData', 'QDateTime', 'QString', 'QTextStream',
            'QTime', 'QUrl', 'QVariant',
        ]
        for cl in api2_classes:
            sip.setapi(cl, 2)
        from PyQt4.QtCore import *
        from PyQt4.QtGui import *

        print("Using Qt4")
        qt_imported = True
        qt_variant = "PyQt4"
        os.environ['QT_API'] = 'pyqt4'
    except:
        pass

