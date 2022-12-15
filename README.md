# naver-blog-archiver
네이버 블로그 markdown으로 가져올 수 있습니다
https://github.com/guzus/naver-blog-archiver

## Save blog article as md
```
python main.py --url https://blog.naver.com/guzus/222580566442 --dest dst
```

## Save all blog articles as md
```
python main.py --blog https://blog.naver.com/dls32208 --dest dst

<--Save all만 해봤습니다


추가한 것:
-파일명이 될 수 없는 단어 -로 대체(\/:*?<>|)->(-)
-폴더가 없는 경우 생성
-파일을 yyyy-mm-dd-title.md 형식으로 저장(For Jekyll)

추가해야 할 것:
-카테고리 가져오고 적용하기
-이미지 가져오기



```
