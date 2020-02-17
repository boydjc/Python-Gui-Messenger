# Filename: PythonChat

"""PythonChat is a simple messaging application built using Python and PyQt5"""

import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QWidget, QStatusBar
from PyQt5.QtWidgets import QGridLayout, QBoxLayout
from PyQt5.QtWidgets import QLineEdit, QTextEdit, QLabel
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from threading import Thread
import socket

# the client connection for incoming connections

class ClientInThread(QThread):
    
    clientName = ''

    sendMsgSig = pyqtSignal(str, str)
    
    def __init__(self, clientAddress, clientSocket):
        QThread.__init__(self)
        self.csocket = clientSocket
        
    def run(self):
        #clientMessage = ("Welcome to the server!").encode()
        #self.csocket.sendall(clientMessage)
        clientName = self.csocket.recv(2048).decode()
        serverMessage = (clientName + ' has connected')
        self.sendMsgSig.emit(serverMessage, 'left')
        while True:
            data = self.csocket.recv(2048)
            data = data.decode()
            if data == 'Close Connection':
                try:
                    serverMessage = (clientName + ' disconnected')
                    self.sendMsgSig.emit(serverMessage, 'left')
                    break
                except Exception as e:
                    print(e)
            else:
                # format incoming messages so that they are red and users messages
                # are blue

                formatedText = '<p style="color:#c70024; ">' + clientName + ": " + data + '</p>'
                self.sendMsgSig.emit(formatedText, 'left')


# Create a subclass of QMainWindow to set up the GUI
class PyChatUi(QMainWindow):
    """PyChat GUI"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PyChat')
        self.setFixedSize(750, 500)
        
        # set central widget and general layout
        # we will use a grid layout for the general layout
        self.generalLayout = QGridLayout()
        self._centralWidget = QWidget(self)
        self.setCentralWidget(self._centralWidget)
        self._centralWidget.setLayout(self.generalLayout)

        # Create the widgets inside the central widget
        self._createChatDisplay()
        self._createConnectionBoxes()
        self._createUserInputBox()
        self._createSendButton()
        self._createStatusBar()

    def _createStatusBar(self):
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
    
        

    def _createConnectionBoxes(self):
        """ Creates the boxes for making a new connection """

        self.connectionLayout = QHBoxLayout()
        self.nameLayout = QHBoxLayout()

        self.generalLayout.addLayout(self.connectionLayout, 0, 0)
        self.generalLayout.addLayout(self.nameLayout, 0, 1)

        self.ipLabel = QLabel('IP Address')
        self.ipLabel.setStyleSheet("font-size: 15px;")
        
        self.portLabel = QLabel('Port')
        self.portLabel.setStyleSheet("font-size: 15px;")
    
        self.connectionIp = QLineEdit()
        self.connectionIp.setFixedSize(100, 20)

        self.connectionPort = QLineEdit()
        self.connectionPort.setFixedSize(100, 20)

        self.connectButton = QPushButton('Connect')
        self.connectButton.setStyleSheet("font-size: 12px;")
        self.connectButton.setFixedSize(75, 30)

        self.disconnectButton = QPushButton('Disconnect')
        self.disconnectButton.setStyleSheet("font-size: 12px;")
        self.disconnectButton.setFixedSize(75, 30)

        self.nameLabel = QLabel('Display Name ')
        self.nameLabel.setStyleSheet("font-size: 15px;")
        
        self.displayName = QLineEdit()
        self.displayName.setText("NoName")
        self.displayName.setFixedSize(100, 20)

        self.connectionLayout.addWidget(self.ipLabel)
        self.connectionLayout.addWidget(self.connectionIp)
        self.connectionLayout.addWidget(self.portLabel)
        self.connectionLayout.addWidget(self.connectionPort)
        self.connectionLayout.addWidget(self.connectButton)
        self.connectionLayout.addWidget(self.disconnectButton)
        self.connectionLayout.addStretch()

        self.nameLayout.addStretch()
        self.nameLayout.addWidget(self.nameLabel)
        self.nameLayout.addWidget(self.displayName)

        
    def _createChatDisplay(self):
        """ Creates the display for the chat window"""

        self.chatDisplay = QTextEdit()

        self.chatDisplay.setStyleSheet("color: #037ffc;"
                                       "font-size: 20px;"
                                       "font-weight: bold;")

        self.chatDisplay.setFixedSize(730, 320)
        self.chatDisplay.setReadOnly(True)
        
        self.generalLayout.addWidget(self.chatDisplay, 1, 0)

    def _createUserInputBox(self):
        """ Creates the box that the user will type into """

        self.userInputBox = QTextEdit()

        self.userInputBox.setStyleSheet("font-size: 15px;")
        
        self.userInputBox.setFixedSize(545, 80)
        self.userInputBox.setAlignment(Qt.AlignTop)
        
        self.generalLayout.addWidget(self.userInputBox, 2, 0)
        
    def _createSendButton(self):

        self.buttonLayout = QHBoxLayout()
        
        self.sendButton = QPushButton('Send')
        self.sendButton.setStyleSheet("font-size: 15px;")
        
        self.sendButton.setFixedSize(180, 80)

        self.buttonLayout.addStretch()
        self.buttonLayout.addWidget(self.sendButton)
        
        self.generalLayout.addLayout(self.buttonLayout, 2, 1)

        
        
class ServerThread(QThread):

    sendMsgSig = pyqtSignal(str, str)
    sendIpSig = pyqtSignal(str, str)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)
        self.serverHostName = socket.gethostname()
        self.serverHostIP = "0.0.0.0"
        self.serverHostRealIp = socket.gethostbyname(self.serverHostName)
        self.serverPort = 7341

    def establishSocket(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((self.serverHostIP, self.serverPort))
        self._listenForConn()

    def broadcastServerMsg(self, serverMessage, align):
        self.sendMsgSig.emit(serverMessage, align)

    def _listenForConn(self):
        while True:
            self.s.listen()
            socketConnection, clientAddress = self.s.accept()

            clientInThread = ClientInThread(clientAddress, socketConnection)
            clientInThread.sendMsgSig.connect(self.broadcastServerMsg)
            clientInThread.start()

    def run(self):
        self.sendIpSig.emit(self.serverHostRealIp, str(self.serverPort))
        self.establishSocket()
        
# client connection for connecting to others and sending outgoing messages

class ClientOutThread(QThread):

    sendMsgSig = pyqtSignal(str, str)
    quitClientThreadSig = pyqtSignal()
    clearUserInputSig = pyqtSignal()

    def __init__(self, ipIn, portIn, view, name, parent=None):
        QThread.__init__(self, parent)
        self.clientHostName = socket.gethostname()
        self.clientHostIP = socket.gethostbyname(self.clientHostName)
        self.ipToConnect = ipIn
        self.portToConnect = portIn
        self.guiView = view
        self.clientName = name

        # set the keyPressEvent for the userInputBox so we can press enter to send messages
        self.guiView.userInputBox.keyPressEvent = self.keyPressEventHandler

        # upon connection, disable the connect button so that the user cant click it again and mess things up
        # enable the disconnect button so the user can disconnect
        
        self.guiView.connectButton.setEnabled(False)
        self.guiView.disconnectButton.setEnabled(True)

        self.guiView.sendButton.setEnabled(True)
        
        self.guiView.disconnectButton.clicked.connect(self.closeServerConnection)
        self.guiView.sendButton.clicked.connect(self._sendMessage)

    def establishServerConnection(self):
        
        self.serverConnSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverConnSocket.settimeout(200)
        self.serverConnSocket.connect((self.ipToConnect, self.portToConnect))
        self._receiveServerMessage()

    def closeServerConnection(self):

        # enable the connect button again so that we can make a new connection
        # but disable the disconnect button
        self.guiView.connectButton.setEnabled(True)
        self.guiView.disconnectButton.setEnabled(False)

        self.guiView.sendButton.setEnabled(False)
        
        self.closeMessage = ('Close Connection')
        self.closeMessage = self.closeMessage.encode()
        self.serverConnSocket.sendall(self.closeMessage)
        self.serverConnSocket.close()
        self.quitClientThreadSig.emit()
    
    def _receiveServerMessage(self):
        #serverInput = self.serverConnSocket.recv(1048)
        #serverInput = serverInput.decode()
        #self.sendMsgSig.emit(serverInput, 'left')

        # send the users display  name to the server
        self.userNameMessage = self.guiView.displayName.text()
        self.userNameMessage = self.userNameMessage.encode()
        self.serverConnSocket.sendall(self.userNameMessage)

    def _sendMessage(self):
        # first get what is in the text box that the client typed in
        self.userInput = self.guiView.userInputBox.toPlainText()
        
        # will emit and print to the screen and clear the user input box

        self.sendMsgSig.emit(self.clientName + ": " + self.userInput, 'right')
        self.clearUserInputSig.emit()

        # this will send the code to the actual persons server
        self.message = self.userInput.encode()
        self.serverConnSocket.sendall(self.message)

        self.guiView.userInputBox.setFocus()

    def keyPressEventHandler(self, e):

        # get the cursor 
        cursor = self.guiView.userInputBox.textCursor()
        #cursorPosition = cursor.position()
        
        if e.key() == Qt.Key_Return:
            self._sendMessage()
        elif e.key() == Qt.Key_Backspace or e.key() == Qt.Key_Delete:
            cursor.deletePreviousChar()
        elif e.key() == Qt.Key_Left:
            cursor.movePosition(cursor.Left)
            self.guiView.userInputBox.setTextCursor(cursor)
        elif e.key() == Qt.Key_Right:
            cursor.movePosition(cursor.Right)
            self.guiView.userInputBox.setTextCursor(cursor)
        elif e.key() == Qt.Key_Up:
            cursor.movePosition(cursor.Up)
            self.guiView.userInputBox.setTextCursor(cursor)
        elif e.key() == Qt.Key_Down:
            cursor.movePosition(cursor.Down)
            self.guiView.userInputBox.setTextCursor(cursor)
        else:
            self.guiView.userInputBox.insertPlainText(str(e.text()))


    def run(self):
        self.establishServerConnection()



        
        

class PyChatCtrl():
    
    def __init__(self, view):
        # give the class an instance of the view so that we can update things
        # on the GUI
        self.guiView = view
        self.guiView.show()

        # when we first start, have the disconnect button disabled so the user cant get into trouble
        self.guiView.disconnectButton.setEnabled(False)
        # and the send button
        self.guiView.sendButton.setEnabled(False)
        self._connectButtonSignalConnector()
        self._startServerThread()
    

    def _startClientOutThread(self):
        # get the current display name that the client wants

        self.clientDisplayName = self.guiView.displayName.text()

        if self.clientDisplayName != '':
            
            try:
                self.client = ClientOutThread(self.guiView.connectionIp.text(), int(self.guiView.connectionPort.text()), self.guiView, self.clientDisplayName)
                self.client.sendMsgSig.connect(self.updateMsgBox)
                self.client.quitClientThreadSig.connect(self._quitClientOutThread)
                self.client.clearUserInputSig.connect(self.clearClientInputBox)
                self.client.start()
            except Exception as e:
                print(e)

        self.guiView.userInputBox.setFocus()

    def _quitClientOutThread(self):
        try:
            self.client.quit()
        except Exception as e:
            print(e)

    def updateMsgBox(self, textToUpdate, alignment):
        
        self.guiView.chatDisplay.append(textToUpdate)
        
        if alignment == 'left':
            self.guiView.chatDisplay.setAlignment(Qt.AlignLeft)
        elif alignment == 'right':
            self.guiView.chatDisplay.setAlignment(Qt.AlignRight)

    def updateStatusBar(self, ipText, portText):
        self.guiView.statusBar.showMessage("Your Ip: " + ipText + "        Your Port: " + portText)

    def clearClientInputBox(self):
        self.guiView.userInputBox.setText("")


    def _startServerThread(self):
        self.server = ServerThread()
        self.server.sendMsgSig.connect(self.updateMsgBox)
        self.server.sendIpSig.connect(self.updateStatusBar)
        self.server.start()

    def _connectButtonSignalConnector(self):
        self.guiView.connectButton.clicked.connect(self._startClientOutThread)

        
        
def main():
    """Main function"""
    pyChat = QApplication([])
    chatGui = PyChatUi()
    ctrl = PyChatCtrl(chatGui)
    #Execute PyChat main loop
    sys.exit(pyChat.exec())

    

if __name__ == '__main__':
    main()
        
