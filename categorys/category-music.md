---
title : "music"
layout: archivepermalink: categories/music
author_profile: true
sidebar_main: true
---

{% assign posts = site.music %}
{% for post in posts %} {% include archive-single2.html type=page.entries_layout %} {% endfor %}