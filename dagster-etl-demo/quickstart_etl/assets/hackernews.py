import base64
import urllib.request
import zipfile
import csv
from io import BytesIO
from typing import List


import matplotlib.pyplot as plt
import pandas as pd
import requests
from dagster import AssetExecutionContext, MetadataValue, Output, asset
from wordcloud import STOPWORDS, WordCloud
from ..resources import data_generator


@asset(group_name="hackernews", compute_kind="HackerNews API")
def signups(hackernews_api: data_generator.DataGeneratorResource):
    """模拟 HackerNews 的新用户注册数据

    用于演示 Resource 的用法
    """
    signups = pd.DataFrame(hackernews_api.get_signups())

    return Output(
        value=signups,
        metadata={
            "Record Count": len(signups),
            "Preview": MetadataValue.md(signups.head().to_markdown()),
            "Earliest Signup": signups["registered_at"].min(),
            "Latest Signup": signups["registered_at"].max(),
        },
    )


@asset(group_name="hackernews", compute_kind="Local CSV")
def stopwords_zip() -> None:
    """从 Dagster 官方下载指定的 stopwords.zip 数据集
    
    用于演示不需要 I/O Manager 的资产
    """
    urllib.request.urlretrieve(
        "https://docs.dagster.io/assets/stopwords.zip",
        "data/stopwords.zip",
    )


@asset(group_name="hackernews", non_argument_deps={"stopwords_zip"}, compute_kind="Local CSV")
def stopwords_csv() -> None:
    """将下载下来的 zip 文件进行解压
    
    用于演示不需要将依赖载入内存，相当于直接操作文件系统（或数据库之类的）
    """
    with zipfile.ZipFile("data/stopwords.zip", "r") as zip_ref:
        zip_ref.extractall("data")

@asset(group_name="hackernews", compute_kind="HackerNews API")
def hackernews_topstory_ids() -> List[int]:
    """Get up to 500 top stories from the HackerNews topstories endpoint.

    API Docs: https://github.com/HackerNews/API#new-top-and-best-stories
    """
    newstories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    top_500_newstories = requests.get(newstories_url).json()
    return top_500_newstories


@asset(group_name="hackernews", compute_kind="HackerNews API", io_manager_key="database_io_manager")
def hackernews_topstories(
    context: AssetExecutionContext, hackernews_topstory_ids: List[int]
) -> pd.DataFrame:
    """Get items based on story ids from the HackerNews items endpoint. It may take 1-2 minutes to fetch all 500 items.

    API Docs: https://github.com/HackerNews/API#items
    """
    results = []
    for item_id in hackernews_topstory_ids:
        item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json").json()
        results.append(item)
        if len(results) % 20 == 0:
            context.log.info(f"Got {len(results)} items so far.")

    df = pd.DataFrame(results)

    # Dagster supports attaching arbitrary metadata to asset materializations. This metadata will be
    # shown in the run logs and also be displayed on the "Activity" tab of the "Asset Details" page in the UI.
    # This metadata would be useful for monitoring and maintaining the asset as you iterate.
    # Read more about in asset metadata in https://docs.dagster.io/concepts/assets/software-defined-assets#recording-materialization-metadata
    context.add_output_metadata(
        {
            "num_records": len(df),
            "preview": MetadataValue.md(df.head().to_markdown()),
        }
    )
    return df

# 用 non_argument_deps 把相关资产串起来
@asset(group_name="hackernews", compute_kind="Plot", non_argument_deps={"stopwords_csv"})
def hackernews_topstories_word_cloud(
    context: AssetExecutionContext, hackernews_topstories: pd.DataFrame
) -> bytes:
    """Exploratory analysis: Generate a word cloud from the current top 500 HackerNews top stories.
    Embed the plot into a Markdown metadata for quick view.

    Read more about how to create word clouds in http://amueller.github.io/word_cloud/.
    """
    #stopwords = set(STOPWORDS)
    #stopwords.update(["Ask", "Show", "HN"])
    with open("data/stopwords.csv", "r") as f:
        stopwords = {row[0] for row in csv.reader(f)}
    
    titles_text = " ".join([str(item) for item in hackernews_topstories["title"]])
    titles_cloud = WordCloud(stopwords=stopwords, background_color="white").generate(titles_text)

    # Generate the word cloud image
    plt.figure(figsize=(8, 8), facecolor=None)
    plt.imshow(titles_cloud, interpolation="bilinear")
    plt.axis("off")
    plt.tight_layout(pad=0)

    # Save the image to a buffer and embed the image into Markdown content for quick view
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    image_data = base64.b64encode(buffer.getvalue())
    md_content = f"![img](data:image/png;base64,{image_data.decode()})"

    # Attach the Markdown content as metadata to the asset
    # Read about more metadata types in https://docs.dagster.io/_apidocs/ops#metadata-types
    context.add_output_metadata({"plot": MetadataValue.md(md_content)})

    return image_data
