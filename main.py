import argparse
import json
import re
import os
import shutil
from typing import List
import requests
from bs4 import BeautifulSoup as bs
from article import Article


def get_urls_from_blog_url(blog_url: str) -> List[str]:
    author = re.compile("(.*)blog.naver.com/(.*)").match(blog_url).group(2)
    curr_page, count_per_page, total_count = 1, 5, None
    article_urls = []
    while total_count is None or curr_page * count_per_page <= total_count:
        url = f"https://blog.naver.com/PostTitleListAsync.naver?blogId={author}&currentPage={curr_page}&countPerPage={count_per_page}"
        response = requests.get(url).text.replace('\\', '\\\\')
        data = json.loads(response)
        posts = data.get("postList")
        total_count = int(data.get("totalCount"))
        for post in posts:
            log_no = post.get("logNo")
            article_url = f"https://blog.naver.com/PostView.naver?blogId={author}&logNo={log_no}"
            article_urls.append(article_url)
        curr_page += 1
    return article_urls


def get_urls() -> List[str]:
    return ["https://blog.naver.com/dls32208/"]
    
def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            shutil.rmtree(directory)
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)

if __name__ == "__main__":
    BlogMainLink="https://blog.naver.com/dls32208"
    page = requests.get(BlogMainLink)
    soup = bs(page.text, "html.parser")
    print(soup)
    main_links = soup.select("iframe")[0]['src']
    main_links=BlogMainLink+main_links
    page = requests.get(main_links)
    soup = bs(page.text, "html.parser")
    



"""
    createFolder("images")
    createFolder("posts")
    parser = argparse.ArgumentParser(description='options')
    parser.add_argument('--url', help='url of a blog article')
    parser.add_argument('--blog', help='url of a blog')
    parser.add_argument('--dest', help='destination directory where blog article should be saved')
    args = parser.parse_args()

    dest = args.dest or "posts"
    blog = "https://blog.naver.com/dls32208"

    if blog:
        for url in get_urls_from_blog_url(blog):
            Article.get_article_from_url(url=url).save_file(dest=dest)
"""