from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from config import *
import pymongo
browser = webdriver.Chrome()
wait = WebDriverWait(browser,20)
client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]
#京东上搜索关键词，发起请求
def get_KEYWORD():
    print('正在狗东搜索关键词...当前关键词：'+KEYWORD)
    try:
        browser.get('https://www.jd.com')
        input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#key')))
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#search > div > div.form > button')))
        input.send_keys(KEYWORD)
        submit.click()
        pagenumber = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'#J_bottomPage > span.p-skip > em:nth-child(1) > b'))).text
        get_product_info()
        return int(pagenumber)
    except TimeoutException:
        return get_KEYWORD()
#实现翻页功能
def get_next_page(pagenumber):
    print('-------------正在获取第'+str(pagenumber)+'页..-----------------')
    try:
        js = "window.scrollTo(972,503)"
        browser.execute_script(js)      #---------解决元素可定位却不可用。报错：...is not clickable ...
        next = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_topPage > a.fp-next')))
        next.click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'#J_topPage > span > b'),str(pagenumber)))
        get_product_info()
    except TimeoutException:
        get_next_page(pagenumber)
#获取商品信息
def get_product_info():
    wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.w .container .g-main2 .m-list .ml-wrap .goods-list-v2 .clearfix .gl-item'))
    )
    html = browser.page_source
    doc = pq(html)
    goods = doc('.w .container .g-main2 .m-list .ml-wrap .goods-list-v2 .clearfix .gl-item').items()
    for good in goods:
        link_and_img = pq(good.find('.gl-i-wrap .p-img').html())
        product = {
            'good_link':'https:'+str(link_and_img.find('a').attr('href')),
            'good_img' : 'https:'+str(link_and_img.find('img').attr('data-lazy-img')),
            'good_price': good.find('.gl-i-wrap .p-price').text(),
            'good_name' : good.find('.gl-i-wrap .p-name').text(),
            'good_commit' : good.find('.gl-i-wrap .p-commit').text(),
            'good_shop' : good.find('.gl-i-wrap .p-shop').text()
        }
        # if product['good_img'] == 'done':
        #     product['good_img'] = 'https:'+str(link_and_img.find('img').attr('src'))
        # print(product['good_img'])
        save_2_mongo(product)
#存储到MONGO
def save_2_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('保存到MONGO成功..')
    except:
        print('-------存储失败啦！------')

def main():
    try:
        pagenum = get_KEYWORD()
        for i in range(2,pagenum+1):
            get_next_page(i)
    except:
        print('某些位置出错了..')
    finally:
        browser.close()

if __name__ == '__main__':
    main()