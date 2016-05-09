#微趋势爬虫#
>使用说明   7/13/2015 4:56:01 PM 
##1、如何调用爬虫？
>爬虫以配置驱动运行。因此在调用前需要在微趋势Mongodb数据库中设置好相关配置。
###MongoDB微趋势爬虫设置
- 数据库结构
####  ![数据库结构](./Readme/1.png)
- 文档结构：
>  ![文档结构](./Readme/2.png)
>  
    productName-产品名称
    channel--渠道名称
    spyder--调用的爬虫类名。**注意：必须与对应的爬虫类名一致**
    key--产品关键字。**注意：key为嵌入url关键字**
    beginTime--爬取开始时间，结构为文本‘20150704’
    endTime--爬取结束时间，结构为文本‘20150701’
    **注意：结束时间要小于开始时间。若结束时间与开始时间同设为0，则爬取从当前开始前两天的评论。
###微趋势爬虫调用方法
- 运行 `crawler.py`
- 运行逻辑： `crawler.py`首先搜索mongo数据库中爬虫配置项，对open为1的爬虫配置根据项spyder实例化爬虫，并根据key，开始时间和结束时间爬取用户评论，对获取的数据保持在mongodb中。


##2、爬虫获取的数据在哪里？
爬虫获取的数据存在MongoDB数据库的SpyderData集合中，库结构如下
#### ![Alt text](./Readme/3.png)
不同渠道获得的数据结构会有所不同。列举如下：
>**360助手**
> ![360助手](./Readme/4.png)
>  
    userName-用户名
    insertTime--数据入库时间
    productName--产品名称
    content--评论内容
    create_time--评论产生时间
    key--同爬虫配置的key
    channel--渠道
    type--好评/差评

-
##3、爬虫的设置
见settings.py
>
    logOpen = True
    logPrint = True
    proxyList = ['http://proxy.tencent.com:8080']
    threadlen = 10
    logFile = algorithmDir+'//log//logMessage.log'
    #mongoConfig
    mghost ='localhost'
    mguser = ''
    mgpass = ''
    mgport = 18894
    mglinkConfig = ''
    if mguser == '':
    mglinkConfig = 'mongodb://%s:%d/' % (mghost,mgport)
    else:
    mglinkConfig = 'mongodb://%s:%s@%s:%d/' % (mguser,str(mgpass),mghost,mgport)



- logOpen：True打开日志记录，False关闭日志记录
- logPrint：日志向控制台输出
- proxyList：代理列表，若无代理，则设为空列表[]
- threadlen：每个渠道爬虫的多线程数量。
- logFile：日志位置，默认为 ./log/logMessage.log
##4、爬虫模块
#### ![Alt text](./Readme/5.png)
##5、如何添加新渠道爬虫？
>添加新渠道爬虫需遵守以下规范

- 爬虫类只能有一个调用接口crawler，`def crawler(self,productName, startTime , endTime , config)`
- 结束时间要小于开始时间。若结束时间与开始时间同设为0，则爬取从当前开始前两天的评论。
- config结构与爬虫配置结构保持一致
- 接口crawler调用 `OperateData().saveResultsToDB(title, resultsData, config)`保存数据。title为爬取数据的表头，resultsData为两层嵌套列表，其中内层列表的顺序要同title的顺序相同，config同借口参数config。
- 新增渠道爬虫需在 `crawler.py`增加导入项，参考：`from spyder.spyder_zhushou360 import SpyderZhushou360`
- 新增渠道爬虫文件放入 ./spyder文件夹中

