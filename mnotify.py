# -*- coding: utf-8 -*-
import time
import io
import threading
import json
import webbrowser

import schedule
from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageEnhance
import requests
from misskey import Misskey

INTERVAL = 60
CONFIG = '.mnotify'


class taskTray:
    def __init__(self):
        # スレッド実行モード
        self.running = False
        # 未読数
        self.unread = 0

        with open(CONFIG) as fd:
            self.config = json.load(fd)
            instance = self.config.get('misskey_instance')
            token = self.config.get('misskey_token')
            if token and instance:
                self.misskey = Misskey(
                    address=instance,
                    i=token,
                )

        # get server meta
        meta = self.misskey.meta()
        self.servername = meta.get('name')
        # get server favicon
        r = requests.get(meta.get('iconUrl'))
        self.u_icon = Image.open(io.BytesIO(r.content))
        # darkened, gray scale
        self.n_icon = ImageEnhance.Brightness(self.u_icon).enhance(0.5).convert('L')

        menu = Menu(
            MenuItem('Open', self.doOpen, default=True, visible=False),
            MenuItem('Check', self.doCheck),
            MenuItem('Exit', self.stopApp),
        )
        self.app = Icon(name='PYTHON.win32.mnotify', title=self.servername, icon=self.n_icon, menu=menu)
        self.doCheck()

    def doOpen(self):
        webbrowser.open(self.config.get('misskey_instance'))

    def doCheck(self):
        try:
            r = self.misskey.i()
            hasUnreadNotification = r.get('hasUnreadNotification')
            unreadNotificationsCount = r.get('unreadNotificationsCount')
            if hasUnreadNotification:
                self.app.title = f'{self.servername} {unreadNotificationsCount}'
                self.app.icon = self.u_icon
            else:
                self.app.title = self.servername
                self.app.icon = self.n_icon
            self.app.update_menu()
        except Exception as e:
            print(e)

    def runSchedule(self):
        schedule.every(INTERVAL).seconds.do(self.doCheck)

        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stopApp(self):
        self.running = False
        self.app.stop()

    def runApp(self):
        self.running = True

        task_thread = threading.Thread(target=self.runSchedule)
        task_thread.start()

        self.app.run()


if __name__ == '__main__':
    taskTray().runApp()
