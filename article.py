import re
import os
import requests
from bs4 import BeautifulSoup
import urllib
import googletrans
from datetime import datetime

class Article:
    def __init__(self, author, title, post,image,category,URL):
        self.author = author
        self.title = title
        self.post = post
        self.image=image
        self.category=category
        self.URL=URL
    def get_Engcategory(self):
        category=self.category
        category=category.replace("\n","")
        category=category.replace(" ","")
        translator = googletrans.Translator()
        category=translator.translate(category,dest='en',src='ko').text
        category=category.replace(" ","")
        specialChars = "\/:*?<>|~!@#$%^&*()_+1234567890"
        for specialChar in specialChars:
            category=category.replace(specialChar, "")
        return category
    def as_markdown(self):
        return f"#{self.title}\n{self.post}"
    def save_file(self, dest):
        try:
            if not os.path.exists(dest):
                os.makedirs(dest)
        except OSError:
            print("Error: Failed to create the directory.")
        markdown = self.as_markdown()
        category=self.get_Engcategory()
        filename=self.title
        specialChars = "\/:*?<>|"
        Date=markdown[markdown.find("se_publishDate pcol2")+22:markdown.find("se_publishDate pcol2")+34]
        Date=(Date.replace(". ","-")).replace(".","-")
        if Date.strip()[-1]!='-':
            Date=Date+"-"
        if("전" in Date):
            Date=datetime.today().strftime("%Y-%m-%d")+"-"
        for specialChar in specialChars:
            filename=filename.replace(specialChar, "-")
        filename=filename.replace('\"', '-')
        filename=filename.replace(" - 네이버 블로그","")
        markdown = markdown[0: markdown.find("<!-- SE_DOC_HEADER_START -->"):] + markdown[markdown.find("<!-- SE_DOC_HEADER_END -->") ::]
        markdown="---\n"+"title: \""+filename+"\"\ncategories:\n - "+category+"\n---\n"+markdown
        os.makedirs("images/"+Date+filename)
        img_list = list()
        for img in self.image:
                img_list.append(img.get('data-lazy-src'))  # 큰사진의 
        for i in range(0,len(img_list),1):
            if(img_list[i]!=None):
                ext_idx=(img_list[i].find('?type'))
                ext=img_list[i][ext_idx-3:ext_idx]
                urllib.request.urlretrieve(img_list[i], "images/"+Date+filename+'/'+str(i)+'.'+ext)
        img__list = list()
        for img__ in self.image:
            img__list.append(img__.get('src'))  # 큰사진의 
        for i in range(0,len(img__list),1):
            if(img__list[i]!=None):
                ext__idx=(img__list[i].find('?type'))
                ext=img__list[i][ext__idx-3:ext__idx]
                if(ext=='.jp'):
                    ext='jpg'
                markdown=markdown.replace(img__list[i],'https://raw.githubusercontent.com/rage147-OwO/rage147-OwO.github.io/master/_images/images/'+Date+filename+'/'+str(i)+'.'+ext)
        markdown=markdown.replace("</img>","")
        with open(f"{dest}/"+Date+filename+".md", "w",encoding='UTF-8') as f:
                f.write(markdown)
        print(self.URL+"\n"+Date+filename+" "+category)
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

        return Article(
            category=iframe_soup.find("div","blog2_series").text,
            author=author,
            title=iframe_soup.find('title').text,
            post=iframe_soup.find('div', attrs={"id": f"post-view{article_id}"}),
            image=iframe_soup.select('.se-image-resource'),
            URL=url
        )
