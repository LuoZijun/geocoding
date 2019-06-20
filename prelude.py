#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

PY37 = sys.version_info.major == 3 and sys.version_info.minor >= 7
PY2 = sys.version_info.major == 2

if not PY37:
    if PY2:
        reload(sys)
        sys.setdefaultencoding('utf-8')
    raise Exception('请使用 Python3.7 以上的版本！')


