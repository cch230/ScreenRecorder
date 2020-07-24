import subprocess
from tkinter import *
from tkinter import messagebox
import os
import mic_record
import ctypes
import signal

class Alert(Toplevel):
    def __init__(self, parent):
        Toplevel.__init__(self, parent)
        self.transient(parent)

        self.parent = parent

        self.result = None

        self.OK = Button(self, text="OK", width=10, command=self.ok, default=ACTIVE)
        self.OK.pack()
        self.bind("<Return>", self.test)
        self.grab_set()

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                  parent.winfo_rooty() + 50))
        self.wait_window(self)


class App:
    def __init__(self, master):
        label1 = Label(master, text="파일명:")
        label1.grid(row=0, column=0, sticky="")
        self.entry1 = Entry(master)
        self.entry1.grid(row=0, column=1)
        defaultFile = "파일명"

        try:
            os.mkdir("record_result")
        except FileExistsError:
            pass

        self.entry1.insert(END, defaultFile)
        master.title(string="Screen Recorder")
        master.resizable(width=False, height=False)

        self.what = "desktop"
        self.radio2 = Radiobutton(master, text="record the window with the title of: ", variable=self.what,
                                  value="title", command=self.enDis1)
        self.radio1 = Radiobutton(master, text="record the entire desktop", variable=self.what, value="desktop",
                                  command=self.enDis)
        self.radio1.select()
        self.radio2.deselect()
        self.radio1.grid(row=2, column=0, sticky="w")
        self.radio2.grid(row=3, column=0, sticky="w")
        self.entry2 = Entry(master, state=DISABLED)
        self.entry2.grid(row=3, column=1)

        # self.rcchecked = False
        self.check_var_mkv = IntVar()
        self.check_var_mp4 = IntVar()
        self.mkv = Checkbutton(master, text="mkv", command=self.mkv_checkboxChanged, variable=self.check_var_mkv)
        self.mkv.grid(row=1, column=0)
        self.mp4 = Checkbutton(master, text="mp4", command=self.mp4_checkboxChanged, variable=self.check_var_mp4)
        self.mp4.grid(row=1, column=1)
        self.mkv.select()

        self.startButton = Button(master, text="Start Recording", command=self.startRecord)
        self.startButton.grid(row=4, column=0, columnspan=2)

        self.recording = False
        self.proc = None
        self.recorder = mic_record.recorder()
        self.master = master
        self.mergeProcess = None
        self.available = False
        self.pollClosed()


    def pollClosed(self):
        if self.recording == True:
            if self.proc.poll() != None:
                print("Something exploded!")
                self.startRecord()
        if self.proc and self.recording == False:
            if self.proc.poll() != None:
                self.startButton.config(text="Start Recording", state=NORMAL)
                self.master.title(string="Screen Recorder")

        #
        # if self.mergeProcess and self.recording == False:
        #     if self.mergeProcess.poll() != None:
        #         self.startButton.config(text="Start Recording", state=NORMAL)
        #         self.master.title(string="Screen Recorder")
        root.after(100, self.pollClosed)


    def enDis(self):
        self.entry2.config(state=DISABLED)
        self.what = "desktop"


    def enDis1(self):
        self.entry2.config(state=NORMAL)
        self.what = "title"


    def mkv_checkboxChanged(self):
        if self.check_var_mkv.get():
            self.mp4.deselect()
        else:
            self.mp4.select()


    def mp4_checkboxChanged(self):
        if self.check_var_mp4.get():
            self.mkv.deselect()
        else:
            self.mkv.select()


    def startRecord(self):
        if self.recording == False:
            self.filename = self.entry1.get()
            print("파일명 : " + self.filename + "     -    녹화시작")
            os.chdir("record_result")
            while 1:
                matches = 0
                for item in os.listdir():
                    if item[:-4] == self.filename:
                        matches += 1
                if matches == 0:
                    self.available = True
                    break
                else:
                    messagebox.showinfo(title="중복 알림", message="중복된 파일명이 있습니다. 파일명 다시 설정해주세요.")
                    break
            os.chdir("..")

            if self.available == False:
                return

            self.startButton.config(text="Stop Recording")

            self.entry1.config(state=DISABLED)
            self.radio1.config(state=DISABLED)
            self.radio2.config(state=DISABLED)
            self.master.title(string="Screen Recorder (Recording...)")

            if self.what == "title":
                self.entry2.config(state=DISABLED)
            self.recording = True

            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            if self.what == "title":
                self.proc = subprocess.Popen(args=['ffmpeg.exe', '-f', 'gdigrab', '-i', str("title="+self.entry2.get()),
                                                   '-framerate', '30', '-y', '-c:v', 'mpeg4', '-qscale:v',
                                                   '7', 'record_result/tmp.mkv'], startupinfo=startupinfo)
            else:
                if self.check_var_mkv.get():
                    print("mkv")
                    self.proc = subprocess.Popen(args=['ffmpeg.exe', '-f', 'dshow', '-i', 'audio=virtual-audio-capturer',
                                                       '-f', 'gdigrab', '-offset_x', '0', '-offset_y', '0', '-video_size',
                                                       '1920x1080', '-itsoffset', '1', '-i', "desktop",
                                                       '-framerate', '60', '-y', '-c:v', 'mpeg4', '-qscale:v', '7',
                                                       str('record_result/' + self.filename + '.mkv'), ], startupinfo=startupinfo)

                else:
                    print("mp4")
                    self.proc = subprocess.Popen(args=['ffmpeg', '-f', 'dshow', '-i', 'audio=virtual-audio-capturer', '-y', '-rtbufsize', '100M', "-f", 'gdigrab', '-framerate', '60',
                                                       '-probesize', '10M', '-draw_mouse', '1', '-offset_x', '0', '-offset_y',
                                                       '0', '-video_size', '1920x1080', '-itsoffset', '1', '-i', 'desktop',
                                                       '-c:v', 'libx264', '-r', '30', '-preset', 'ultrafast', '-tune',
                                                       'zerolatency', '-crf', '25', '-pix_fmt', 'yuv420p', str('record_result/' + self.filename + '.mp4'),
                                                        ], startupinfo=startupinfo)

            # 마이크 녹음 시작
            # self.recorder.record("record_result/" + self.filename + ".wav")
            # root.grab_set()

        elif self.recording == True:
            defaultFile = self.filename
            self.entry1.config(state=NORMAL)
            self.radio1.config(state=NORMAL)
            self.radio2.config(state=NORMAL)
            if self.what == "title":
                self.entry2.config(state=NORMAL)
            available = False
            fileNum = 0
            self.recording = False
            self.available = False

            try:
                ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, 0)
                # self.proc.send_signal(signal.CTRL_C_EVENT)
                # self.proc.terminate()
            except KeyboardInterrupt:
                print("ignoring ctrlc")

            # 녹음 종료
            # self.recorder.stop_recording()
            # if self.rcchecked:
            #     self.webcamrecorder.stopCapture()
            try:
                os.mkdir("ScreenCaptures")
            except FileExistsError:
                pass
            self.master.title(string="Screen Recorder (converting...)")
            self.startButton.config(text="converting your previous recording, please wait...", state=DISABLED)
            # startupinfo = subprocess.STARTUPINFO()
            # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            # startupinfo.wShowWindow = subprocess.SW_HIDE
            # if self.rcchecked:
            #     self.mergeProcess = subprocess.Popen(args= ["ffmpeg","-i",'tmp/tmp.mkv','-i','tmp/tmp.wav','-i','tmp/webcamtmp.mkv','-filter_complex','[2:v] scale=640:-1 [inner]; [0:0][inner] overlay=0:0 [out]',"-shortest",'-map','[out]','-y',"ScreenCaptures/"+self.filename])
            # else:
            # self.mergeProcess = subprocess.Popen(args= ["ffmpeg","-i",'tmp/First_Exam.mkv','-i','tmp/First_Exam.mp3',"-shortest",'-y',"ScreenCaptures/"+self.filename], startupinfo=startupinfo)

            os.chdir("ScreenCaptures")
            while available == False:
                matches = 0
                for item in os.listdir():
                    if item == defaultFile:
                        matches += 1
                if matches == 0:
                    available = True
                else:
                    fileNum += 1
                    file = self.filename.split(".")
                    defaultFile = file[0].rstrip("1234567890") + str(fileNum) + "." + file[1]
                self.entry1.delete(0, END)
                self.entry1.insert(END, defaultFile)
            os.chdir("../")


if __name__ == '__main__':
    root = Tk()
    app = App(root)
    root.mainloop()