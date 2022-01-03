from python_graphql_client import GraphqlClient
import feedparser
import httpx
import json
import pathlib
import re
import os
import datetime
import time

root=pathlib.Path(__file__).parent.resolve()
client = GraphqlClient(endpoint="https://api.github.com/graphql")

TOKEN = os.environ.get("GH_TOKEN", "")

def replace_chunk(content, marker, chunk, inline=False):
    r = re.compile(
        r"<!\-\- {} starts \-\->.*<!\-\- {} ends \-\->".format(marker, marker), 
        re.DOTALL, 
    )
    if not inline:
        chunk = "\n{}\n".format(chunk)
    chunk = "<!-- {} starts -->{}<!-- {} ends -->".format(marker, chunk, marker)
    return r.sub(chunk, content)

def formatGMTime(timestamp):
    GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
    dateStr = datetime.datetime.strptime(timestamp, GMT_FORMAT) + datetime.timedelta(hours=8)
    return dateStr.date()

def fetch_douban():
    entries = feedparser.parse("https://www.douban.com/feed/people/FFsays/interests")["entries"]
    while entries=="" or len(entries) == 0:
        time.sleep(20)
        entries = feedparser.parse("https://www.douban.com/feed/people/FFsays/interests")["entries"]
    return [
        {
            "title": item["title"], 
            "url": item["link"].split("#")[0], 
            "published": formatGMTime(item["published"])
        }
        for item in entries
    ]

def fetch_blog():
    entries = feedparser.parse("http://blog.typoverflow.me/feed")["entries"]
    res = []
    for item in entries:
        try:
            if item["title"] == "南大印象" or item["title"] == "观影记录": 
                continue 
            res.append(
                {
                    "title": item["title"], 
                    "url": item["link"], 
                    "bio": re.findall(r"<p>(.*?)</p>", item["content"][0]["value"])[0]
                }
            )
        except Exception as e:
            print(e)
            print("continue")
            continue
    return res

if __name__ == "__main__":
    readme = root / "README.md"
    doubans = fetch_douban()[:5]
    blogs = fetch_blog()[:3]

    rewritten = readme.open().read()
    doubans_md = "\n".join(
        ["* <a href='{url}' target='_blank'>{title}</a> - {published}".format(**item) for item in doubans]
    )
    rewritten = replace_chunk(rewritten, "douban", doubans_md)

    blog_md = "\n".join(
        ["* <a href='{url}' target='_blank'>{title}</a><br><font color=\"gray\" size=2>{bio}</font>".format(**item) for item in blogs]
    )
    rewritten = replace_chunk(rewritten, "blog", blog_md)

    readme.open("w").write(rewritten)
    