地理编码数据爬取
========================

.. contents::

爬取进度
------------

:数据条目:   666262 条
:已爬取条目: 666235 条


安装前置依赖
------------

.. code:: bash

    pip3 install -r --upgrade requirements.txt
    

如何参与爬取
--------------

1. 访问百度开放平台页面 http://lbsyun.baidu.com/
2. 选择并点击 顶栏菜单当中的 `控制台` 
3. 使用你的账号登入百度开放平台
4. 选择并点击左栏菜单 `创建应用`
5. 启用服务: 坐标转换、地理编码、地点检索、逆地理编码、普通IP定位
6. 请求校验方式 选择为 `sn校验方式`, 并把 `SK` 信息复制下来，点击提交。
7. 创建好后，在 应用列表里面应该可以看到你刚刚创建的应用，这个时候把 `AK` 信息复制下来。
8. 这个时候你有了 `SK` 和 `AK` 这两个信息。
9. 在 `geocoding.py` 文件里面 把你获得的 `SK` 和 `AK` 信息填写进去。
10. 然后 运行 `geocoding.py` 脚本就完事了。
11. 等到抓取到了将近 1万 条数据后，你的账号当天将不再被允许使用了。
12. 这个时候你可以将你爬取到的数据提交至 Github。
13. `$ git add assets/geocode`
14. `$ git commit "Update assets/geocode"`
15. `$ git push origin patch-1`
16. 提交 一个 PR。


非常感谢你的参与！


地理编码服务
--------------

百度地理编码服务(免费，但是有请求额度限制):

*   http://lbsyun.baidu.com/index.php?title=webapi/guide/webservice-geocoding
*   http://api.map.baidu.com/geocoding/v3/?address=%E5%8C%97%E4%BA%AC%E5%B8%82%E6%B5%B7%E6%B7%80%E5%8C%BA%E4%B8%8A%E5%9C%B0%E5%8D%81%E8%A1%9710%E5%8F%B7&output=json&ak=%E6%82%A8%E7%9A%84ak


高德地理编码服务:

*   https://lbs.amap.com/api/webservice/guide/api/georegeo
*   https://lbs.amap.com/api/webservice/guide/tools/flowlevel

腾讯地理编码服务:

*   https://lbs.qq.com/webservice_v1/guide-geocoder.html
*   https://lbs.qq.com/webservice_v1/guide-quota.html


中华人民共和国行政区划代码数据来源
--------------------------------

:官方数据: http://www.mca.gov.cn/article/sj/xzqh/2019/


`assets/adcode/` 目录下的数据来源于 `modood/Administrative-divisions-of-China <https://github.com/modood/Administrative-divisions-of-China>`_ 项目。


`assets/geocode/` 目录下的数据来源于 `百度地理编码` 爬虫服务查询得来。





