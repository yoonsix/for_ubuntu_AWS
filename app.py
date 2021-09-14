import pandas as pd 
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from tqdm import tqdm
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time



path = '/home/ubuntu/chromedriver '
options = webdriver.ChromeOptions()
options.add_argument("headless")
driver = webdriver.Chrome(path, options=options)
# driver = webdriver.Chrome(path)
driver.implicitly_wait(4) 

def dataload():
       df = pd.read_csv('final.csv')
       df = df[['url','name', 'title', 'hashtag', 'hashtag_num', 'image', 'profile', 'menu',
              'post_total', 'like', 'sex', 'visit', 'neighbor' ]]
       df = df.iloc[:10,:]
       url_list = df[['url']]
       url_list = df['url'].tolist()
       return df,url_list


def no_space(text):
       text1 = re.sub('&nbsp; | &nbsp;| \n|\t|\r', '', text)
       text2 = re.sub('\n\n', '', text1)
       text2 = text2.replace('\n', '')
       return text2

def recent_1month_post_cnt(monthCheck,url_blogId,checkpoint):
       if checkpoint:
              blog_id = url_blogId
              url = f'https://blog.naver.com/PostList.naver?blogId={blog_id}&skinType=&skinId=&from=menu'
              driver.get(url)
              try:
                     elem2=driver.find_element_by_id('listCountToggle')
                     elem2.send_keys(Keys.ENTER)
              except:
                     elem2 = driver.find_element_by_partial_link_text("목록열기")
                     elem2.send_keys(Keys.ENTER)
                     time.sleep(1)
                     elem2=driver.find_element_by_id('listCountToggle')
                     elem2.send_keys(Keys.ENTER)
              elem2 = driver.find_element_by_partial_link_text("30줄 보기")
              elem2.send_keys(Keys.ENTER)
              time.sleep(1)
       
       li = []
       results = []
       unique_check = True
       blog_month_cnt = 0
       now = datetime.now()
       now_time = str(now).split(' ')[0].split('-')
       nowy = now_time[0] # 현재 년도
       nowm = int(now_time[1]) # 현재 월 
       nowd = int(now_time[2]) # 현재 일 
       
       contents=driver.find_elements_by_class_name("wrap_td")
       contents = contents[2:]

       for index, content in enumerate(contents):
              # print(content.text)
              if ((nowy+'. ') in content.text)|("시간 전" in content.text)|("분 전" in content.text):
                     li.append(contents[index-1].text)
                     li.append(content.text)
                     for i in results:
                            if i==li:
                                   unique_check = False
                     if unique_check:
                            results.append(li)
                     li = []

       final_post_time = []
       for i in results:
              if "시간 전" in i[1]:
                     blog_month_cnt = blog_month_cnt + 1
              elif "분 전" in i[1]:
                     blog_month_cnt = blog_month_cnt + 1
              else:
                     final_post_time.append(i[1])
       
       # print(final_post_time)
       beefore_one_month = now - relativedelta(months=1)
       beefore_one_month_time = str(beefore_one_month).split(' ')[0].split('-')
       be1m = int(beefore_one_month_time[1]) # 한달전 월 
       be1md = int(beefore_one_month_time[2]) # 한달전 일 

       for i in final_post_time:
              post_month = int(i.split('.')[1])
              post_day = int(i.split('.')[2])
              if post_month == nowm:
                     blog_month_cnt = blog_month_cnt + 1
              if (post_month == be1m) & (be1md<=post_day):
                     blog_month_cnt = blog_month_cnt + 1
       # print('blog_month_cnt : ', blog_month_cnt)
       if blog_month_cnt>=30:
              monthCheck = monthCheck + 1
              # print('monthCheck', monthCheck)
              page_bar=driver.find_elements_by_class_name("blog2_paginate")[0]
              pages = page_bar.find_elements_by_css_selector('a')[monthCheck-1] 
              pages.send_keys(Keys.ENTER)
              time.sleep(1)
              return recent_1month_post_cnt(monthCheck,'상관없음',False)
       else:
              return (blog_month_cnt+monthCheck*30)

def scrapping_con_rep_com(url_array):
       url_list = url_array
       result = []
       reply_cnt = []
       comment_cnt = []
       recent_1month_post_total = []

       for url in url_list:
              
              # 최근 한달간 포스트 개수 세기 
              data = recent_1month_post_cnt(0,url.split('/')[-2],True)
              # print('한달동안포스팅개수 : ',data)
              recent_1month_post_total.append(data)
              
              content_list = ''
              driver.get(url)
              try:
                     driver.switch_to.frame('mainFrame')
                     overlays = ".se-component.se-text.se-l-default" 
                     contents = driver.find_elements_by_css_selector(overlays)
                     for content in contents:
                            content_list = content_list+ content.text 
                     result.append(no_space(content_list)+'.') 
              except:
                     result.append('비공개') 
                     reply_cnt.append(0) 
                     comment_cnt.append(0) 
                     
                     continue              
              try:
                     url_id = url.split('/')
                     elem2=driver.find_element_by_id(f"Comi{url_id[-1]}")
                     elem2.send_keys(Keys.ENTER)
              except:
                     # print('댓글창이없습니다')
                     reply_cnt.append(0) 
                     comment_cnt.append(0) 
                     continue
              try:
                     comment=driver.find_elements_by_class_name("u_cbox_text_wrap")
                     comment_cnt.append(len(comment)) # 전체댓글수 집계
                     # print('전체댓글개수 : ',len(comment))
              except:
                     # print('댓글이없습니다')
                     reply_cnt.append(0) 
                     comment_cnt.append(0)
                     continue

              reply=driver.find_elements_by_class_name("u_cbox_ico_reply")
              reply_cnt.append(len(reply))
              # print('대댓글개수: ',len(reply))
              # print('------------------------------')

       return result, comment_cnt, reply_cnt, recent_1month_post_total

df,url_list = dataload()
result,comment_cnt,reply_cnt, recent_1month_post_total = scrapping_con_rep_com(url_list)
df['content'] = result
df['comment_cnt'] = comment_cnt
df['reply_cnt'] = reply_cnt
df['recent_1month_post_total'] = recent_1month_post_total
df.to_csv(f'result0to10.csv',index=False)

driver.quit()


# https://blog.naver.com/cjinwoo1
# 크롤링 코드 워크플로우 

# 1. 비공개 글 유무 판단 
# 비공개 글일때 -> continue

# 2. 댓글 유무 판단 
# 댓글창 자체가 없을때 -> continue 

# 3. 댓글이 없을때 -> continue

# 4. 마지막 
# try : 대댓글뽑는코드
# except : 대댓글.append(0)

# 마지막 관문
# 30개씩 띄우고 다음페이지 넘기기까지,,,,,,,, 해야 최종이다. 


