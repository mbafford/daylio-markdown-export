---
date: {{entry.timestamp.date()}}
time: {{entry.timestamp.strftime('%H:%M:%S')}}
daylio_mood: {{entry.mood.mood_name}}
tags:
    - daylio
{% for tag in entry.tags %}
    - {{tag.tag}}
{% endfor %}
---

{% if entry.note_title %} 
# {{entry.note_title}}

{% endif -%}

{# 
{% for tag in entry.tags -%}
{{tag.hashtag}}
{% endfor %}
#}

{%- if entry.note_text %}
    {{-entry.note_text}}
{% endif -%}

{% for asset in entry.assets %}
![[{{asset.file.filename}}|800]]
{% endfor %}