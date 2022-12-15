import re
import os

import requests
from bs4 import BeautifulSoup


class Article:
    def __init__(self, author, title, post):
        self.author = author
        self.title = title
        self.post = post

    def as_markdown(self):
        return f"#{self.title}\n{self.post}"

    def save_file(self, dest):
        try:
            if not os.path.exists(dest):
                os.makedirs(dest)
        except OSError:
            print("Error: Failed to create the directory.")
        markdown = self.as_markdown()
        filename=self.title
        specialChars = "\/:*?<>|"
        Date=markdown[markdown.find("se_publishDate pcol2")+22:markdown.find("se_publishDate pcol2")+34]
        Date=(Date.replace(". ","-")).replace(".","-")
        if Date.strip()[-1]!='-':
            Date=Date+"-";
        for specialChar in specialChars:
            filename=filename.replace(specialChar, "-")
        filename=filename.replace('\"', '-')
        markdown = markdown[0: markdown.find("<!-- SE_DOC_HEADER_START -->"):] + markdown[markdown.find("<!-- SE_DOC_HEADER_END -->") ::]        
        with open(f"{dest}/"+Date+filename+".md", "w",encoding='UTF-8') as f:
            f.write(markdown)

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
            author=author,
            title=iframe_soup.find('title').text,
            post=iframe_soup.find('div', attrs={"id": f"post-view{article_id}"})
        )
