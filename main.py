import argparse
import json
import re
import os
import shutil
from typing import List
from bs4 import BeautifulSoup

import requests

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
def SetCategory(userid):
    BlogCategoryLink="https://rss.blog.naver.com/"+userid+".xml"
    page = requests.get(BlogCategoryLink)
    soup = BeautifulSoup(page.text, "html.parser")
    CategoryList=soup.find_all("category")
    for Category in CategoryList:
        print(Category.text)
def SaveHtml(Link):
    page = requests.get(Link)
    soup = BeautifulSoup(page.text, "html.parser")
    print(page.text)
    file = open('save.txt', 'w')  
    for i in page.text:
        file.write(i)
    file.close() 
if __name__ == "__main__":
    UserID="dls32208"
    createFolder("images")
    createFolder("posts")
    blog = "https://blog.naver.com/dls32208"

    if blog:
        for url in get_urls_from_blog_url(blog):
            Article.get_article_from_url(url=url).save_file(dest=dest)

class Article:
    def __init__(self, author, title, post,image,category):
        self.author = author
        self.title = title
        self.post = post
        self.image=image
        self.category=category
    def as_markdown(self):
        return f"#{self.title}\n{self.post}"

    def save_file(self, dest):
        try:
            if not os.path.exists(dest):
                os.makedirs(dest)
        except OSError:
            print("Error: Failed to create the directory.")
        markdown = self.as_markdown()
        category=self.category
        category=category.replace("\n","")
        filename=self.title
        specialChars = "\/:*?<>|"
        Date=markdown[markdown.find("se_publishDate pcol2")+22:markdown.find("se_publishDate pcol2")+34]
        Date=(Date.replace(". ","-")).replace(".","-")
        if Date.strip()[-1]!='-':
            Date=Date+"-";
        for specialChar in specialChars:
            filename=filename.replace(specialChar, "-")
        filename=filename.replace('\"', '-')
        filename=filename.replace(" - 네이버 블로그","")
        markdown = markdown[0: markdown.find("<!-- SE_DOC_HEADER_START -->"):] + markdown[markdown.find("<!-- SE_DOC_HEADER_END -->") ::]
        markdown="---\n"+"title: "+filename+"\ncategories:\n - "+category+"\n---\n"+markdown
        
        with open(f"{dest}/"+Date+filename+".md", "w",encoding='UTF-8') as f:
            f.write(markdown)
        os.makedirs("images/"+Date+filename)
        img_list = list()
        for img in self.image:
                img_list.append(img.get('data-lazy-src'))  # 큰사진의 
        for i in range(0,len(img_list),1):
            if(img_list[i]!=None):
                ext_idx=(img_list[i].find('?type'))
                ext=img_list[i][ext_idx-3:ext_idx]
                urllib.request.urlretrieve(img_list[i], "images/"+Date+filename+'/'+str(i)+'.'+ext)
        
        



    @staticmethod
    def get_article_from_simple_url(url: str):
        url_matcher = re.compile("(.*)blog.naver.com/(.*)/(.*)")
        matches = url_matcher.match(url)
        author = matches.group(2)
        article_id = matches.group(3)

        url = f"https://blog.naver.com/PostView.naver?blogId={author}&logNo={article_id}"
        return Article.get_article_from_url(url)

    @staticmethod
    def get_article_from_url(url: str):
        print(url)
        url_matcher = re.compile("(.*)blog.naver.com/PostView.naver\?blogId=(.*)&logNo=(.*)")
        matches = url_matcher.match(url)
        author = matches.group(2)
        article_id = matches.group(3)

        response = requests.get(url).text
        iframe_soup = BeautifulSoup(response, 'html.parser')

        return Article(
            category=iframe_soup.find("div","blog2_series").text,
            author=author,
            title=iframe_soup.find('title').text,
            post=iframe_soup.find('div', attrs={"id": f"post-view{article_id}"}),
            image=iframe_soup.select('.se-image-resource')
        )
