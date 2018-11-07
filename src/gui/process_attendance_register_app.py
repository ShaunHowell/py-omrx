#!/bin/python
import os

from omr.attendance_register.processing import *
from omr.core.metrics import *

import wx
import webbrowser

class AttendanceFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(AttendanceFrame, self).__init__(*args, **kw)
        self.buttons = []
        self.create_buttons()
        self.layout_UI()
        self.Centre()
        self.statusbar.SetStatusText('ready')

    def create_buttons(self):
        def create_button(button_type, label, function, with_text=True):
            button = wx.Button(self.panel, label=label)
            path_text = wx.StaticText(self.panel, label='_'*30) if with_text else None
            self.buttons.append([button_type, {'button': button, 'text': path_text}])
            button.Bind(wx.EVT_BUTTON, function)

        self.panel = wx.Panel(self)
        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(9)

        for button_type in ["images", "output"]:
            create_button(button_type,
                          "Open {} folder".format(button_type),
                          getattr(self, 'choose_{}_folder'.format(button_type)))
        create_button('process','Process images', self.process_images, with_text=False)

    def layout_UI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        for button_type, button_dict in self.buttons:
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            hbox.Add(button_dict['button'], 0, wx.ALL, 5)
            if button_dict['text']:
                hbox.Add(button_dict['text'], 0, wx.ALIGN_LEFT | wx.ALL, 5)
                vbox.Add(hbox, flag=wx.ALIGN_LEFT | wx.ALIGN_BOTTOM | wx.ALL, border=10)
            else:
                vbox.Add(hbox, flag=wx.ALIGN_CENTRE | wx.ALL, border=10)
            vbox.Add((-1, 5))

        self.panel.SetSizer(vbox)

        self.statusbar = self.CreateStatusBar(1)
        self.statusbar.SetStatusText('UI created')

    def choose_images_folder(self, event):
        dialog = wx.DirDialog(self,
                              'Choose images directory', '',
                              style=wx.DD_DEFAULT_STYLE)
        try:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            path = dialog.GetPath()
        except Exception:
            wx.LogError('Failed to open directory!')
            raise
        finally:
            dialog.Destroy()
        if len(path) > 0:
            self.input_path = Path(path)
            text_objext = next((object[1]['text'] for object in self.buttons if object[0]=='images'), None)
            text_objext.SetLabel('...{}'.format(str(path)[-30:]))

    def choose_output_folder(self, event):
        dialog = wx.DirDialog(self,
                              'Choose output directory', '',
                              style=wx.DD_DEFAULT_STYLE)
        try:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            path = dialog.GetPath()
        except Exception:
            wx.LogError('Failed to open directory!')
            raise
        finally:
            dialog.Destroy()
        if len(path) > 0:
            self.output_folder = Path(path)
            text_objext = next((object[1]['text'] for object in self.buttons if object[0]=='output'), None)
            text_objext.SetLabel('...{}'.format(str(path)[-30:]))

    def open_output_folder(self):
        webbrowser.open(str(self.output_folder))

    def process_images(self, event):
        self.statusbar.PushStatusText('processing images')
        process_attendance_sheet_folder(input_folder=str(self.input_path),
                                        form_design_path=None,
                                        output_folder=str(self.output_folder))
        success_dialog = wx.MessageDialog(self.panel,
                         message='Processing finished: open output folder?',
                         style=wx.ICON_INFORMATION | wx.YES_NO | wx.NO_DEFAULT | wx.CENTRE,
                         caption='Attendance register processing done'
                         ).ShowModal()
        if success_dialog == 5103:
            self.open_output_folder()
        self.statusbar.PushStatusText('ready')


if __name__ == '__main__':
    app = wx.App()
    frm = AttendanceFrame(None, title='Attendance Register OMR Tool')
    frm.Show()
    app.MainLoop()
