# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import time, datetime
import MySQLdb
import random
import logging
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, UnexpectedAlertPresentException

import  chardet
# from selenium import PhantomJS
import sys
reload(sys)
sys.setdefaultencoding('utf8')

def element_exist(driver,path):
    driver.implicitly_wait(3)
    status = 0
    try:
        driver.find_element_by_xpath(path)
        status = 1
    except NoSuchElementException,e:
        # time.sleep(1)
        status = 0
    return status

def wait_element(driver, path):
    driver.implicitly_wait(10)
    status = 0
    # while status ==0:
    try:
        driver.find_element_by_xpath(path)
        status = 1
    except NoSuchElementException, e:
        driver.refresh()
        try:
            driver.find_element_by_xpath(path)
            status = 1
        except NoSuchElementException, e:
            logging.error(e.message)
            status = 0
    return status

def sql_query(sql_statement):
        conn=MySQLdb.connect(host='localhost',user='root',passwd='admin',db='weibo',port=3306,charset='utf8')
        cur = conn.cursor()
        sql = sql_statement
        try:
            cur.execute(sql)
            conn.commit()
            #print 'sql statement success'
        except StandardError, e:
            conn.rollback()
            logging.error( '(sql statement fail): '+sql_statement)

def search_weibo_name(driver):
    driver.implicitly_wait(10)
    con = MySQLdb.connect('localhost', 'root', 'admin', 'weibo');
    with con:
        cur = con.cursor()
        cur.execute("SELECT distinct weibo_name_url FROM weibo")
        rows = cur.fetchall()
        total_num = len(rows)
        cur_num = 1
        for row in rows:
            try:
                driver.get( row[0])
                # driver.implicitly_wait(random.randint(2,3))
                user_info = driver.find_elements_by_xpath('//div[@class="ut"]/span[@class="ctt"]')
                driver.find_element_by_xpath('//div[@class="ut"]/a[contains(text(),"资料")]').click()
                # driver.implicitly_wait(random.randint(2,3))
                vip_info_temp = driver.find_element_by_xpath('//div[contains(@class, "c") and contains(text(), "会员等级")]')
                vip_info = vip_info_temp.text.strip()[5:8].strip()
                basic_info_temp = driver.find_element_by_xpath('//div[contains(@class,"tip") and contains(text(),"基本信息")]/following-sibling::*[1]')
                basic_info = basic_info_temp.text.strip().replace(chr(39), chr(32)).replace(chr(10),chr(32)).encode('gbk','ignore').decode('gbk','ignore')
                nick_name_temp = basic_info_temp.text.strip().split(chr(10))[0]
                nick_name = nick_name_temp[3:len(nick_name_temp)]

                sql = "insert into user(weibo_name,weibo_level,basic_info,user_url) values('%s','%s','%s','%s');" %\
                      (nick_name,vip_info,basic_info,row[0])
                sql_query(sql)
                logging.info('update weibo user success! '+str(cur_num)+'/'+str(total_num)+' '+row[0])
                cur_num +=1
                # for i in range(len(user_info)):
                #     print user_info[i].text.strip().encode('gbk','ignore').decode('gbk','ignore')
                # print '*****************************************************************'
                # print nick_name
                # print vip_info
                # print row[0]
                # print basic_info
            except NoSuchElementException, e:
                driver.back()
                logging.error(e.message)
                cur_num += 1
                continue
            except StandardError, e:
                cur_num +=1
                continue

def search_weibo_ping(driver):
    driver.implicitly_wait(10)
    con = MySQLdb.connect('localhost', 'root', 'admin', 'weibo');
    with con:
        cur = con.cursor()
        cur.execute("select DISTINCT weibo_ping_url,weibo_ping weibo_ping from weibo where weibo_ping <> 0 order by CONVERT(weibo_ping, SIGNED) DESC")
        rows = cur.fetchall()
        total_num = len(rows)
        cur_num = 1
        for row in rows:
            # print row[0]
            # print row[1]
            try:
                driver.get(row[0])
                time.sleep(random.randint(3,4))
                # if element_exist(driver,'//div[@id="pagelist"]') == 1:
                # row[1] here could be updated according to latest comments amount
                if int(row[1]) > 10:
                    if wait_element(driver, '//div[contains(@class,"c") and contains(@id, "C_")]') == 1:
                        page_num_temp = driver.find_element_by_xpath('//div[@id="pagelist"]').text.strip()
                        page_num = int(filter(lambda x:x.isdigit(),page_num_temp).strip()[1:])
                        num = 2
                        while num <= page_num:
                            try:
                                if element_exist(driver,'//div[@id="pagelist"]') == 1:
                                    pinglun_ren = driver.find_elements_by_xpath('//div[contains(@class,"c") and contains(@id, "C_")]/a[1]')
                                    pinglun =driver.find_elements_by_xpath('//div[contains(@class,"c") and contains(@id, "C_")]/span[@class="ctt"]')
                                    for p in range(len(pinglun)):
                                        weibo_ping_name = pinglun_ren[p].text.strip().replace(chr(39),chr(32)).encode('gbk','ignore').decode('gbk','ignore')
                                        weibo_ping = pinglun[p].text.strip().replace(chr(39),chr(32)).encode('gbk','ignore').decode('gbk','ignore')
                                        sql = "insert into ping(weibo_ping_name,weibo_ping_content,weibo_ping_url) values('%s','%s','%s');" %\
                                              (weibo_ping_name, weibo_ping,row[0])
                                        sql_query(sql)
                                    driver.find_element_by_xpath('//div[@class="pa"]/form/div/input[@name="page"]').clear()
                                    driver.find_element_by_xpath('//div[@class="pa"]/form/div/input[@name="page"]').send_keys(num)
                                    driver.find_element_by_xpath('//div[@class="pa"]/form/div/input[@type="submit"]').click()
                                    # num+=1
                                else:
                                    driver.back()
                                    time.sleep(1)
                            except NoSuchElementException, e:
                                driver.back()
                                time.sleep(1)
                            except StaleElementReferenceException,e:
                                driver.back()
                                time.sleep(1)
                            except UnexpectedAlertPresentException, e:
                                driver.back()
                                time.sleep(1)
                            finally:
                                num += 1
                    else:
                        driver.back()
                        continue
                else:
                    # if wait_element(driver,  '//div[contains(@class,"c") and contains(@id, "C_")]') == 1:
                    if element_exist(driver,  '//div[contains(@class,"c") and contains(@id, "C_")]') == 1:
                        pinglun_ren = driver.find_elements_by_xpath('//div[contains(@class,"c") and contains(@id, "C_")]/a[1]')
                        pinglun =driver.find_elements_by_xpath('//div[contains(@class,"c") and contains(@id, "C_")]/span[@class="ctt"]')
                        for p in range(len(pinglun)):
                            weibo_ping_name = pinglun_ren[p].text.strip().replace(chr(39),chr(32)).encode('gbk','ignore').decode('gbk','ignore')
                            weibo_ping = pinglun[p].text.strip().replace(chr(39),chr(32)).encode('gbk','ignore').decode('gbk','ignore')
                            sql = "insert into ping(weibo_ping_name,weibo_ping_content,weibo_ping_url) values('%s','%s','%s');" %\
                                  (weibo_ping_name, weibo_ping,row[0])
                            sql_query(sql)
                    else:
                        driver.refresh()
                        logging.error('not found comments! '+str(cur_num)+'/'+str(total_num)+' '+row[0])
                        continue

            except NoSuchElementException, e:
                driver.back()
                logging.error(e.message)
                continue
            except StaleElementReferenceException,e:
                driver.back()
                logging.error(e.message)
                continue
            except UnexpectedAlertPresentException, e:
                driver.back()
                continue
            else:
                logging.info('update weibo ping success! '+str(cur_num)+'/'+str(total_num)+' '+row[0])
            finally:
                cur_num += 1

def search_weibo_content(driver,key_words):
    driver.implicitly_wait(10)
    for key_word in key_words:
        logging.info("starting to search keyword: "+ key_word.decode('utf8'))
        # print 'start searching: ' + key_word.decode('utf8')
        driver.find_element_by_name("keyword").send_keys(key_word.decode('utf8'))
        driver.find_element_by_name("smblog").click()
        # try:
        #     if driver.find_element_by_xpath('//div[contains(@class,"c") and contains(text(),"抱歉")]').is_displayed():
        #         logging.info('no result found for keyword: '+key_word)
        #         break
        # except StandardError, e:
        #     logging.info('has result!')
        ## here should add if case to detect if result are found!
        total_count = driver.find_element_by_xpath('//div[@id="pagelist"]/form/div').text
        ##need to update cal counter method
        counter =  int(filter(lambda x:x.isdigit(),total_count))-1000
        # print counter
        for i in range(counter):
            if len(driver.find_elements_by_xpath('//body/div[@class="c"]'))<5:
                driver.find_element_by_name("smblog").click()
                # driver.implicitly_wait(random.randint(10,15))
                logging.info(str(i) + ': fetch meet blank page!')
                # print str(i) + ': fetch meet blank page!'
                continue
            try:
                weibo_id = driver.find_elements_by_xpath('//div[contains(@class,"c") and contains(@id,"M_")]')
                weibo_name = driver.find_elements_by_xpath('//div[contains(@class,"c") and contains(@id,"M_")]/div[1]/a[@class="nk"]')
                # weibo_uid = driver.find_elements_by_xpath('//div[contains(@class,"c") and contains(@id,"M_")]/div[1]/a[@class="nk"]')
                weibo_content = driver.find_elements_by_xpath('//div[contains(@class,"c") and contains(@id,"M_")]/div[1]/span[@class="ctt"]')
                weibo_zan = driver.find_elements_by_xpath('//div[contains(@class,"c") and contains(@id,"M_")]/div[last()]/a[contains(text(),"赞[")]')
                weibo_zhuan= driver.find_elements_by_xpath('//div[contains(@class,"c") and contains(@id,"M_")]/div[last()]/a[contains(text(),"转发[")]')
                weibo_ping = driver.find_elements_by_xpath('//div[contains(@class,"c") and contains(@id,"M_")]/div[last()]/a[contains(text(),"评论[")]')
                weibo_time= driver.find_elements_by_xpath('//div[contains(@class,"c") and contains(@id,"M_")]/div[last()]/span[@class="ct"]')

                for j in range(len(weibo_name)):
                    try:

                        w_id = weibo_id[j].get_attribute("id")
                        name =  weibo_name[j].text.strip().replace(chr(39), chr(32)).encode('gbk','ignore').decode('gbk','ignore')
                        name_url = weibo_name[j].get_attribute("href")
                        ##filter ' and illegal gbk code
                        content =  weibo_content[j].text.strip().replace(chr(39), chr(32)).encode('gbk','ignore').decode('gbk','ignore')
                        zan =   filter(lambda x:x.isdigit(),weibo_zan[j].text.strip())
                        zhuan =  filter(lambda x:x.isdigit(),weibo_zhuan[j].text.strip())
                        ping = filter(lambda x:x.isdigit(),weibo_ping[j].text.strip())
                        ping_url = weibo_ping[j].get_attribute("href")
                        time_device = weibo_time[j].text.strip().replace(chr(39), chr(32)).split('来自')
                        # content.replace(chr(39), chr(32));
                        pub_time = time_device[0]
                        ##within 60 minites
                        if '分钟前' in pub_time:
                            pub_time = (datetime.datetime.now() + datetime.timedelta(minutes= -1*int(filter(lambda x:x.isdigit(),pub_time)))).strftime("%Y-%m-%d %H:%M:%S")
                        ##today and 60 minites ago
                        elif '今天' in pub_time:
                            str6 =  filter(lambda x:x.isdigit(),pub_time).strip()
                            pub_time = datetime.datetime(datetime.datetime.now().year,
                                 datetime.datetime.now().month,
                                 datetime.datetime.now().day,
                                 int(str6[0:2]),
                                 int(str6[2:4]),
                                 0).strftime("%Y-%m-%d %H:%M:%S")
                        ##this year till yesterday
                        elif   '月' in pub_time or '日' in pub_time:
                            str6 =  filter(lambda x:x.isdigit(),pub_time).strip()
                            pub_time = datetime.datetime(datetime.datetime.now().year,int(str6[0:2]),int(str6[2:4]),int(str6[4:6]),int(str6[6:8]),0).strftime("%Y-%m-%d %H:%M:%S")
                        if len(time_device) == 2:
                            device = time_device[1].encode('gbk','ignore').decode('gbk','ignore')
                        else:
                            device = 'None Device'
                        # if len(content and chr(39)) >0:

                        sql = "insert into weibo(key_word,weibo_id,weibo_name,weibo_content,weibo_zan,weibo_zhuan,weibo_ping,weibo_time,weibo_device,weibo_name_url,weibo_ping_url)" \
                              " values('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s','%s');" %\
                              (key_word,w_id,name,content,zan,zhuan,ping,pub_time,device,name_url,ping_url)
                        sql_query(sql)
                    except StandardError, e:
                        logging.error('fetch data error! '+str(i+1)+':'+str(j)+''+e.message)
                        # print 'fetch data error! '+str(i+1)+':'+str(j)+''+e.message
                        continue
                    # print str(i)+':'+str(j)
                ##option 1: click next page
                # driver.find_element_by_xpath('//div[@class="pa"]/form/div/a[text()="下页"]').click()
                ##option 2: jump to specified page
                logging.info(str(i+1)+' page fetch done!')
                # print str(i+1)+' page fetch done!'
                driver.find_element_by_xpath('//div[@class="pa"]/form/div/input[@name="page"]').clear().send_keys(i+2)
                driver.find_element_by_xpath('//div[@class="pa"]/form/div/input[@value="跳页"]').click()
                time.sleep(random.randint(3, 5))
            except NoSuchElementException, e:
                driver.back()
                logging.error(str(i+1)+' page fetch data error!'+e.message)
                # print str(i+1)+' page fetch data error!'+e.message
                # print name
                # print content.encode('gbk','ignore')
                continue
                driver.find_element_by_xpath('//div[@class="pa"]/form/div/a[text()="下页"]').click()
                driver.implicitly_wait(random.randint(5,7))
        logging.info('fetching '+ key_word.decode('utf8')+' done!')
        driver.find_element_by_name("keyword").clear()

def search_weibo(key_words,wait_seconds):
    driver = webdriver.Firefox()
    # driver = webdriver.PhantomJS()
    driver.get('http://weibo.cn/search/')
    # driver.get('http://search.people.com.cn/rmw/GB/rmwsearch/')
    driver.find_element_by_name("mobile").send_keys('emailzombie@126.com')
    driver.find_element_by_xpath('//input[@type="password"]').send_keys("abc314159")
    verify_code = driver.find_element_by_xpath('//input[@name="code"]')
    actions = ActionChains(driver)
    actions.move_to_element(verify_code)
    actions.click(verify_code)
    actions.perform()
    ##waiting for input verify code
    time.sleep(wait_seconds)
    logging.info("successfully login weibo!")
    logging.info('starting to search weibo contents!')
    # search_weibo_content(driver,key_words)
    logging.info('starting to search weibo name info!')
    # search_weibo_name(driver)
    logging.info('starting to search weibo comments!')
    search_weibo_ping(driver)
    # driver.quit()

def initLogging(logFilename):
    """Init for logging
    """
    logging.basicConfig(
                    level    = logging.INFO,
                    format   = '%(asctime)s %(filename)s[LINE %(lineno)d] %(levelname)s: %(message)s',
                    datefmt  = '%m-%d %H:%M',
                    filename = logFilename,
                    filemode = 'w');
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler();
    console.setLevel(logging.INFO);
    # set a format which is simpler for console use
    formatter = logging.Formatter('LINE %(lineno)-4d : %(levelname)-8s %(message)s');
    # tell the handler to use this format
    console.setFormatter(formatter);
    logging.getLogger('').addHandler(console);

# main function
if __name__ == "__main__":
    logFilename = "weibo.log"
    initLogging(logFilename)
    key_words = ["正大广场","正大集团"]
    search_weibo(key_words,20)
    logging.info( 'fetch all key words done!')




