---
layout: archive
title: "Academic CV of Prof. Dr.-Ing. Jan-Niklas Voigt-Antons"
permalink: /cv/
author_profile: true
description: "Academic CV of Prof. Dr.-Ing. Jan-Niklas Voigt-Antons including appointments, grants, teaching, service, and external profiles."
redirect_from:
  - /resume
---

<div class="section-block section-block--white" markdown="1">

[Download CV (PDF)](/files/cv.pdf){: .btn .btn--primary}

## Appointments

- **since 2024:** Professor of Computer Science (Immersive Media), Hamm-Lippstadt University of Applied Sciences (HSHL).
- **Current:** Director, Immersive Reality Lab.
- **Prior academic appointments:** TU Berlin and collaborating research environments (see publication timeline and external profiles).

## Education

- **Dr.-Ing.** (Engineering).
- Interdisciplinary profile bridging computer science, human factors, and empirical experience evaluation.

## Industry and transfer

- Applied R&D with industry and public stakeholders in XR, digital twins, and human-centered system evaluation.
- Transfer formats: prototypes, training modules, workshops, and pilot deployments.

</div>

<div class="section-block section-block--light" markdown="1">

## Grants and projects (selected)

{% for project in site.data.projects %}
- **{{ project.name }}** ({{ project.period }}) — {{ project.role }}
{% endfor %}

## Teaching (selected)

{% for course in site.data.courses %}
- **{{ course.title }}** ({{ course.years }}) — {{ course.objective }}
{% endfor %}

## Service (selected)

- Director, Immersive Reality Lab.
- Reviewing and service in venues including ACM CHI, IEEE ISMAR, ACM VRST, and QoMEX.
- Standardization-related dissemination and invited talks.

</div>

<div class="section-block section-block--white" markdown="1">

## Selected publications

- [Dynamic and Responsible Digital Twins for Extended Reality](/publication/2025-09-01-J32)
- [VR Cloud Gaming UX: Exploring the Impact of Network Quality on Emotion, Presence, Game Experience and Cybersickness](/publication/2024-08-01-C81)
- [Psychophysiology-based QoE Assessment: A Survey](/publication/2016-09-15-J6)
- [The digitalization of healthcare for older adults (editorship)](https://berlinup.books.tu-berlin.de/en/autor_innen/jan-niklas-voigt-antons/)

## External profiles

<div class="profile-links">
  <a href="https://scholar.google.com/citations?user=IFIaOZsAAAAJ" class="profile-chip"><i class="fas fa-graduation-cap" aria-hidden="true"></i> Google Scholar</a>
  <a href="https://orcid.org/0000-0002-2786-9262" class="profile-chip"><i class="fab fa-orcid" aria-hidden="true"></i> ORCID</a>
  <a href="https://dblp.org/pid/39/10762" class="profile-chip"><i class="fas fa-database" aria-hidden="true"></i> DBLP</a>
  <a href="https://dl.acm.org/profile/99659317387" class="profile-chip"><i class="fas fa-book" aria-hidden="true"></i> ACM author profile</a>
  <a href="https://www.hshl.de/personen/prof-dr-ing-jan-niklas-voigt-antons" class="profile-chip"><i class="fas fa-university" aria-hidden="true"></i> HSHL profile</a>
</div>

</div>
