#爬虫使用说明

##运行环境
* Python 2.7.5
* 安装*BeautifulSoup*库，如果有easy_install，直接运行：`easy_install beautifulsoup4`
* 安装*requests*库，如果有easy_install，直接运行：`easy_install requests`

##配置文件说明
配置文件：`configs.json`，为JSON格式，其中

* `push_address`为每爬完一次后，将数据以post方式推送到的地址
* `proxies`为以网站为单位的代理服务器地址，每个网站指定一个，必须以http开头

配置文件：`page_list/{website_id}.txt`，其中*{website_id}*代表相应网站的ID。该文件每行填入一个地址或者关键字，其中

* 应用类网站每行写入一个**应用主页**地址
* 论坛类应用每行写入一个**论坛板块**的首页地址
* 微博每行写入一条**关键字**
* **如文件中有特殊注明，请根据注释的规则进行配置**

##运行参数
	./crawler.py website_id start_time end_time

* website_id：网站标识符，其中
	* 应用宝：myapp
	* 91手机助手：91
	* 安智网：anzhi
	* 豆瓣条目：douban_subject
	* Google Play：googleplay
	* 安卓网：hiapk
	* 百度贴吧吧内：tieba_forum
	* 百度贴吧搜索：tieba_search
	* 腾讯论坛：tencentbbs，其中
		* `bbs.g.qq.com`域名下的，生成的数据文件在`data/tencentbbs_bbsg`目录下
		* `gamebbs.qq.com`域名下的，生成的数据文件在`data/tencentbbs_gamebbs`目录下
	* 多玩论坛：duowan
	* 178论坛：178
* start_time：开始时间
* end_time：结束时间
	* 时间格式：`YYMMDDhhmm`，例如：2014年3月19日22:09，写作201403192209

##输出数据说明
输出数据为JSON格式，位置在data目录下，每个网站的数据在其对应的ID为名称的目录下

数据文件中，字段名称以`app_`开头的为应用市场类网站爬取的数据，`forum_`开头的为论坛类网站爬取的数据，`weibo_`开头的为微博爬取的数据，具体字段含义如下

* `app_name`：应用名称mdp
* `app_score`：应用评分
* `app_score_count_all`：应用评分总数
* `app_score_count_1`：1分的数量
* `app_score_count_2`：2分的数量
* `app_score_count_3`：3分的数量
* `app_score_count_4`：4分的数量
* `app_score_count_5`：5分的数量
* `app_downloads_count`：应用下载次数
* `app_id`：应用在该网站的ID
* `app_comments_count`：本次抓取的应用评论数量
* `app_version`：应用版本
* `app_comments_start_time`：应用评论的开始时间
* `app_comments_end_time`：应用评论的结束时间
* `app_comments`：应用评论列表，其中
	* `app_comment_user_id`：用户ID
	* `app_comment_user_name`：用户名称
	* `app_comment_user_photo`：用户头像地址
	* `app_comment_user_link`：用户主页地址
	* `app_comment_user_score`：该用户的评分
	* `app_comment_content`：评论内容
	* `app_comment_agree_count`：评论同意数
	* `app_comment_disagree_count`：评论否定数
	* `app_comment_time`：评论时间
	* `app_comment_channel`：评论发表渠道

* `forum_name`：论坛名称
* `forum_id`：论坛ID
* `forum_posts_count`：本次抓取的帖子数量
* `forum_posts_start_time`：论坛帖子的开始时间
* `forum_posts_end_time`：论坛帖子的结束时间
* `forum_posts`：论坛帖子列表，其中
	* `forum_post_id`：帖子ID
	* `forum_post_title`：帖子标题
	* `forum_post_view_count`：帖子的浏览量
	* `forum_post_reply_count`：帖子的回复数
	* `forum_post_author_content`：楼主帖子内容
	* `forum_post_author_time`：楼主帖子发表时间
	* `forum_post_author_user_name`：楼主用户名
	* `forum_post_author_user_photo`：楼主的头像地址
	* `forum_post_author_user_link`：楼主的用户主页地址
	* `forum_post_reply_content`：最新回复内容
	* `forum_post_reply_user_name`：最新回复的用户名
	* `forum_post_reply_time`：最新回复的时间
	* `forum_post_reply_user_photo`：最新回复用户的头像地址
	* `forum_post_reply_user_link`：最新回复用户的主页地址

* `weibo_posts_count`：本次抓取的微博数量
* `weibo_posts_start_time`：抓取微博的开始时间
* `weibo_posts_end_time`：抓取微博的结束时间
* `weibo_posts`：微博列表，其中
	* `weibo_post_user_name`：发表该微博的用户名
	* `weibo_post_user_link`：发表该微博的用户链接
	* `weibo_post_content`：微博内容
	* `weibo_post_forward_content`：微博转发理由
	* `weibo_post_original_user_name`：微博原作者用户名
	* `weibo_post_original_user_link`：微博原作者链接

* `search_keyword`：搜索关键字，用于新浪微博和百度贴吧搜索

##注意事项
* *Google Play*的评论时间只可以精确到天，但时间格式不变，后面的小时、分钟将被忽略
* 贴吧、豆瓣小组较老的帖子的发表时间只能精确到天，程序默认将其发表时间设置为当天的**中午12:00**
* 微博、论坛、贴吧数据更新较为频繁，抓取时请设置**较小**的时间段

##关于我
Jiaheng Zhang

熟悉*Python*、*C#*、*Java*等多种语言的开发，擅长*Windows*、*Windows Phone*、*Android*等平台和服务器程序的开发

E-mail：<mailto:jsxzjh@gmail.com>，个人主页：<http://xzjh.org>