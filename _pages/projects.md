---
layout: archive
title: "Projects & Transfer"
permalink: /projects/
author_profile: true
description: "Funded projects, roles, and transfer outcomes in XR, digital twins, QoE, and digital health."
---

## Funding at a glance

- **5 ongoing third-party funded projects** (public/EU/transfer contexts)
- **Roles:** PI, Co-PI, and work package lead depending on project setup
- **Focus:** XR, digital twins, user experience measurement, and transfer into education/industry

_Source basis: public HSHL profile and project communications._

## Projects

{% for project in site.data.projects %}
### {{ project.name }} {#{{ project.id }}}

- **Period:** {{ project.period }}
- **Funding source:** {{ project.funding }}
- **Role:** {{ project.role }}
- **Topics:** {{ project.topics | join: ", " }}

**Outcomes**
{% for outcome in project.outcomes %}
- {{ outcome }}
{% endfor %}

{% endfor %}
