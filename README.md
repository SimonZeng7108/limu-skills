# 小红书总结 · 李沐 AMA

A static archive of [Li Mu’s Xiaohongshu AMA](https://www.xiaohongshu.com/explore/6a9f7b27000000000f039800?xsec_token=ABlD0QZda9uE7KqikfwwusafTHZlpkGIsUGMZD5FzImCE=&xsec_source=pc_search): every floor he replied to, grouped by topic, plus a skill card for each category.

**Live site:** [https://simonzeng7108.github.io/limu-skills/](https://simonzeng7108.github.io/limu-skills/)

[![Screenshot of the 小红书总结 archive](docs/preview.png)](https://simonzeng7108.github.io/limu-skills/)

The page keeps the Xiaohongshu comment layout. Only threads with an author reply are listed (97 floors). Other replies stay collapsed until you expand them. The right column is one Cursor skill per category, written from the same AMA answers.

## Local preview

```bash
python -m http.server 8765
```

Then open [http://127.0.0.1:8765/](http://127.0.0.1:8765/). After editing comments, categories, or skills, rebuild the data file:

```bash
python scripts/build_data.py
```
