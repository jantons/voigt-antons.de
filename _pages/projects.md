---
layout: archive
title: "Projects & Transfer"
permalink: /projects/
author_profile: true
description: "Funded projects, roles, and transfer outcomes in XR, digital twins, QoE, and digital health."
---

<div class="section-block section-block--white" markdown="1">

## Funding table

| Project | Period | Funding program / funder | Role | Partners | Outputs |
|---|---|---|---|---|---|
{% for project in site.data.projects %}| [{{ project.name }}](#{{ project.id }}) | {{ project.period }} | {{ project.funding_program }} ({{ project.funder }}) | {{ project.role }} | {{ project.partners | join: ", " }} | {% for output in project.outputs %}[{{ output.label }}]({{ output.url }}){% unless forloop.last %}; {% endunless %}{% endfor %} |
{% endfor %}

</div>

<div class="section-block section-block--light">

<h2>Project details</h2>

{% for project in site.data.projects %}
<div class="research-card" id="{{ project.id }}">
  <h3>{{ project.name }}</h3>
  <p><strong>Period:</strong> {{ project.period }}</p>
  <p><strong>Role:</strong> {{ project.role }}</p>
  <p><strong>Funding:</strong> {{ project.funding_program }} / {{ project.funder }}</p>
  <p><strong>Topics:</strong> {{ project.topics | join: ", " }}</p>

  <p><strong>Evidence links</strong></p>
  <ul>
    {% for link in project.evidence_links %}
    <li><a href="{{ link.url }}">{{ link.label }}</a></li>
    {% endfor %}
  </ul>
</div>
{% endfor %}

</div>

<div class="section-block section-block--white" markdown="1">

## Transfer & industry

{% assign partner_sum = 0 %}{% for project in site.data.projects %}{% assign partner_sum = partner_sum | plus: project.transfer_partners_estimate %}{% endfor %}
- Current portfolio includes **~{{ partner_sum }} partner engagements across public and industry contexts**.
- Typical transfer formats: prototype demonstrators, stakeholder workshops, pilot deployments, and training-focused modules.
- Current transfer focus areas: XR prototyping, digital twins, user-experience evaluation, and applied teaching innovation.

</div>
