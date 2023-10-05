#------------------------------------------------------------------------
# pmm: acommon.py
#-----------------
# Common data
#------------------------------------------------------------------------
import logging
logger = logging.getLogger(__name__)

gAnalysisStore = None
gApp = None

class AnalysisStore:
    def __init__(self):
        self.assets = {}

    def add(self, name, cls):
        if not name in self.assets.keys():
            self.assets[name] = cls
    def create(self, tname, oname='', model=None, viewModel=None):
        x = None
        viewModel = None
        if gApp:
            viewModel = gApp.viewModel
        #logger.info(f'gApp = {gApp}, tname={tname}, vmodel={viewModel}')
        if tname in self.assets.keys():
            cls = self.assets[tname]
            n2 = oname
            if n2 == '':
                n2 = tname
            x = cls(n2)
            x.setModel(model)
            x.setViewModel(viewModel)
        return x

class AppCommon:
    def __init__(self, view, model, viewModel):
        self.view = view
        self.model = model
        self.viewModel = viewModel
        #
        getAnalysisStore()
        pass

def setAppCommon(view, model, viewModel):
    global gApp
    gApp = AppCommon(view, model, viewModel)
    return gApp

def getApp():
    return gApp

def getModel():
    return gApp.model

def getController():
    return gApp.model

def getViewController():
    return gApp.viewModel

def getWindow():
    return gApp.view

def getAnalysisStore():
    global gAnalysisStore
    if gAnalysisStore == None:
        gAnalysisStore = AnalysisStore()
    return gAnalysisStore

def createAnalysis(name, model=None, viewModel=None):
    store = getAnalysisStore()
    x = store.create(name, oname='', model=model, viewModel=viewModel)
    return x

