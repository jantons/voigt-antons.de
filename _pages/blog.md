---
layout: archive
title: "Blog"
permalink: /blog/
author_profile: true
---

<div class="section-block section-block--white" markdown="1">

A collection of all blog entries in reverse chronological order.

</div>

<div class="section-block section-block--light">
{% include base_path %}
{% for post in site.posts %}
  {% include archive-single.html %}
{% endfor %}
</div>
