# naver-blog-archiver
네이버 블로그 markdown으로 가져올 수 있습니다.
https://github.com/guzus/naver-blog-archiver

## Save blog article as md
```
python main.py --url https://blog.naver.com/guzus/222580566442 --dest dst
```

## Save all blog articles as md
```
python main.py --blog https://blog.naver.com/dls32208 --dest dst
```



## 추가한 것:
```
-파일명이 될 수 없는 단어 -로 대체(\/:*?<>|)->(-)
-폴더가 없는 경우 생성
-파일을 yyyy-mm-dd-title.md 형식으로 저장(For Jekyll)
-카테고리 한->영 자동 생성
-Jekyll 카테고리를 위해 nav_list_main, category-<Name>.md 자동생성
```






