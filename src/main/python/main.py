
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from matplotlib.pyplot import text


from ui.notifications.messageWindow import Notification
from ui.mainFrames.ICDataHandleFrame import DataHandleFrame
from ui.mainFrames.ICPlotOptionsFrame import PlotOptionFrame
from ui.mainFrames.ICSliceMarksFrame import SliceMarksFrame

from backend.utils.worker import Worker
from backend.data.data import DataCollection
from backend.data.ICGrouping import ICGrouping
from backend.filter.categoricalFilter import CategoricalFilter
from backend.utils.funcControl import funcPropControl
from backend.utils.misc import getTxtFilesFromDir
from backend.utils.stringOperations import getRandomString
from backend.utils.Logger import ICLogger
from backend.config.config import Config
from backend.saver.ICSessionHandler import ICSessionHandler

from backend.plotting.plotterCalculations import PlotterBrain

    
from ui.utils import removeFileExtension, areFilesSuitableToLoad, isWindows, standardFontSize, getHashedUrl
from ui.mainFrames.ICFigureReceiverBoxFrame import MatplotlibFigure
from ui.custom.ICWelcomeScreen import ICWelcomeScreen
from ui.custom.warnMessage import AskQuestionMessage, WarningMessage
from ui.dialogs.ICAppValidation import ICValidateEmail

import sys, os
import numpy as np
import pandas as pd
import time
from datetime import datetime
import webbrowser
import requests
import warnings
from multiprocessing import freeze_support
import base64
import json 

from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_OAEP

#ignore some warnings
warnings.filterwarnings("ignore", 'This pattern has match groups')

__VERSION__ = "0.10.10.20210316"

filePath = os.path.dirname(sys.argv[0])
exampleDir = os.path.join(filePath,"examples")
exampleFuncs = []
standardFontSize = 12 



for fileName in getTxtFilesFromDir(exampleDir):
    addExample =  {
        "subM":"Load Examples",
        "name":"name",
        "fn" : {"obj":"self","fn":"sendRequestToThread",
                "kwargs":{"funcProps":{"key":"data::addDataFrameFromTxtFile",
                          "kwargs":{"pathToFile":os.path.join(filePath,"examples","name.txt"),"fileName":"name.txt"}}}
        }}
    addExample["name"] = removeFileExtension(fileName)
    addExample["fn"]["kwargs"]["funcProps"]["kwargs"]["pathToFile"] = os.path.join(exampleDir,fileName)
    addExample["fn"]["kwargs"]["funcProps"]["kwargs"]["fileName"] = removeFileExtension(fileName)
    exampleFuncs.append(addExample)

menuBarItems = [

    {
        "subM":"Help",
        "name":"Discussions (New Features)",
        "fn": lambda : webbrowser.open("https://github.com/hnolCol/instantclue/discussions/13")
    },
    
    {
        "subM":"Help",
        "name":"YouTube Videos",
        "fn": lambda : webbrowser.open("https://www.youtube.com/channel/UCjSfodDjhCMY2bw9_i6VOXA")
    },
    {
        "subM":"Help",
        "name":"Bug Report",
        "fn": lambda : webbrowser.open("https://github.com/hnolCol/instantclue/issues")
    },
    {
        "subM":"About",
        "name":"GitHub",
        "fn": lambda : webbrowser.open("https://github.com/hnolCol/instantclue")
    },
    {
        "subM":"About",
        "name":"Cite us (orig)",
        "fn": lambda : webbrowser.open("https://www.nature.com/articles/s41598-018-31154-6/")
    },
    {
        "subM":"About",
        "name":"Cite us (extend.)",
        "fn": lambda : webbrowser.open("https://www.nature.com/articles/s41598-018-31154-6/")
    },
    {
        "subM":"About",
        "name":"v. {}".format(__VERSION__),
        "fn": lambda : pd.DataFrame([__VERSION__]).to_clipboard(index=False,header=False)
    },
    {
        "subM":"File",
        "name":"Load file(s)",
        "fn": {"obj":"self","fn":"askForFile","objName":"mainFrames","objKey":"data"}
    },
    {
        "subM":"File",
        "name":"Load session",
        "fn": {"obj":"self","fn":"loadSession","objName":"mainFrames","objKey":"data"}
    },
    {
        "subM":"File",
        "name":"Save session",
        "fn": {"obj":"self","fn":"saveSession","objName":"mainFrames","objKey":"data"}
    },
    {
        "subM":"File",
        "name":"Load Examples",
        "fn": {"obj":"self","fn":"_createSubMenu"}
    },
    {
        "subM":"Log",
        "name":"Save log",
        "fn": {"obj":"self","fn":"loadSession","objName":"mainFrames","objKey":"data"}
    },
        {
        "subM":"Share",
        "name":"Validate App",
        "fn": {"obj":"self","fn":"loadSession","objName":"mainFrames","objKey":"data"}
    },
    {
        "subM":"Share",
        "name":"Copy App ID",
        "fn": {"obj":"self","fn":"copyAppIDToClipboard"}
    }
] + exampleFuncs 


class InstantClue(QMainWindow):
    
    #define signals to clear interactive TableViews
    resetGroupColorTable = pyqtSignal()
    resetGroupSizeTable = pyqtSignal()
    resetQuickSelectTable = pyqtSignal()
    resetLabelTable = pyqtSignal()
    resetTooltipTable = pyqtSignal()
    resetStatisticTable = pyqtSignal() 
    resetMarkerTable = pyqtSignal()
    quickSelectTrigger = pyqtSignal()

    def __init__(self, parent=None):
        super(InstantClue, self).__init__(parent)

        self.mainPath = os.path.dirname(sys.argv[0])
        self.setWindowIcon(QIcon(os.path.join(self.mainPath,"icons","instantClueLogo.png")))
        
        self.config = Config(mainController = self)
        self.version = __VERSION__
        self._setupFontStyle()
        #set up data collection
        self._setupData()
        #setup filter center
        self._setupFilters()
        #setup statustuc center
        self._setupStatistics()
        #setup normalizer
        self._setupNormalizer()
        self._setupTransformer()
        #plotter brain (calculates props for plos)
        self.plotterBrain = PlotterBrain(sourceData = self.data)
        #split widget
        self.splitterWidget = MainWindowSplitter(self)
        #set up notifcation handler
        self.notification = Notification()
        #set up logger 
        self.logger = ICLogger(self.config,__VERSION__)

        _widget = QWidget()
        _layout = QVBoxLayout(_widget)
        _layout.setContentsMargins(1,3,3,3)
        _layout.addWidget(self.splitterWidget)

        self.setCentralWidget(_widget)
        self._setupStyle()

        self._getMainFrames()
        self._setPlotter()
        self._addMenu()

        self.threadpool = QThreadPool()
        
        self.mainFrames["sliceMarks"].threadWidget.setMaxThreadNumber(self.threadpool.maxThreadCount())

        self._connectSignals()
        
        self.quickSelectTrigger.connect(self.mainFrames["data"].qS.updateDataSelection)
        self.setAcceptDrops(True)
        self.acceptDrop = False
        #update parameters saved in parents (e.g data, plotter etc)
        self.config.updateAllParamsInParent()

        #self.validateApp()

    def _connectSignals(self):
        "Connects signals using the resetting of the tables defined in the sliceMarks frame."
        self.resetGroupColorTable.connect(self.mainFrames["sliceMarks"].colorTable.reset)
        self.resetGroupSizeTable.connect(self.mainFrames["sliceMarks"].sizeTable.reset)
        self.resetLabelTable.connect(self.mainFrames["sliceMarks"].labelTable.reset)
        self.resetTooltipTable.connect(self.mainFrames["sliceMarks"].tooltipTable.reset)
        self.resetStatisticTable.connect(self.mainFrames["sliceMarks"].statisticTable.reset)
        self.resetMarkerTable.connect(self.mainFrames["sliceMarks"].markerTable.reset)
        self.resetQuickSelectTable.connect(self.mainFrames["sliceMarks"].quickSelectTable.removeFromGraph)

    def _setupData(self):
        ""
        self.data = DataCollection(parent=self)
        self.grouping = ICGrouping(self.data)
        self.colorManager = self.data.colorManager
        self.sessionManager = ICSessionHandler(mainController = self)

    def _setupFontStyle(self):
        ""
        self.config.setParamRange("label.font.family",QFontDatabase().families())
        from ui import utils
        utils.standardFontSize = self.config.getParam("label.font.size")
        fontFamily = self.config.getParam("label.font.family") 
        if fontFamily in self.config.getParamRange("label.font.family"):
            utils.standardFontFamily = fontFamily
        else:
            #default to arial
            self.config.setParam("label.font.family","Arial") 
            utils.standardFontFamily = "Arial"

    def _setupFilters(self):
        ""
        if not hasattr(self,"data"):
            raise ValueError("No data object found.")

        self.categoricalFilter = self.data.categoricalFilter
        self.numericFilter = self.data.numericFilter
    
    def _setupNormalizer(self):

        self.normalizer = self.data.normalizer

    def _setupStatistics(self):

        self.statCenter = self.data.statCenter

    def _setupTransformer(self):

        self.transformer = self.data.transformer

    def _getMainFrames(self):

        self.mainFrames = self.splitterWidget.getMainFrames()
    
    def _setPlotter(self):

        self.data.setPlotter(self.mainFrames["middle"].ICPlotter)

    def _addMenu(self):
        "Main window menu."
        self.subMenus = {}
        subMenus = ["File","Log","Share","Help","About"]
        for subM in subMenus:
            self.subMenus[subM] = QMenu(subM,self)
            self.menuBar().addMenu(self.subMenus[subM])

        for menuProps in menuBarItems:
            if "fn" in menuProps and isinstance(menuProps["fn"],dict) and "fn" in menuProps["fn"] and menuProps["fn"]["fn"]== "_createSubMenu":
                self._createSubMenu(menuProps["name"],menuProps["subM"])
                
            else:
                subMenu = self.subMenus[menuProps["subM"]]
                action = subMenu.addAction(menuProps["name"])
                if "fn" in menuProps:
                    if isinstance(menuProps["fn"],dict):

                        fn = self._getObjFunc(menuProps["fn"])
                        if "kwargs" in menuProps["fn"]:
                            action.triggered.connect(lambda bool, 
                                            fn = fn, 
                                            kwargs = menuProps["fn"]["kwargs"] : fn(**kwargs))
                        else:                        
                            action.triggered.connect(fn)
                    else:
                        action.triggered.connect(menuProps["fn"])
        

    def _createSubMenu(self,subMenuName,parentMenu):
        "Add a sub menu to a parent menu."
        if parentMenu in self.subMenus:
            parentMenu = self.subMenus[parentMenu]
            self.subMenus[subMenuName] = QMenu(subMenuName,parentMenu)
            parentMenu.addMenu(self.subMenus[subMenuName])
        

    def progress_fn(self, n):
        ""
        
        
 
    def print_output(self, s):
        ""
        

    def errorInThread(self, errorType = None, v = None, e = None):
        "Error message if something went wrong in the calculation."
        self.sendMessageRequest({"title":"Error ..","message":"There was an unknwon error."})

    def _getObjFunc(self,fnProps):
        ""
        if fnProps["obj"] == "self":
            if "objKey" in fnProps and "objName" in fnProps:
                subObj = getattr(self,fnProps["objName"])[fnProps["objKey"]]
                fn = getattr(subObj,fnProps["fn"])
            elif "objName" in fnProps:
                #objKey not in fnProps
                fn = getattr(getattr(self,fnProps["objName"]),fnProps["fn"])
            else:
                fn = getattr(self,fnProps["fn"])
        else:
            classObj = getattr(self,fnProps["obj"])
            fn = getattr(classObj,fnProps["fn"])
        return fn

    def _threadComplete(self,resultDict):
        ""
        
        #check if thread returns a dict or none
        if resultDict is None:
            return
        #get function to call afer thread completed calculations
        fnsComplete = funcPropControl[resultDict["funcKey"]]["completedRequest"]
        if "data" not in resultDict:
            print("data not found in result dict")
            return
        data = resultDict["data"]
        #iteratre over functions. This is a list of dicts
        #containing function name and object name
        for fnComplete in fnsComplete:
            #get function from func dict
            fn = self._getObjFunc(fnComplete)
            #init kwargs : result dict should containg all kwargs for a function
            #careful with naming, since duplicates will be overwritten.
            if any(kw not in data for kw in fnComplete["requiredKwargs"]):
                continue
            kwargs = {}
            for kw in fnComplete["requiredKwargs"]:
                kwargs[kw] = data[kw]
            if "optionalKwargs" in fnComplete:
                for kw in fnComplete["optionalKwargs"]:
                    if kw in data:
                        kwargs[kw] = data[kw]
            try:
                #finnaly execute the function
                fn(**kwargs)
            except Exception as e:
                print("ERRRO")
                print(fn)
                print(fnComplete)
                print(e)
        
    
    def _threadFinished(self,threadID):
        "Indicate in the ui that a thread finished."
        self.mainFrames["sliceMarks"].threadWidget.threadFinished(threadID)
    
    def isPlottingThreadRunning(self):
        ""
        

    def sendRequest(self,funcProps):
        ""
        try:
            if "key" not in funcProps:
                return
            else:
                funcKey = funcProps["key"]

            if  funcKey in funcPropControl:

                fnRequest = funcPropControl[funcKey]["threadRequest"]
                fn = self._getObjFunc(fnRequest)

                if all(reqKwarg in funcProps["kwargs"] for reqKwarg in fnRequest["requiredKwargs"]):
                    data = fn(**funcProps["kwargs"])
                    if data is not None:
                        self._threadComplete({"funcKey":funcKey,"data":data })
                else:
                    print("not all kwargs found.")
                    print(fnRequest["requiredKwargs"])
                    print(funcProps["kwargs"])
        except Exception as e:
            print(e)
    

    def dragMoveEvent(self, e):
        "Ignore/acccept drag Move Event"
        if self.acceptDrop:
            e.accept()
        else:
            e.ignore()
    
    def dragEnterEvent(self,event):
        "check if drag event has urls (e.g. files)"
        #check if drop event has Urls
        if event.mimeData().hasUrls():
            event.accept()
            self.acceptDrop = True
        else:
            event.ignore()
            self.acceptDrop = False
    
    def dropEvent(self,event):
        "Allows drop of files from os"
        #find Urls of dragged objects
        droppedFiles = [url.path() for url in event.mimeData().urls() if url.isValid()]
        #check if file ends with proper fileExtension
        checkedDroppedFiles = areFilesSuitableToLoad(droppedFiles)
        if len(checkedDroppedFiles) > 0:
            event.accept()
            self.mainFrames["data"].addTxtFiles(checkedDroppedFiles)
            self.mainFrames["data"].addExcelFiles(checkedDroppedFiles)


    def sendRequestToThread(self, funcProps = None, **kwargs):
        # Pass the function to execute
        try:
            if "key" not in funcProps:
                return
            else:
                funcKey = funcProps["key"]

            if  funcKey in funcPropControl:

                fnRequest = funcPropControl[funcKey]["threadRequest"]
                fn = self._getObjFunc(fnRequest)

                #print(fnRequest["requiredKwargs"])

                if all(reqKwarg in funcProps["kwargs"] for reqKwarg in fnRequest["requiredKwargs"]):
                    # Any other kwargs are passed to the run function
                    threadID = getRandomString()

                    worker = Worker(fn = fn, funcKey = funcKey, ID = threadID,**funcProps["kwargs"]) 
                    worker.signals.result.connect(self._threadComplete)
                    worker.signals.finished.connect(self._threadFinished)
                    worker.signals.progress.connect(self.progress_fn)
                    worker.signals.error.connect(self.errorInThread)
                    self.threadpool.start(worker)
                    self.mainFrames["sliceMarks"].threadWidget.addActiveThread(threadID, funcKey)
                    #self.logger.add(funcKey,funcProps["kwargs"])
                    #Count.setText(str(self.threadpool.activeThreadCount()))
                
                else:
                    print("not all required kwargs found...")

        except Exception as e:
            print(e)


    def closeEvent(self, event = None, *args, **kwargs):
        """Overwrite close event"""
       
        msgText = "Are you sure you want to exit Instant Clue? Please confirm?"
        
        w = AskQuestionMessage(
            parent=self,
            infoText = msgText, 
            title="Question",
            iconDir = self.mainPath,
            yesCallback = lambda e = event: self.saveParameterAndClose(e))
        w.exec_()
        if w.state is None:
            event.ignore()

    def saveParameterAndClose(self, event):
        ""
        self.config.saveParameters()
        event.accept()

    def getUserLoginInfo(self):
        "Visionary ..."
        try:
            URL = "http://127.0.0.1:5000/api/v1/projects"
            r = requests.get(URL)
            return True, r.json()
        except:
            return False, []

    def sendTextEntryToWebApp(self, projectID = 1, title = "", text = "Hi", isMarkDown = True):
        "Visionary ..."
        URL = "http://127.0.0.1:5000/api/v1/projects/entries"
        jsonData = {
                "ID"            :   projectID,
                "title"         :   title,
                "text"          :   text,
                "isMarkDown"    :   isMarkDown,
                "time"          :   time.time(),
                "timeFrmt"      :   datetime.now().strftime("%d-%m-%Y :: %H:%M:%S")
                }
        id = getRandomString()
        
        r = requests.post(URL, json = jsonData)

        if r.ok:
            self.sendMessageRequest({"title":"Done","message":"Text entry transfered to WebApp. "})

    def checkAppIDForCollision(self,b64EncAppID):
        "Checks in InstantClue Webapp API if id exists alread. Since we create random strings as an id, a collision is possible and should be avoided."
        URL = "http://127.0.0.1:5000/api/v1/app/id/exists"
        
        r = requests.get(URL,params={"app-id":b64EncAppID})
        if r.status_code == 200:
            validID = json.loads(r.json())["valid"] == "True"
            return validID, False
        else:
            return False,True

    def encryptStringWithPublicKey(self, byteToEntrypt):
        ""
        publickKeyPath = os.path.join(self.mainPath,"conf","key","receiver.pem")
        if os.path.exists(publickKeyPath):
            privateKeyString = RSA.import_key(open(publickKeyPath).read())
            encryptor = PKCS1_OAEP.new(privateKeyString)
            encrypted = encryptor.encrypt(byteToEntrypt)
            b64EncStr = base64.b64encode(encrypted).decode("utf-8")
            return b64EncStr 


    def validateApp(self):
        ""
        
        
        appIDPath, validPath = self.appIDFound()
        
       
        if not validPath:
            appIDValid = False
            while not appIDValid:
                #create app ID
                appID = getRandomString(20).encode("utf-8")
                #encrypt appid for sending
                b64EncAppID = self.encryptStringWithPublicKey(appID)
                #check for collision
                appIDValid, httpRequestFailed = self.checkAppIDForCollision(b64EncAppID)
                if httpRequestFailed:
                    self.sendMessageRequest({"title":"Error..","message":"HTTP Request failed. App could not be validated."})
                    return

            self.saveAppID(appIDPath,b64EncAppID)
        #valEmailDialog = ICValidateEmail(mainController=self)
        #valEmailDialog.exec_()
            
    
            
            




           # if b64EncStr is not None:
            #    requests.put(URL,json={"app-id":b64EncStr})
           # else:
            #    self.sendMessageRequest({"title":"Error..","message":"Private key not found.."})
        
        

            #requests.post(URL,json={"app-id":b64_encStr})


    def isValidated(self):
        ""


    def appIDFound(self):
        ""
        appIDPath = self.getAppIDPath()
        return appIDPath, os.path.exists(appIDPath)

    def saveAppID(self,appIDPath, b64EncStr):
        ""
        with open(appIDPath,"w") as f:
            f.write(b64EncStr)

    def getAppIDPath(self):
        ""
        return os.path.join(self.mainPath,"conf","key","app_id")

    def getAppID(self):
        ""
        appIDPath = self.getAppIDPath()
        with open(appIDPath,"r") as f:
            b64EncStr = f.read()
            return b64EncStr

    def getDataID(self):
        ""
        return self.mainFrames["data"].getDataID()

    def copyAppIDToClipboard(self):
        ""
        appID = self.getAppID()
        if appID is not None:
            pd.DataFrame([appID]).to_clipboard(index=False,header=False, excel=False)
            self.sendMessageRequest({"title":"Copied","message":"Encrypted App ID has been copied."})

    def getGraph(self):
        "Returns the graph object from the figure mainFrame (middle)."
        graph = None
        exists = hasattr(self.mainFrames["middle"].ICPlotter,"graph")
        if exists:
            graph = self.mainFrames["middle"].ICPlotter.graph
        return exists, graph

    def getTreeView(self,dataHeader = "Numeric Floats"):
        "Returns the tree view for a specific data type"
        return self.mainFrames["data"].getTreeView(dataHeader)

    def getPlotType(self):
        "Returns the the current plot type as a string"
        return self.mainFrames["right"].getCurrentPlotType()

    def groupingActive(self):
        "Returns bools, indicating if grouping is active."
        return self.getTreeView().table.isGroupigActive()

    def isDataLoaded(self):
        "Checks if there is any data loaded."
        return len(self.mainFrames["data"].dataTreeView.dfs) > 0

    def sendMessageRequest(self,messageProps = dict()):
        "Display message on user screen in the top right corner"
        # check if all keys present
        if all(x in messageProps for x in ["title","message"]): 
            self.notification.setNotify(
                messageProps["title"],
                messageProps["message"])

    def sendToWarningDialog(self,infoText="",textIsSelectable=False,*args,**kwargs):
        ""
        w = WarningMessage(title="Warning", infoText=infoText,iconDir=self.mainPath, textIsSelectable = textIsSelectable, *args,**kwargs)
        w.exec_()

    def sendToInformationDialog(self,infoText="",textIsSelectable=False):
        ""
        w = WarningMessage(title="Information", infoText=infoText,iconDir=self.mainPath, textIsSelectable = textIsSelectable)
        w.exec_()

    def _setupStyle(self):
        "Style setup of the graphical user interface."
        
        self.setWindowTitle("Instant Clue")
        self.setStyleSheet(" QToolTip{ background-color: white ; color: black;font: 12pt;font-family: Arial;margin: 3px 3px 3px 3px;border: 0px}")
        self.setStyleSheet("""
                QScrollBar:horizontal {
                    border: none;
                    background: none;
                    height: 11px;
                    margin: 0px 11px 0 11px;
                }

                QScrollBar::handle:horizontal {
                    background: darkgrey;
                    min-width: 11px;
                   
                }
                QScrollBar::handle:horizontal:hover {
                    background: #286FA4;
                }

                QScrollBar::add-line:horizontal {
                    background: none;
                    width: 11px;
                    subcontrol-position: right;
                    subcontrol-origin: margin;
                    
                }

                QScrollBar::sub-line:horizontal {
                    background: none;
                    width: 11px;
                    subcontrol-position: top left;
                    subcontrol-origin: margin;
                    position: absolute;
                }

                QScrollBar:left-arrow:horizontal{
                    width: 11px;
                    height: 11px;
                    background: #7c7c7b;
                    
                }

                QScrollBar:right-arrow:horizontal {
                    width: 11px;
                    height: 11px;
                    background: #7c7c7b;
                    
                }
                

                QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                    background: none;
                }

                /* VERTICAL */
                QScrollBar:vertical {
                    border: none;
                    background: none;
                    width: 11px;
                    margin: 11px 0 11px 0;
                }

                QScrollBar::handle:vertical {
                    background: darkgrey;
                    min-height: 11px;
                    border-radius: 1px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #286FA4;
                }

                QScrollBar::add-line:vertical {
                    background: none;
                    height: 11px;
                    subcontrol-position: bottom;
                    subcontrol-origin: margin;
                }

                QScrollBar::sub-line:vertical {
                    background: none;
                    height: 11px;
                    subcontrol-position: top left;
                    subcontrol-origin: margin;
                    position: absolute;
                }

                QScrollBar:up-arrow:vertical {
                    width: 11px;
                    height: 11px;
                    background: #7c7c7b;
                    
                }

                QScrollBar:down-arrow:vertical {
                    width: 11px;
                    height: 11px;
                    background: #7c7c7b;
                    
                }

                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                    background: none;
                }

                """)

class MainWindowSplitter(QWidget):
    "Main Window Splitter to separate ui in different frames."
    def __init__(self, parent):
        super(MainWindowSplitter, self).__init__(parent)

        self.mC = self.parent()
        self.__controls()
        self.__layout()


    def __controls(self):
        "Creates widgets"
        
        self.ICwelcome = ICWelcomeScreen(parent=self,version=__VERSION__)
        self.mainSplitter = QSplitter(Qt.Horizontal)
        mainWindowWidth = self.parent().frameGeometry().width()
        sizeCalculation = []
        self.mainFrames = dict()
        mainFrameProps = [("data",0.25),("sliceMarks",0.1),("middle",0.55),("right",0.1)]
        for layoutId, sizeFrac in mainFrameProps:
            if layoutId == "data":
                w = DataHandleFrame(self, mainController = self.mC)
            elif layoutId == "sliceMarks":
                w = SliceMarksFrame(self, mainController = self.mC)
            elif layoutId == "middle":
                w = MatplotlibFigure(self, mainController= self.mC)
            elif layoutId == "right":
                w = PlotOptionFrame(self, mainController= self.mC)
            self.mainFrames[layoutId] = w 
            self.mainSplitter.addWidget(w)
            sizeCalculation.append(int(mainWindowWidth * sizeFrac*1000)) #hack, do not know why it is not working properly with small numbers
    
        #make splitter expand
        self.mainSplitter.setSizePolicy(QSizePolicy.Expanding,
                                        QSizePolicy.Expanding)
        self.mainSplitter.setSizes(sizeCalculation)

    def __layout(self):
        "Adds widgets to layout"
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.ICwelcome)#self.mainSplitter)
        self.setLayout(self.vbox)

    def getMainFrames(self):
        ""
        return self.mainFrames

    def showMessageForNewVersion(self,releaseURL):
        ""
        w = AskQuestionMessage(
            parent=self,
            infoText = "A new version of Instant Clue is available. Download now?", 
            title="Information",
            iconDir = self.mC.mainPath,
            yesCallback = lambda : webbrowser.open(releaseURL))
        w.show()

    def welcomeScreenDone(self):
        "Indicate layout changes once Welcome Screen finished."
        self.layout().removeWidget(self.ICwelcome)
        self.layout().addWidget(self.mainSplitter)
        self.ICwelcome.deleteLater()


def main():
    "Start the main window."
    app = QApplication(sys.argv)
    app.setStyle("Windows") # set Fusion Style
    iconPath = os.path.join("..","icons","base","32.png")
    if os.path.exists(iconPath):
        app.setWindowIcon(QIcon(iconPath))
    win = InstantClue() # Inherits QMainWindow
    screenGeom = QDesktopWidget().screenGeometry()
    win.setGeometry(50,50,screenGeom.width()-100,screenGeom.height()-120)
    win.show()    
    win.raise_()
    app.exec_()

if __name__ == '__main__':
    freeze_support()
    sys.exit(main())
