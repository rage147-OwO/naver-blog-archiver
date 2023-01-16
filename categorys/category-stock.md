---
title : "stock"
layout: archivepermalink: categories/stock
author_profile: true
sidebar_main: true
---

{% assign posts = site.stock %}
{% for post in posts %} {% include archive-single2.html type=page.entries_layout %} {% endfor %}