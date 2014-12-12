#!/bin/sh

date_start=20141106
date_end=20141111

date_cursor=$date_start

while [  $date_cursor -le $date_end ];
do
	/data/home/moa_crawl/env/bin/python2.7 crawler.py weibo ${date_cursor}0000 ${date_cursor}2359 
	date_cursor=`date -d "$date_cursor +1 day" +%Y%m%d`
done
