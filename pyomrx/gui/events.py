import wx

EVT_DATA_EXT_START_ID = wx.NewId()
EVT_DATA_EXT_SUCCESS_ID = wx.NewId()
EVT_DATA_EXT_NONFATAL_ID = wx.NewId()

EVT_FORM_GEN_START_ID = wx.NewId()
EVT_FORM_GEN_SUCCESS_ID = wx.NewId()
EVT_FORM_GEN_NONFATAL_ID = wx.NewId()


class DataExtractionStartEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_DATA_EXT_START_ID)


class DataExtractionSuccessEvent(wx.PyEvent):
    def __init__(self, data, input_path, output_path, worker_id):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_DATA_EXT_SUCCESS_ID)
        self.data = data
        self.input_path = input_path
        self.output_path = output_path
        self.worker_id = worker_id


class DataExtractionNonFatalEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_DATA_EXT_NONFATAL_ID)


class FormGenerationStartEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_FORM_GEN_START_ID)


class FormGenerationSuccessEvent(wx.PyEvent):
    def __init__(self, input_path, output_path, worker_id):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_FORM_GEN_SUCCESS_ID)
        self.input_path = input_path
        self.output_path = output_path
        self.worker_id = worker_id


class FormGenerationNonFatalEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_FORM_GEN_NONFATAL_ID)
