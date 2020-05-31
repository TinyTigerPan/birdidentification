#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2020/5/8 18:09
# @Author  : Zhouxianpan
# @FileName: select.py
# @Software: PyCharm

import re

f = open('output.txt', 'w')
for i in range(1, 1330):
    htm_f = open("b"+str(i)+".htm", "rb")
    content = htm_f.readlines()
    for j in content:
        try:
            decode_content = j.decode("GB2312")
            # print(decode_content)
            ans = re.findall(r'<p><font\ssize=(.*)><b>(.*)</b></font>\s(.*)</p>', decode_content)[0][1:]
            f.writelines(str(i) + "\t" + ans[0] + "\t" + ans[1] + "\n")
        except Exception as e:
            pass
    htm_f.close()

f.close()

