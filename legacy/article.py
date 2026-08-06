import re
import os
import requests
from bs4 import BeautifulSoup
import urllib
import googletrans
from markdownify import markdownify
from datetime import datetime


def remove_first_sentence_and_whitespace(text):
    sentences = text.split('\n')
    remaining_text = '\n'.join(sentences[1:])
    remaining_text = remaining_text.strip()
    remaining_text = remaining_text.lstrip('\n')
    return remaining_text


class Article:
    def __init__(self, URL ,Author, Title,Date, Post,Image,Category):
        self.author = Author
        self.url=URL
        self.title = Title
        self.date=Date
        self.post = Post
        self.image=Image
        self.category=Category
    def get_Engcategory(self):
        category=self.category
        category=category.replace("\n","")
        category=category.replace(" ","")
        translator = googletrans.Translator()
        category=translator.translate(category,dest='en',src='ko').text
        category=category.replace(" ","")
        specialChars = "\/:*?<>|~!@#$%^&*()_+`-={}|[]\;':\",./<>?"
        Numbers="1234567890"
        for specialChar in specialChars:
            category=category.replace(specialChar, "specialChar")
        for Num in Numbers:
            category=category.replace(Num, "")
        return category
    def as_markdown(self):
        return f"#{self.title}\n{self.post}"
    def save_file(self, postpath,imagepath):
        markdown = self.as_markdown()
        category=self.get_Engcategory()
        filename=self.title
        specialChars = "\/:*?<>|""-"
        for specialChar in specialChars:
            filename=filename.replace(specialChar, "-")
        filename=filename.replace('\"', '-')
        filename=filename.replace(" - 네이버 블로그","")
        markdown = markdown[0: markdown.find("<!-- SE_DOC_HEADER_START -->"):] + markdown[markdown.find("<!-- SE_DOC_HEADER_END -->") ::]
        markdown="---\n"+"title: \""+filename+"\"\ncategories:\n - "+category+"\n---\n"+markdown
        os.makedirs(imagepath+"/"+self.date+filename, exist_ok=True)
        img_list = list()
        for img in self.image:
                img_list.append(img.get('data-lazy-src'))  # 큰사진의 
        for i in range(0,len(img_list),1):
            if(img_list[i]!=None):
                ext_idx=(img_list[i].find('?type'))
                urllib.request.urlretrieve(img_list[i], imagepath+"/"+self.date+filename+'/'+str(i)+'.'+"png")
        img__list = list()
        for img__ in self.image:
            img__list.append(img__.get('src'))  # 큰사진의 
        for i in range(0,len(img__list),1):
            if(img__list[i]!=None):
                ext__idx=(img__list[i].find('?type'))
                ext=img__list[i][ext__idx-3:ext__idx]
                if(ext=='.jp'):
                    ext='jpg'
                markdown=markdown.replace(img__list[i],'https://raw.githubusercontent.com/rage147-OwO/rage147-OwO.github.io/master/_images/images/'+self.date+filename+'/'+str(i)+'.'+"png")
        markdown=markdown.replace("</img>","")
        markdown = markdownify(str(markdown))
        markdown=remove_first_sentence_and_whitespace(markdown)
        print(markdown)
        with open(f"{postpath}/"+self.date+filename+".md", "w",encoding='UTF-8') as f:
                f.write(markdown)
        print(self.url+"\n"+self.date+filename+" "+category)
    def get_Korcategory(self):
        category=self.category
        category=category.replace(" ","")
        category=category.replace("\n","")
        return category   
    @staticmethod
    def get_article_from_url(url: str):
        url_matcher = re.compile("(.*)blog.naver.com/PostView.naver\?blogId=(.*)&logNo=(.*)")
        matches = url_matcher.match(url)
        author = matches.group(2)
        article_id = matches.group(3)
        response = requests.get(url).text
        iframe_soup = BeautifulSoup(response, 'html.parser')

        # 코드 블록 요소 찾기
        code_blocks = iframe_soup.find_all("div", {"class": "__se_code_view language-javascript"})

        # 코드 블록 요소를 markdown 코드 블록으로 변환
        for code_block in code_blocks:
            code_text = code_block.get_text().strip()
            markdown_code = "```\n"+code_text+"\n```"
            code_block.replace_with(BeautifulSoup(markdown_code, "html.parser"))

        post=iframe_soup.find('div', attrs={"id": f"post-view{article_id}"})
        date=post.find("span","se_publishDate pcol2").text[0:12]
        date=(date.replace(". ","-")).replace(".","-")
        if date.strip()[-1]!='-':
            date=date+"-"
        if("전" in date):
            date=datetime.today().strftime("%Y-%m-%d")+"-"
            date.replace("0","")
        return Article(
            URL=url,
            Author=author,
            Category=iframe_soup.find("div","blog2_series").text,
            Title=iframe_soup.find('title').text,
            Post=post,
            Image=iframe_soup.select('.se-image-resource'),
            Date= date
        )

