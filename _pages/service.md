---
layout: archive
title: "Service & Leadership"
permalink: /service/
author_profile: true
description: "Academic leadership, reviewing, program committees, standardization, and invited talks."
---

## Leadership

- **{{ site.data.service.leadership.role }}**, Hamm-Lippstadt University of Applied Sciences.
- **Mission:** {{ site.data.service.leadership.mission }}
- **Team structure:** {{ site.data.service.leadership.team_structure }}
- **Infrastructure:** {{ site.data.service.leadership.infrastructure | join: ", " }}

## Reviewing and program committees (selected)

### Conferences
{% for conf in site.data.service.reviewing.conferences %}
- {{ conf }}
{% endfor %}

### Journals
{% for journal in site.data.service.reviewing.journals %}
- {{ journal }}
{% endfor %}

## Community and standardization

{% for item in site.data.service.community %}
- [{{ item.label }}]({{ item.url }})
{% endfor %}

## Invited talks and dissemination

See [Talks and presentations](/talks/) for recent invited talks, conference contributions, and media appearances.
