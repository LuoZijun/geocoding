#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import prelude

import os
import sys
import re
import json
import time
import signal
import asyncio
import logging
import hashlib
import urllib.parse
import urllib.request

import aiohttp


logger   = logging.getLogger('geocoding')


# BAIDU_AK = "ZpQwkKhbauP7yrhr6cZ939etEbt4xmPN"
# BAIDU_SK = "PMPiwdWMGr4XLw0MhshX7byVxpm8AVGK"

BAIDU_AK = "IFgNGL6NIr9uKfu5aIAr5CNLdSUwCLz2"
BAIDU_SK = "puXLmp81l4e2TvP9AK5bLmw7XRfE9Lsp"


BAIDU_URL_BASE = "http://api.map.baidu.com"

NAMES = dict()

# 配额受限
class LimitError(Exception):
    pass

# 其它错误
class OtherError(Exception):
    pass

class NameIsTooLong(Exception):
    pass


def mk_names():
    filepath = "assets/adcode/names.json"
    
    if os.path.exists(filepath):
        names = json.loads(open(filepath, "r").read())
        return names

    names = dict()
    provinces = json.loads(open("assets/adcode/provinces.json", "r").read())
    cities = json.loads(open("assets/adcode/cities.json", "r").read())
    areas = json.loads(open("assets/adcode/areas.json", "r").read())
    streets = json.loads(open("assets/adcode/streets.json", "r").read())

    for data in (provinces, cities, areas, streets):
        for item in data:
            k = item["code"]
            v = item["name"]
            assert(k not in names)
            names[k] = v

    open(filepath, "wb").write(json.dumps(names).encode("utf8"))

    return names

async def baidu_geocoding(province_name, city_name, area_name, street_name, name, code, method="whitelist"):
    """
    百度地理编码: http://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-geocoding
    SN 计算方法: http://lbsyun.baidu.com/index.php?title=lbscloud/api/appendix
    """
    for _name in (province_name, city_name, area_name, street_name, name):
        assert(type(_name) == str)

    assert(type(code) == int)
    assert(type(method) == str)
    assert(method in ("whitelist", "sk"))

    if city_name in ("市辖区", "县"):
        # 直辖市
        real_city_name = province_name
        fullname = area_name + street_name + name
    elif city_name in ("省直辖县级行政区划", "自治区直辖县级行政区划"):
        # 省级直辖县级单位（没有市级单位）
        real_city_name = None
        fullname = province_name + area_name + street_name + name
    else:
        real_city_name = city_name
        fullname = area_name + street_name + name

    if len(fullname.encode("utf8")) > 84:
        # 替换一些地区别名（比如括号括起来的 XXX开发区 ）
        fullname = re.sub(r"\（.*?\）", "", fullname)

    if len(fullname.encode("utf8")) > 84:
        fullname = area_name + street_name + name
        fullname = re.sub(r"\（.*?\）", "", fullname)

    if len(fullname.encode("utf8")) > 84:
        fullname = street_name + name
        fullname = re.sub(r"\（.*?\）", "", fullname)

    if len(fullname.encode("utf8")) > 84:
        fullname = name
        fullname = re.sub(r"\（.*?\）", "", fullname)

    if len(fullname.encode("utf8")) > 84:
        # 手动处理
        raise NameIsTooLong()

    # 检查是否已经下载过
    filepath = "assets/geocode/%d.json" % code
    need_sync = False
    if os.path.exists(filepath):
        n = time.time() - os.path.getmtime(filepath)
        if n > 7*24*60*60:
            need_sync = True
    else:
        need_sync = True

    if not need_sync:
        return None

    # 下载资料
    query = {
        "address": fullname,
        # 坐标系说明: http://lbsyun.baidu.com/index.php?title=coordinate
        # gcj02ll bd09mc
        "ret_coordtype": "gcj02ll",
        "output": "json",
        "ak": BAIDU_AK,
    }
    
    if real_city_name is not None:
        query["city"] = real_city_name

    params = urllib.parse.urlencode(query)
    urlpath = "/geocoding/v3?" + params

    if method == "sk":
        tmp = urllib.parse.quote_plus(urlpath) + BAIDU_SK
        sn = hashlib.md5(tmp.encode("utf8")).hexdigest()
        url = BAIDU_URL_BASE + urlpath + "&sn=" + sn
    elif method == "whitelist":
        url = BAIDU_URL_BASE + urlpath
    else:
        raise ValueError("oops ...")

    session = aiohttp.ClientSession()
    response = await session.get(url)
    content = await response.content.read()
    await session.close()

    body = content.decode("utf8")
    data = json.loads(body)
    """
    {
        'status': 0,
        'result': {
            'location': {
                'lng': 121.57721255218964,
                'lat': 31.281673560193113
            },
            'precise': 0,
            'confidence': 60,
            'comprehension': 100,
            'level': '地产小区'
        }
    }
    """
    assert(type(data["status"]) == int)

    if data["status"] >= 300:
        raise LimitError(data["message"])

    if data["status"] != 0:
        logger.error("%d %s %r", code, name, query)
        logger.error("查询: %s URL: %s Response: %s", fullname, url, data)
        raise OtherError(data.get("message") or data.get("msg"))

    assert(type(data["result"]["location"]["lat"]) == float)
    assert(type(data["result"]["location"]["lng"]) == float)
    assert(type(data["result"]["precise"]) == int)
    assert(type(data["result"]["confidence"]) == int)
    assert(type(data["result"]["comprehension"]) == int)
    assert(type(data["result"]["level"]) == str)

    data = data["result"]

    data["source"] = "baidu"

    data["code"] = code
    data["name"] = name
    data["fullname"] = fullname
    
    logger.debug("%d - %s - %s,%s" % (code, fullname, data["location"]["lng"], data["location"]["lat"]) )

    open(filepath, "wb").write(json.dumps(data).encode("utf8"))


async def main():
    names = mk_names()

    filepath = "assets/adcode/villages.csv"
    filesize = os.path.getsize(filepath)
    file = open(filepath, "r")
    
    # 限制并发数
    max_tasks = 80 # 百度最大限制为 160
    
    if len(sys.argv) >= 2:
        start_line = int(sys.argv[1])
    else:
        start_line = 0
    
    line_num = 0

    while 1:
        if file.tell() == filesize:
            logger.info("file.tell() == filesize")
            break

        logger.debug("Last Line: %d", line_num)

        line = file.readline().strip()
        line_num += 1

        if line_num < start_line:
            continue

        if line.startswith("code") or line == "":
            continue

        code, name, street_code, province_code, city_code, area_code = line.split(",")
        
        if area_code.endswith("\n"):
            area_code = area_code[:-1]

        name = name[1:-1]
        code = int(code)
        try:
            await baidu_geocoding(names[province_code], names[city_code], names[area_code], names[street_code], name, code)
        except NameIsTooLong:
            data = "%d %s %s %s %s %s\n" % ( code, names[province_code], names[city_code], names[area_code], names[street_code], name,)
            open("errors.log", "a").write(data)
        except OtherError:
            data = "%d %s %s %s %s %s\n" % ( code, names[province_code], names[city_code], names[area_code], names[street_code], name,)
            open("errors.log", "a").write(data)
        except Exception as e:
            raise e
        
    logger.info("DONE")

def merge():
    cities = json.loads(open("assets/adcode/cities.json", "r").read())

    filepath = "assets/adcode/villages.csv"
    filesize = os.path.getsize(filepath)
    file = open(filepath, "r")
    
    list_files = os.listdir("assets/geocode")
    for city in cities:
        city_code = city["code"]
        full_city_code = str(city_code) + "0000" + "0000"
        city_file = open("assets/%s.json" % full_city_code, "a")
        
        for fname in list_files:
            if fname.startswith(city_code) and fname.endswith(".json"):
                data = json.loads(open("assets/geocode/%s" % fname, "r").read())
                # code name lng lat precise confidence comprehension level
                code = data["code"]
                name = data["name"]
                lng = data["location"]["lng"]
                lat = data["location"]["lat"]
                precise = data["precise"]
                confidence = data["confidence"]
                comprehension = data["comprehension"]
                level = data["level"]
                line = "%s\t%s\t%f\t%f\t%d\t%d\t%d\t%s\n" % (code, name, lng, lat, precise, confidence, comprehension, level)
                city_file.write(line)


if __name__ == '__main__':
    logging.basicConfig(
        format  = '%(asctime)s %(levelname)-5s %(threadName)-10s %(name)-15s %(message)s',
        datefmt = '%Y-%m-%d %H:%M:%S',
        level   = logging.INFO
    )
    logging.getLogger("urllib").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    signal.signal(signal.SIGINT,  signal.SIG_DFL)
    signal.signal(signal.SIGSEGV, signal.SIG_DFL)
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    
    # asyncio.run(main())
    merge()
