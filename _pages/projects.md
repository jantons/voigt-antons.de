---
layout: archive
title: "Projects & Transfer"
permalink: /projects/
author_profile: true
description: "Funded projects, roles, and transfer outcomes in XR, digital twins, QoE, and digital health."
---

## Funding table

| Project | Period | Funding program / funder | Role | Partners | Outputs |
|---|---|---|---|---|---|
{% for project in site.data.projects %}| [{{ project.name }}](#{{ project.id }}) | {{ project.period }} | {{ project.funding_program }} ({{ project.funder }}) | {{ project.role }} | {{ project.partners | join: ", " }} | {% for output in project.outputs %}[{{ output.label }}]({{ output.url }}){% unless forloop.last %}; {% endunless %}{% endfor %} |
{% endfor %}

## Project details

{% for project in site.data.projects %}
### {{ project.name }} {#{{ project.id }}}

- **Period:** {{ project.period }}
- **Role:** {{ project.role }}
- **Funding:** {{ project.funding_program }} / {{ project.funder }}
- **Topics:** {{ project.topics | join: ", " }}

**Evidence links**
{% for link in project.evidence_links %}
- [{{ link.label }}]({{ link.url }})
{% endfor %}

{% endfor %}

## Transfer & industry

{% assign partner_sum = 0 %}{% for project in site.data.projects %}{% assign partner_sum = partner_sum | plus: project.transfer_partners_estimate %}{% endfor %}
- Current portfolio includes **~{{ partner_sum }} partner engagements across public and industry contexts**.
- Typical transfer formats: prototype demonstrators, stakeholder workshops, pilot deployments, and training-focused modules.
- Current transfer focus areas: XR prototyping, digital twins, user-experience evaluation, and applied teaching innovation.
