from python_graphql_client import GraphqlClient
import feedparser
import httpx
import json
import pathlib
import re
import os
import datetime

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
    return [
        {
            "title": item["title"], 
            "url": item["link"].split("#")[0], 
            "published": formatGMTime(item["published"])
        }
        for item in entries
    ]

def fetch_blog():
    entries = feedparser.parse("http://blog.typoverflow.me/feed.xml")["entries"]
    entries = entries[1:]
    print(entries[0])
    res = []
    for item in entries:
        # try:
        res.append(
            {
                "title": item["title"], 
                "url": item["link"], 
                "bio": re.findall(r"(?:<blockquote>\n<p>)?(.*)<br>", item["content"][1]["value"])[0]
            }
        )
        # except:
        #     print("continue")
        #     continue
    print("-----------------------------")
    print(res)

    return res

if __name__ == "__main__":
    readme = root / "README.md"
    doubans = fetch_douban()[:5]
    blogs = fetch_blog()[:5]

    rewritten = readme.open().read()
    doubans_md = "\n".join(
        ["* <a href='{url}' target='_blank'>{title}</a> - {published}".format(**item) for item in doubans]
    )
    rewritten = replace_chunk(rewritten, "douban", doubans_md)

    blog_md = "\n".join(
        ["* <a href='{url}' target='_blank'>{title}</a>\n<font color=\"gray\" size=2>{bio}</font>".format(**item) for item in blogs]
    )
    rewritten = replace_chunk(rewritten, "blog", blog_md)

    readme.open("w").write(rewritten)
    
    print("-----------------------------")
    print(blogs)
    print("-----------------------------")