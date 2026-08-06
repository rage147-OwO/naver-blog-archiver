
import schedule
import time
import feedparser

rss_url = "https://rss.blog.naver.com/dls32208.xml"

def get_rss():
    feed = feedparser.parse(rss_url)
    
    print("Title: ", feed["feed"]["title"])
    print("Description: ", feed["feed"]["description"])

    for entry in feed.entries:
        print("Title: ", entry.title)
        print("Link: ", entry.link)
        print("Description: ", entry.description)
        print("Published Date: ", entry.published)
        print("\n")

# 매일 12시에 get_rss() 함수를 실행합니다.
schedule.every().day.at("12:00").do(get_rss)

while True:
    # schedule.run_pending() 함수를 이용하여 매일 정해진 시간에 get_rss() 함수를 실행합니다.
    schedule.run_pending()

    # 사용자가 원할 때 수동으로 RSS를 받습니다.
    user_input = input("RSS를 받으시겠습니까? (Y/N)")
    if user_input.lower() == "y":
        get_rss()

    # 1초마다 코드를 실행합니다.
    time.sleep(1)
