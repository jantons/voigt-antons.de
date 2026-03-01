---
permalink: /
title: "XR Researcher & Professor of Immersive Media"
author_profile: true
description: "Prof. Dr.-Ing. Jan-Niklas Voigt-Antons: Human-centered XR and experience measurement for spatial interaction, learning, training, digital health, and immersive media research."
redirect_from: 
  - /about/
  - /about.html
---

<div class="section-block section-block--white">

**Prof. Dr.-Ing. Jan-Niklas Voigt-Antons** is a Professor of Computer Science
(Immersive Media) at Hamm-Lippstadt University of Applied Sciences (HSHL) and
Director of the Immersive Reality Lab. His research focuses on human-centered
Extended Reality (XR), Quality of Experience (QoE) measurement, psychophysiological
sensing, and digital health applications. With over 2,700 citations and 210+
publications, his work bridges immersive technology design with rigorous
user-experience evaluation. He contributes to ITU-T standardization efforts and
collaborates internationally on XR research.

</div>

<div class="section-block section-block--light">

## Appointments & affiliation

<div class="affiliation-box">
  <div class="role">Professor of Computer Science (Immersive Media)</div>
  <div class="institution">Hamm-Lippstadt University of Applied Sciences (HSHL), Director of the Immersive Reality Lab</div>
  <div class="links">
    <a href="https://www.hshl.de/personen/prof-dr-ing-jan-niklas-voigt-antons">HSHL profile</a>
    <a href="https://immersive-reality-lab.de/pages/team_voigtantons.html">Immersive Reality Lab profile</a>
  </div>
</div>

</div>

<div class="section-block section-block--white">

## Evidence snapshot

<div class="metrics-grid">
  <div class="metric-card">
    <a href="https://scholar.google.de/citations?user=IFIaOZsAAAAJ">
      <span class="metric-number">2,700+</span>
      <span class="metric-label">Citations</span>
    </a>
  </div>
  <div class="metric-card">
    <a href="https://scholar.google.de/citations?user=IFIaOZsAAAAJ&hl=de">
      <span class="metric-number">210+</span>
      <span class="metric-label">Publications</span>
    </a>
  </div>
  <div class="metric-card">
    <a href="https://orcid.org/0000-0002-2786-9262">
      <span class="metric-number">ORCID</span>
      <span class="metric-label">Persistent researcher ID</span>
    </a>
  </div>
  <div class="metric-card">
    <a href="https://dblp.org/pid/39/10762">
      <span class="metric-number">DBLP</span>
      <span class="metric-label">Computer science bibliography</span>
    </a>
  </div>
</div>

</div>

<div class="section-block section-block--light">

## Research lines snapshot

{% for line in site.data.highlights.research_lines %}
<div class="research-card">
  <h3>{{ line.name }}</h3>
  <p>{{ line.claim }}</p>
  <div class="keywords">
    {% for keyword in line.keywords %}
    <span class="keyword-tag">{{ keyword }}</span>
    {% endfor %}
  </div>
  <a href="/research/#{{ line.id }}" class="btn btn--info btn--small">See outputs</a>
</div>
{% endfor %}

[Research](/research/){: .btn .btn--primary}
[Projects](/projects/){: .btn .btn--primary}
[Contact](/contact/){: .btn .btn--primary}

</div>

<div class="section-block section-block--white">

## Featured elsewhere

<div class="profile-links">
  <a href="https://www.hshl.de/personen/prof-dr-ing-jan-niklas-voigt-antons" class="profile-chip"><i class="fas fa-university" aria-hidden="true"></i> HSHL</a>
  <a href="https://scholar.google.de/citations?user=IFIaOZsAAAAJ" class="profile-chip"><i class="fas fa-graduation-cap" aria-hidden="true"></i> Google Scholar</a>
  <a href="https://orcid.org/0000-0002-2786-9262" class="profile-chip"><i class="fas fa-id-card" aria-hidden="true"></i> ORCID</a>
  <a href="https://dblp.org/pid/39/10762" class="profile-chip"><i class="fas fa-database" aria-hidden="true"></i> DBLP</a>
  <a href="https://dl.acm.org/profile/99659317387" class="profile-chip"><i class="fas fa-book" aria-hidden="true"></i> ACM DL</a>
  <a href="https://berlinup.books.tu-berlin.de/en/autor_innen/jan-niklas-voigt-antons/" class="profile-chip"><i class="fas fa-landmark" aria-hidden="true"></i> BerlinUP</a>
</div>

</div>
