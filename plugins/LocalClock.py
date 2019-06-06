# -*- coding: utf-8-*-

import logging
import time
import datetime
from robot.sdk.AbstractPlugin import AbstractPlugin

logger = logging.getLogger(__name__)

class Plugin(AbstractPlugin):

    def handle(self, text, parsed):
        now = datetime.datetime.now()
        today_date = now.strftime(u"%Y年%m月%d日")
        today_time = now.strftime(u"%H点%M分")
        text = '%s%s'%(today_date,today_time)
        self.say(text, cache=False)

    def isValid(self, text, parsed):
        return any(word in text.lower() for word in [u"几点了", u"现在时间"])
        
        
