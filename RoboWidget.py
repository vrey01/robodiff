
from QVariant import *
from RoboDiff import RoboDiff

ROBOT_UPDATE = 50  # Update time from robot device in millisec

class RoboWidget(QWidget):

    def __init__(self, *args):
        super(QWidget,self).__init__(*args)

	self.robot = None
        self.initWidget()

	self.timer = QTimer()
        self.timer.timeout.connect(self._update)

    def initWidget(self):
        self.mainLayout = QGridLayout() 

	self.stateLabel = QLabel("State:") 
	self.stateValue = QLabel() 

	self.powerLabel = QLabel("Power:") 
	self.powerValue = QLabel() 

	self.powerButton = QPushButton("Enable")
	self.powerButton.clicked.connect(self.switchPower)

	self.mainLayout.addWidget(self.stateLabel, 0, 0)
	self.mainLayout.addWidget(self.stateValue, 0, 1)
	self.mainLayout.addWidget(self.powerLabel, 1, 0)
	self.mainLayout.addWidget(self.powerValue, 1, 1)
	self.mainLayout.addWidget(self.powerButton, 2, 1)

        self.setLayout(self.mainLayout)

    def setRobot(self,device):
        self.robot = device
	self.startRobot()

    def startRobot(self):
        if self.robot:
	    self.robot.run()
	    self.timer.start(ROBOT_UPDATE)

    def _update(self):
        if self.robot:
	    self.robot.sync()
	    self.stateValue.setText( str(self.robot.get_state()) )
	    self.powerValue.setText( str(self.robot.get_power()) )

    def switchPower(self):
        self.robot.switchPower()

def test():
    import signal
    def sig_handler(*args):
        print("Stopping robot.")
        robot.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)


    app = QApplication([])
    win = QMainWindow()
    wid = RoboWidget()

    #robot = RoboDiff(("160.103.50.80",9020,9100))
    robot = RoboDiff()
    wid.setRobot(robot)
    win.setCentralWidget(wid)
    win.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
   test()
