import argparse
import json
import re
import os
import shutil
from typing import List
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


def create_folder(directory: str):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        else:
            shutil.rmtree(directory)
            os.makedirs(directory)
    except OSError:
        print('Error: Creating directory. ' + directory)


def save_categories(categories_eng: List[str], categories_kor: List[str], category_path: str):
    for category_eng in categories_eng:
        with open(category_path + "/category-" + category_eng + ".md", "w", encoding='UTF-8') as f:
            f.write("---\ntitle: \"" + category_eng + "\"\nlayout: archive\n" + "permalink: categories/" + category_eng + "\nauthor_profile: true\nsidebar_main: true\n---\n\n{% assign posts = site.categories." + category_eng + " %}\n{% for post in posts %} {% include archive-single2.html type=page.entries_layout %} {% endfor %}")

    with open(category_path + "CategoryEng.md", "w", encoding='UTF-8') as f:
        f.write('\n'.join(categories_eng))

    with open(category_path + "CategoryKor.md", "w", encoding='UTF-8') as f:
        f.write('\n'.join(categories_kor))


def create_nav_list_main(saved_post_path: str, categories_eng: List[str], categories_kor: List[str]):
    with open("nav_list_main_original", "rt", encoding='UTF-8') as f:
        lines = f.readlines()

    with open(saved_post_path + "/nav_list_main", "w", encoding='UTF-8') as f:
        f.write(''.join(lines))
        f.write("\n")

        for kor_category_index in range(len(categories_kor)):
            f.write("\n<ul>\n{% for category in site.categories %}\n{% if category[0] == \"" + categories_eng[kor_category_index] + "\" %}\n<li><a href=\"/categories/" + categories_eng[kor_category_index] + "\" class=\"\">" + categories_kor[kor_category_index] + " ({{category[1].size}})</a></li>\n{% endif %}\n{% endfor %}\n</ul>\n")
        f.write("</li>\n</ul>\n</nav>")


if __name__ == "__main__":
    blog_id = "rage147-owo"
    saved_post_path = "SavedPost\\" + blog_id
    blog_url = "https://blog.naver.com/" + blog_id

    post_path = saved_post_path + "\\_posts"
    image_path = saved_post_path + "\\_images"
    category_path = saved_post_path + "\\_pages\\categories"

    EXCLUDED_CATEGORIES = ["2023일기", "2022일기","요리","게임","음악","주식","기타","내돈내산","영화","바이크"]  # Add names of the categories you want to exclude.
    EXCLUDED_CATEGORIES_CLEANED = [category.lower().replace(" ", "") for category in EXCLUDED_CATEGORIES]


    create_folder(saved_post_path)
    create_folder(post_path)
    create_folder(image_path)
    create_folder(category_path)

    category_eng_list = []
    category_kor_list = []

    for url in get_urls_from_blog_url(blog_url):
        article = Article.get_article_from_url(url=url)
        cleaned_category = article.category.lower().replace(" ", "").strip().replace("\n", "")


        print(f"Processing article: {article.title} ({cleaned_category})")
        if cleaned_category in EXCLUDED_CATEGORIES_CLEANED:
            print(f"Excluded category: {cleaned_category}")
            continue  # Skip the article if its category is in the excluded list.

        article.save_file(post_path, image_path)
        eng_category = article.get_Engcategory()

        if eng_category not in category_eng_list:
            category_eng_list.append(eng_category)
            category_kor_list.append(article.get_Korcategory())


    save_categories(category_eng_list, category_kor_list, category_path)
    create_nav_list_main(saved_post_path, category_eng_list, category_kor_list)


