---
layout: page
title: お問い合わせ
permalink: /contact/
---

当サイトへのお問い合わせは、以下のフォームからお願いいたします。

{% if site.contact_form_url != "" -%}
<p><a class="btn" href="{{ site.contact_form_url }}" target="_blank" rel="noopener">お問い合わせフォームを開く</a></p>
{%- else -%}
<p>お問い合わせフォームは現在準備中です。</p>
{%- endif %}

いただいた情報の取り扱いについては、[プライバシーポリシー]({{ '/privacy/' | relative_url }})をご覧ください。
