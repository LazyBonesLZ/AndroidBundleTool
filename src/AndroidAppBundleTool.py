#! /usr/bin/env python
# -*- coding: utf-8 -*-
import sys,os
import datetime
import Queue
import logging
import signal
import time
import threading
import tkFileDialog
import subprocess
import getpass

from ConfigParser import SafeConfigParser
# if sys.version_info < (3, 0):
#     # Python 2
#     import Tkinter as tk
# else:
#     # Python 3
#     import tkinter as tk

import Tkinter as tk
import ScrolledText
import ttk

valueMap = {}
KEY_AAB = "aab_path"
KEY_JKS = "key_store_path"
KEY_STORE_PWD = "key_store_pwd"
KEY_ALIAS = "key_alias"
KEY_ALIAS_PWD = "key_alias_pwd"
KEY_EXPORT_PATH = "key_export_path"
KEY_BUNDLETOOL_PATH = "key_bundletool_path"
KEY_ADB_PATH = "key_adb_path"
bDoingJob = False
SYS_USER =  getpass.getuser()
SYS_CONFIG_PATH = "config.ini"


def getFileTypeByKey(keyName):
    if KEY_AAB == keyName:
        return "*.aab"
    if KEY_JKS == keyName:
        return "*.jks"
    if KEY_EXPORT_PATH == keyName:
        return "*.apks"
    if KEY_BUNDLETOOL_PATH == keyName:
        return "*.jar"
    return  "*.*"
def dealWithSpace(str):
    return str.replace(' ','\\ ')

def open_file(keyName,entry):
    """Open a file for editing."""
    if bDoingJob:
        return
    if not keyName:
        return

    if KEY_JKS == keyName or KEY_ADB_PATH == keyName:
        filepath = tkFileDialog.askopenfilename()
    else:
        filepath = tkFileDialog.askopenfilename(
            filetypes = [("Files",getFileTypeByKey(keyName)), ("All Files", "*.*")]
        )
   
    if not filepath:
        return 
    entry.config(state='normal')
    entry.delete(0, tk.END)
    entry.insert(0, filepath)
    entry.config(state='disabled')
    #处理字符串 不允许有空格
    valueMap[keyName] = dealWithSpace(filepath)

    if KEY_BUNDLETOOL_PATH == keyName or KEY_ADB_PATH == keyName :
        config = SafeConfigParser()
        config.read(SYS_CONFIG_PATH)
        level = logging.INFO
        logger.log(level, "SYS_CONFIG_PATH:" +SYS_CONFIG_PATH)
        print("Config:" + keyName + "=" + valueMap.get(keyName))
        config.set('main', keyName, valueMap.get(keyName))
        with open(SYS_CONFIG_PATH, 'w') as f:
             config.write(f)
             level = logging.INFO
             logger.log(level, "Config Saved:" + keyName + "=" + valueMap.get(keyName))

    print(keyName + "=" + filepath)

def open_dir(keyName,entry):
    """Open a file for editing."""
    if bDoingJob:
        return
    if not keyName:
        return

    filepath = tkFileDialog.asksaveasfilename(initialdir = "/",title = "Select file",defaultextension="apks",filetypes = (("apks files","*.apks"),("apks files","*.apks")))
    if not filepath:
        return 
    entry.config(state='normal')
    entry.delete(0, tk.END)
    entry.insert(0, filepath)
    entry.config(state='disabled')
    #处理字符串 不允许有空格
    valueMap[keyName] = dealWithSpace(filepath)
    print(keyName + "=" + filepath)

def popen_and_call(on_success,on_fail, popen_args):
    """
    Runs the given args in a subprocess.Popen, and then calls the function
    on_exit when the subprocess completes.
    on_exit is a callable object, and popen_args is a list/tuple of args that 
    would give to subprocess.Popen.
    """
    def run_in_thread(on_success, on_fail, popen_args):
        proc = subprocess.Popen(**popen_args)

        error = proc.stderr.read()
        if error != '' and not "The APKs have been extracted in the directory" in error:
            level = logging.ERROR
            logger.log(level, error)
            on_fail()
            return
        proc.wait()
        on_success()
        return
    thread = threading.Thread(target=run_in_thread, args=(on_success,on_fail, popen_args))
    thread.start()
    # returns immediately after the thread starts
    return thread


class App:

    def __init__(self, root):
        self.root = root
        
        root.title("Android App Bundle Tool")
        # root.rowconfigure(0, minsize=360, weight=1)
        # root.rowconfigure(1, minsize=200, weight=1)
        # root.columnconfigure(0, minsize=360, weight=1)
        
        # 菜单区
        fr_menus = tk.Frame(root, relief=tk.RAISED, bd=2)
        # 输出区
        fr_console = tk.Frame(root, relief=tk.RAISED, bd=1)
        self.console = ConsoleUi(fr_console)
     
 
        # 设置tab显示风格
        mygreen = "#d2ffd2"
        withte = "#ffffff"

        style = ttk.Style()
        style.theme_create( "yummy", parent="alt", settings={
            "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0] } },
            "TNotebook.Tab": {
            "configure": {"padding": [5, 1]},
            "map":       {"background": [("selected", withte)],
                          "expand": [("selected", [1, 1, 1, 0])] } } } )
        style.theme_use("yummy")

        notebook = ttk.Notebook(fr_menus)
        tab1 = tk.Frame(notebook,width=580, height=360)
        tab2 = tk.Frame(notebook,width=580, height=360)
        notebook.add(tab1, text='AAB Tool')
        notebook.add(tab2, text='Settings')
        notebook.grid(row=0, column=0,sticky="nsew")
        
        fr_menus.grid(row=0, column=0, sticky="ns" )
        fr_console.grid(row=1, column=0, sticky="nsew")
 

        # setup aab file path:
        labelAabPath = tk.Label(tab1,text="AAB File Path: ")
        labelAabPath.grid(row=0, column=0,sticky="nw",padx=5, pady=20)
        self.entryAabPath = tk.Entry(tab1,width=40,state='disabled')
        self.entryAabPath.grid(row=0, column=1,sticky="nw", padx=5, pady=20)
        btnAabPath = tk.Button(tab1,text="...",command=lambda:open_file(KEY_AAB,self.entryAabPath))
        btnAabPath.grid(row=0, column=2,sticky="nw", padx=5, pady=20)

    
        # set key store file path:
        labelKeystorePath = tk.Label(tab1,text="Key Store Path: ")
        labelKeystorePath.grid(row=1, column=0,sticky="nw",padx=5, pady=5)
        self.entryKeystorePath = tk.Entry(tab1,width=40,state='disabled')
        self.entryKeystorePath.grid(row=1, column=1,sticky="nw", padx=5, pady=5)
        btnKeystorePath = tk.Button(tab1,text="...",command=lambda:open_file(KEY_JKS,self.entryKeystorePath))
        btnKeystorePath.grid(row=1, column=2,sticky="nw", padx=5, pady=5)

        # set key store file path:
        labelKeystorePwd = tk.Label(tab1,text="Key Store Password: ")
        labelKeystorePwd.grid(row=2, column=0,sticky="nw",padx=5, pady=5)
        self.entryKeystorePwd = tk.Entry(tab1,width=40)
        self.entryKeystorePwd.grid(row=2, column=1,sticky="nw", padx=5, pady=5)

        # set key store file path:
        labelKeyAlias = tk.Label(tab1,text="Key Alias: ")
        labelKeyAlias.grid(row=3, column=0,sticky="nw",padx=5, pady=5)
        self.entryKeyAlias = tk.Entry(tab1,width=40)
        self.entryKeyAlias.grid(row=3, column=1,sticky="nw", padx=5, pady=5)
       

        # set key store file path:
        labelKeyPwd = tk.Label(tab1,text="Key Password: ")
        labelKeyPwd.grid(row=4, column=0,sticky="nw",padx=5, pady=5)
        self.entryKeyPwd = tk.Entry(tab1,width=40)
        self.entryKeyPwd.grid(row=4, column=1,sticky="nw", padx=5, pady=5)

        # set apks output path:
        labelExportPath = tk.Label(tab1,text="Export Path: ")
        labelExportPath.grid(row=5, column=0,sticky="nw",padx=5, pady=20)
        self.entryExportPath = tk.Entry(tab1,width=40)
        self.entryExportPath.grid(row=5, column=1,sticky="nw", padx=5, pady=20)
        btnExportPath = tk.Button(tab1,text="...",command=lambda:open_dir(KEY_EXPORT_PATH,self.entryExportPath))
        btnExportPath.grid(row=5, column=2,sticky="nw", padx=5, pady=20)

        # buttons container
        fr_btns = tk.Frame(tab1,width=580, height=50)
        fr_btns.grid(row=6, column=1, columnspan = 2, sticky="nw")

        btnExportApks = tk.Button(fr_btns,text="Export Apks",command=self.exportApks)
        btnExportApks.grid(row=0, column=1,sticky="nw", padx=5, pady=5)

        btnOpenInFinder = tk.Button(fr_btns,text="Open in Finder",command=self.openApksInFinder)
        btnOpenInFinder.grid(row=0, column=2,sticky="nw", padx=5, pady=5)

        btnInstallApk = tk.Button(fr_btns,text="Install Apk",command=self.installApk)
        btnInstallApk.grid(row=0, column=3,sticky="nw", padx=5, pady=5)

        btnApkSize = tk.Button(fr_btns,text="Apk Size",command=self.getApkSize)
        btnApkSize.grid(row=0, column=4,sticky="nw", padx=5, pady=5)

        #set tab2
        labelBundleToolPath = tk.Label(tab2,text="BundleTool Path: ")
        labelBundleToolPath.grid(row=0, column=0,sticky="nw",padx=5, pady=20)
        self.entryBundleToolPath = tk.Entry(tab2,width=40,state='disabled')
        self.entryBundleToolPath.grid(row=0, column=1,sticky="nw", padx=5, pady=20)
        btnBundleToolPath = tk.Button(tab2,text="...",command=lambda:open_file(KEY_BUNDLETOOL_PATH,self.entryBundleToolPath))
        btnBundleToolPath.grid(row=0, column=2,sticky="nw", padx=5, pady=20)

        labelADBPath = tk.Label(tab2,text="ADB Path: ")
        labelADBPath.grid(row=1, column=0,sticky="nw",padx=5, pady=20)
        self.entryADBPath = tk.Entry(tab2,width=40,state='disabled')
        self.entryADBPath.grid(row=1, column=1,sticky="nw", padx=5, pady=20)
        btnADBPath = tk.Button(tab2,text="...",command=lambda:open_file(KEY_ADB_PATH,self.entryADBPath))
        btnADBPath.grid(row=1, column=2,sticky="nw", padx=5, pady=20)



        # ================> copy default config file <================
        level = logging.INFO
        configPathDir = "/Users/" + SYS_USER  + "/.AndroidBundleTool"
        if not os.path.exists(configPathDir):
            os.makedirs(configPathDir)
            logger.log(level, "Create config Path:" + configPathDir)
        global SYS_CONFIG_PATH
        SYS_CONFIG_PATH = configPathDir + "/config.ini"
        if not os.path.exists(SYS_CONFIG_PATH):
            logger.log(level, "Copy default config>>>>")
            import shutil
            shutil.copy('config.ini',SYS_CONFIG_PATH)

        #read bundletool config
        config = SafeConfigParser()
        config.read(SYS_CONFIG_PATH)
        bundletoolpath = config.get('main', KEY_BUNDLETOOL_PATH)
        print('bundletoolpath:' + bundletoolpath)
        if 'NULL'!= bundletoolpath and os.path.exists(bundletoolpath):
            self.entryBundleToolPath.config(state='normal')
            self.entryBundleToolPath.delete(0, tk.END)
            self.entryBundleToolPath.insert(0, bundletoolpath)
            self.entryBundleToolPath.config(state='disabled')
            valueMap[KEY_BUNDLETOOL_PATH] = dealWithSpace(bundletoolpath)

        #read adb config
        adbpath = config.get('main', KEY_ADB_PATH)
        logger.log(level, "config adbpath: " + adbpath)
        if 'NULL' == adbpath:
            # auto check wether the adb file existed in the android sdk path
            adbpath = "/Users/" + SYS_USER  + "/Library/Android/sdk/platform-tools/adb"
        
        logger.log(level, "real adbpath: " + adbpath)
        if os.path.exists(adbpath):
            logger.log(level, "adbpath checked: adb file existed!")
            self.entryADBPath.config(state='normal')
            self.entryADBPath.delete(0, tk.END)
            self.entryADBPath.insert(0, adbpath)
            self.entryADBPath.config(state='disabled')
            valueMap[KEY_ADB_PATH] = dealWithSpace(adbpath)

        self.root.protocol('WM_DELETE_WINDOW', self.quit)
        self.root.bind('<Control-q>', self.quit)
        signal.signal(signal.SIGINT, self.quit)

    def quit(self, *args):
        # self.clock.stop()
        self.root.destroy()

        
    def verifyParams(self):
        level = logging.ERROR
        tmpBundltoolPath = valueMap.get(KEY_BUNDLETOOL_PATH)
        if not tmpBundltoolPath:
            logger.log(level, "Bundl tool Path 不能为空!! 请先设置！！！")
            return False

        tmpAABPath = valueMap.get(KEY_AAB)
        if not tmpAABPath:
            logger.log(level, "AAB file path 不能为空!!")
            return False

        tmpKeyStorePath = valueMap.get(KEY_JKS)
        if not tmpKeyStorePath:
            logger.log(level, "Key store file path 不能为空!!")
            return False

        tmpKeyStorePwd = self.entryKeystorePwd.get()
        if not tmpKeyStorePwd:
            logger.log(level, "Key store Password 不能为空!!")
            return False
        valueMap[KEY_STORE_PWD] = dealWithSpace(tmpKeyStorePwd)

        tmpKeyAlias = self.entryKeyAlias.get()
        if not tmpKeyAlias:
            logger.log(level, "Key alias 不能为空!!")
            return False
        valueMap[KEY_ALIAS] = dealWithSpace(tmpKeyAlias)

        tmpKeyPwd = self.entryKeyPwd.get()
        if not tmpKeyPwd:
            logger.log(level, "Key Password 不能为空!!")
            return False
        valueMap[KEY_ALIAS_PWD] = dealWithSpace(tmpKeyPwd)

        tmpExportPath = self.entryExportPath.get()
        if not tmpExportPath:
            logger.log(level, "Apks export path 不能为空!!")
            return False
        valueMap[KEY_EXPORT_PATH] = dealWithSpace(tmpExportPath)

        level = logging.INFO
        return True

    def exportApks(self):
        global bDoingJob
        if bDoingJob:
            print('is doing')
            return

        if not self.verifyParams():
            return
       
        try:
            cmdExport = 'java -jar ' + valueMap.get(KEY_BUNDLETOOL_PATH) + ' build-apks --bundle=' + valueMap.get(KEY_AAB) +' --output=' + valueMap.get(KEY_EXPORT_PATH) + ' --ks='+ valueMap.get(KEY_JKS) + ' --ks-pass=pass:' + valueMap.get(KEY_STORE_PWD) + ' --ks-key-alias=' + valueMap.get(KEY_ALIAS) + ' --key-pass=pass:' + valueMap.get(KEY_ALIAS_PWD)
            print('cmdExport = ' + cmdExport)
    
            def exportSuccess():
                global bDoingJob
                level = logging.INFO
                logger.log(level, "Export apks successfully!")
                bDoingJob = False
                return
            def exportFailed():
                global bDoingJob
                level = logging.INFO
                logger.log(level, "Export apks Failed!")
                bDoingJob = False
                return
    
            bDoingJob = True
            level = logging.INFO
            logger.log(level, "Exporting...")
            popen_and_call(lambda:exportSuccess(),lambda:exportFailed(),{'args':cmdExport,'shell':True, 'stdin':subprocess.PIPE, 'stdout':subprocess.PIPE, 'stderr':subprocess.PIPE,'close_fds':True})
        except Exception as e:
            level = logging.ERROR
            logger.log(level, sys.exc_info()[0])


    def openApksInFinder(self):
        global bDoingJob
        if bDoingJob:
            print('is doing')
            return
        file = valueMap.get(KEY_EXPORT_PATH)
        if not file:
            level = logging.INFO
            logger.log(level, "Apks export path 不能为空!!")
            return

        path, file_name = os.path.split(file)
        cmd = 'open ' + path
        print(cmd)
        os.system(cmd)

    def installApk(self):
        global bDoingJob
        if bDoingJob:
            print('is doing')
            return

        adbPath = valueMap.get(KEY_ADB_PATH)
        if not adbPath:
            level = logging.ERROR
            logger.log(level, "请先设置ADB path ： Settings -> ADB Path!!")
            return
        # file = valueMap.get(KEY_EXPORT_PATH)
        filepath = tkFileDialog.askopenfilename(
            filetypes = [("Files","*.apks"), ("All Files", "*.*")]
        )
        print(filepath)
        if not filepath:
            level = logging.ERROR
            logger.log(level, "请先选择apks文件！")
            return

        try:
            cmdInstall = 'java -jar ' + valueMap.get(KEY_BUNDLETOOL_PATH) + ' install-apks --apks=' + str(filepath) + ' --adb=' + adbPath
            #获取Android版本
            adbCmd = adbPath + ' shell getprop ro.build.version.sdk'
            op = subprocess.Popen(adbCmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,close_fds=True)
        
            error = op.stderr.read()
            if error != '':
                level = logging.ERROR
                logger.log(level, error)
                return
            androidVersion = op.stdout.read()
            if androidVersion != '':
                level = logging.INFO
                logger.log(level, '当前设备：Android version = ' + androidVersion)
                if int(androidVersion) < 19:
                    cmdInstall += ' --allow-downgrade'
            print('cmdInstall = ' + cmdInstall)
            # logger.log(level, 'cmdInstall = ' + cmdInstall)

                
            def installSuccess():
                global bDoingJob
                level = logging.INFO
                logger.log(level, "Install apk successfully!")
                bDoingJob = False
                return
            def installFailed():
                global bDoingJob
                level = logging.INFO
                logger.log(level, "Install apk Failed!")
                bDoingJob = False
                return
    
            bDoingJob = True
            level = logging.INFO
            logger.log(level, "[***请注意***]如果提示安装失败，可能是因为设备上已经安装了该apk, 请先【手动卸载】！！！！")
            logger.log(level, "Apks path:" + filepath)
            logger.log(level, "Installing...")
            popen_and_call(lambda:installSuccess(),lambda:installFailed(),{'args':cmdInstall,'shell':True, 'stdin':subprocess.PIPE, 'stdout':subprocess.PIPE, 'stderr':subprocess.PIPE,'close_fds':True})

        except Exception as e:
            level = logging.ERROR
            logger.log(level, sys.exc_info()[0])
       
        # subprocess.Popen(cmd)

    def getApkSize(self):
        global bDoingJob
        if bDoingJob:
            print('is doing')
            return
        file = valueMap.get(KEY_BUNDLETOOL_PATH)
        if not file:
            level = logging.ERROR
            logger.log(level, "请先设置BundleTool path ： Settings -> BundleTool Path!!")
            return

        filepath = tkFileDialog.askopenfilename(
            filetypes = [("Files","*.apks"), ("All Files", "*.*")]
        )
        print(filepath)
        if not filepath:
            level = logging.ERROR
            logger.log(level, "请先选择apks文件！")
            return
        try:
            cmdGetSize = 'java -jar ' + valueMap.get(KEY_BUNDLETOOL_PATH) + ' get-size total --apks=' + filepath

            print('cmdGetSize = ' + cmdGetSize)
                
            def getSizeFinished():
                global bDoingJob
                bDoingJob = False
                return
            def calculate(on_exit, popen_args):
                """
                Runs the given args in a subprocess.Popen, and then calls the function
                on_exit when the subprocess completes.
                on_exit is a callable object, and popen_args is a list/tuple of args that 
                would give to subprocess.Popen.
                """
                def run_in_thread(on_exit, popen_args):
                    proc = subprocess.Popen(**popen_args)
                    error = proc.stdout.read()
                    if error != '' :
                        import re
                    list = re.findall(r"\d+\.?\d*",error)
                    print(list)
                    if len(list) > 0:
                        minsize = list[0]
                        maxsize = list[1]
                        level = logging.INFO
                        logger.log(level, "Apks path:" + filepath)
                        info = 'Apk MinSize = '+ str(round((float(minsize) / 1024 /1024),2)) + 'M,' + ', MaxSize = '  + str(round((float(maxsize) / 1024 /1024),2)) + 'M'
                        logger.log(level, info)
                    proc.wait()
                    on_exit()
                    return
                thread = threading.Thread(target=run_in_thread, args=(on_exit, popen_args))
                thread.start()
                # returns immediately after the thread starts
                return thread

            bDoingJob = True
            level = logging.INFO
            logger.log(level, "Calculating...")
            calculate(lambda:getSizeFinished(),{'args':cmdGetSize,'shell':True, 'stdin':subprocess.PIPE, 'stdout':subprocess.PIPE, 'stderr':subprocess.PIPE,'close_fds':True})

        except Exception as e:
            level = logging.ERROR
            logger.log(level, sys.exc_info()[0])
       
        # subprocess.Popen(cmd)

        
logger = logging.getLogger(__name__)

class QueueHandler(logging.Handler):
    """Class to send logging records to a queue
    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget
    """
    # Example from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
    # (https://stackoverflow.com/questions/13318742/python-logging-to-tkinter-text-widget) is not thread safe!
    # See https://stackoverflow.com/questions/43909849/tkinter-python-crashes-on-new-thread-trying-to-log-on-main-thread

    def __init__(self, log_queue):
        logging.Handler.__init__(self)
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)

class ConsoleUi:
    """Poll messages from a logging queue and display them in a scrolled text widget"""

    def __init__(self, frame):
        self.frame = frame
        # Create a ScrolledText wdiget
        self.scrolled_text = ScrolledText.ScrolledText(frame, state='disabled', height=12)
        self.scrolled_text.grid(row=0, column=0, sticky="nsew")
        self.scrolled_text.configure(font='TkFixedFont')
        self.scrolled_text.tag_config('INFO', foreground='black')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config('CRITICAL', foreground='red', underline=1)
        # Create a logging handler using a queue
        self.log_queue = Queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        self.queue_handler.setFormatter(formatter)
        logger.addHandler(self.queue_handler)
        # Start polling messages from the queue
        self.frame.after(100, self.poll_log_queue)

    def display(self, record):
        msg = self.queue_handler.format(record)
        self.scrolled_text.configure(state='normal')
        self.scrolled_text.insert(tk.END, msg + '\n', record.levelname)
        self.scrolled_text.configure(state='disabled')
        # Autoscroll to the bottom
        self.scrolled_text.yview(tk.END)

    def poll_log_queue(self):
        # Check every 100ms if there is a new message in the queue to display
        while True:
            try:
                record = self.log_queue.get(block=False)
            except Queue.Empty:
                break
            else:
                self.display(record)
        self.frame.after(100, self.poll_log_queue)

def main():   
    logging.basicConfig(level=logging.DEBUG)
    
    root = tk.Tk()
    app = App(root)
    app.root.mainloop()


if __name__ == '__main__':
    main()

