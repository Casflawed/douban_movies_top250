import re
import requests
import csv
# import pymysql
import lxml.html
from lxml import etree
import numpy as np

ROOT_URL = "http://bcch.ahnw.cn/"
DOWNLOAD_URL = ROOT_URL + "Right.aspx"
#  连接数据库
# db = pymysql.connect(host='127.0.0.1', port=3306, user='root', passwd=PWD, db='douban',
#                      charset='utf8')
# cur = db.cursor()


def download_page(url): # 下载页面
    return requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0'
    }).text


# def execute_db(movies_info):  # 将获取的电影信息导入数据库
#     sql = "INSERT INTO test(rank, NAME, score, country, year, " \
#           "category, votes, douban_url) values(%s,%s,%s,%s,%s,%s,%s,%s)"
#     try:
#         cur.executemany(sql, movies_info)
#         db.commit()
#     except Exception as e:
#         print("Error:", e)
#         db.rollback()


def processLinksFunc(categoryId, title, libCategoryTab, html, writer, farm_techs):
    tree = lxml.html.fromstring(html)
    block_titles = tree.xpath("//div[@class='detail-block-title']")
    block_contents = tree.xpath("//div[@class='detail-content']")
    # property：简介
    intro = ""
    # property：图片库url
    libImgUrl = ""
    # property：内容（json格式）
    content = ""

    for item in block_titles:
        # 简介 or 缩图 or 详细资料
        span_detail_title = item.xpath("descendant::span[@class='detail-title']")[0]
        span_detail_title_text = span_detail_title.text.strip()

        if span_detail_title_text == "简介":
            detail_infos = block_contents[0].xpath("div[@class='detail-info']")
            for info in detail_infos:
                label = info.xpath("span[1]")[0].text
                value = info.xpath("span[2]")[0].text
                if label is not None and value is not None:
                    intro = intro + label + value + "\n"
        if span_detail_title_text == "缩图":
            links = block_contents[1].xpath("descendant::a")
            links_num = len(links)
            flag = 0
            for link in links:
                img_url = link.xpath("img/@src")[0]
                full_img_url = ROOT_URL + img_url
                if flag < links_num - 1:
                    libImgUrl = libImgUrl + full_img_url + ","
                else:
                    libImgUrl = libImgUrl + full_img_url
        if span_detail_title_text == "详细资料":
            label_items = block_contents[2].xpath("//div[@class='detail-content-title']/b")
            value_items = block_contents[2].xpath("//span[@class='detail-content-text']")

            item_num = len(label_items)
            for num in range(0, item_num):
                label = label_items[num].text
                value = value_items[num].text
                if label is not None and value is not None:
                    content = content + label + "\n" + value + "\n"
    farm_tech = (title,  intro, categoryId, content, libImgUrl, libCategoryTab)
    farm_techs.append(farm_tech)
    print(farm_tech)
    writer.writerow(farm_techs)


def getLinkListFunc(categoryId, html, writer, farm_techs):
    # 三级分类的病虫草害页面
    tree = lxml.html.fromstring(html)
    tables = tree.xpath("//div[@class='main']/table")
    # property：关联字典项lib_category_tabs
    libCategoryTab = ""
    flag = 0
    # 表1是病害，表2是虫害
    for table in tables:
        # 病害 or 虫害列表
        if flag == 0:
            libCategoryTab = "1644156913035902977"
        else:
            libCategoryTab = "1644156987115700225"
        disaster_list = table.xpath("descendant::a[@class='item-subtitle']")
        for item in disaster_list:
            # 病害 or 虫害详情链接
            disaster_full_href = ROOT_URL+ item.xpath("@href")[0]
            # 病害 or 虫害标题
            title = item.text.strip()
            processLinksFunc(categoryId, title, libCategoryTab, download_page(disaster_full_href), writer, farm_techs)
        flag = flag + 1

def parse_root_html(html, writer, farm_techs):  # 使用lxml爬取数据并清洗
    # 农业病虫草害图文数据库解析
    tree = lxml.html.fromstring(html)
    # 二级分类，如农作物-禾本科、蔬菜-根菜类和果树-仁果类
    item_row = tree.xpath("//tr[@class='item-row']")
    for row in item_row:
        # 三级分类，如水稻和小麦
        three_level_item = row.xpath("descendant::a[@class='item-subtitle']")
        for item in three_level_item:
            categoryId = item.text.strip()
            full_three_level_url = ROOT_URL + item.xpath("@href")[0]
            # 获取三级分类病虫草害url
            getLinkListFunc(categoryId, download_page(full_three_level_url), writer, farm_techs)


def main():
    url = DOWNLOAD_URL
    # 将数据导入到csv文件中
    writer = csv.writer(open('movies.csv', 'w', newline='', encoding='utf-8'))
    fields = ('title',  'intro', 'categoryId', 'content', 'libImgUrl', 'libCategoryTab')
    writer.writerow(fields)
    farm_techs = []
    while url:
        html = download_page(url)
        url = parse_root_html(html, writer, farm_techs)
    # execute_db(movies_info)

class ContentItem:
    def __init__(self):
        self.label = ""
        self.value = ""

if __name__ == '__main__':
    main()
