"""牛客网搜索 MCP 服务器

使用 FastMCP 框架实现的 MCP 服务器，提供牛客网内容搜索功能。
"""

import re
import requests
from typing import Optional
from pydantic import BaseModel, Field
from fastmcp import FastMCP

# ==================== 创建 MCP 服务器 ====================

mcp = FastMCP(
    name="NowCoder搜索",
    instructions="这是一个牛客网搜索工具，可以根据关键词搜索牛客网上的内容（Feed动态、讨论帖等），并获取详情。牛客网有两种内容类型：Feed（rc_type=201）和讨论帖（rc_type=207）。",
)

# ==================== 数据模型 ====================


class SearchRecord(BaseModel):
    """搜索记录（搜索结果）"""

    title: str = Field(description="文章标题")
    rc_type: int = Field(
        description="内容类型：201=Feed（动态），207=讨论帖。获取详情时：201用uuid调用get_feed_details，207用content_id调用get_discuss_details"
    )
    uuid: str = Field(default="", description="文章UUID（rc_type=201时使用）")
    content_id: str = Field(default="", description="内容ID（rc_type=207时使用）")
    created_at: int = Field(default=0, description="创建时间戳（毫秒）")
    edit_time: int = Field(default=0, description="修改时间戳（毫秒）")
    view_count: int = Field(default=0, description="浏览量")
    like_count: int = Field(default=0, description="点赞数")
    comment_count: int = Field(default=0, description="评论数")
    company: str = Field(default="", description="认证公司名称")
    job_title: str = Field(default="", description="认证岗位名称")


class FeedDetail(BaseModel):
    """Feed详情（动态类型）"""

    title: str = Field(description="文章标题")
    content: str = Field(description="文章完整内容")
    uuid: str = Field(default="", description="文章UUID")
    url: str = Field(default="", description="文章访问链接")


class DiscussDetail(BaseModel):
    """讨论帖详情（rcType=207）"""

    title: str = Field(description="帖子标题")
    content: str = Field(description="帖子完整内容")
    content_id: str = Field(default="", description="内容ID")
    url: str = Field(default="", description="帖子访问链接")


class SearchResult(BaseModel):
    """搜索结果"""

    current: int = Field(description="当前页码")
    size: int = Field(description="当页文章数量")
    total: int = Field(description="文章总数")
    total_page: int = Field(description="总页数")
    records: list[SearchRecord] = Field(description="搜索结果列表")


# ==================== API 配置 ====================

NOWCODER_API_URL = "https://gw-c.nowcoder.com/api/sparta/pc/search"
NOWCODER_DETAIL_URL = "https://www.nowcoder.com/feed/main/detail"  # Feed详情页
NOWCODER_DISCUSS_API_URL = (
    "https://gw-c.nowcoder.com/api/sparta/detail/content-data/detail"  # 讨论帖详情API
)
NOWCODER_DISCUSS_URL = "https://www.nowcoder.com/discuss"  # 讨论帖详情页
REQUEST_TIMEOUT = 30  # 请求超时时间（秒）

# 标签选项（用户可选）：id -> 名称
TAG_OPTIONS = {
    818: "面经",
    861: "求职进度",
    823: "内推",
    856: "公司评价",
}

# 有效的标签 ID 列表（用于参数校验）
VALID_TAG_IDS = list(TAG_OPTIONS.keys())
# 有效的排序值列表（用于参数校验）
VALID_ORDER_VALUES = ["", "create"]


# ==================== 工具函数 ====================


def html_to_text(html: str) -> str:
    """将 HTML 内容转换为纯文本

    Args:
        html: HTML 格式的内容

    Returns:
        纯文本内容
    """
    if not html:
        return ""

    # 移除 script 和 style 标签及其内容
    html = re.sub(
        r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE
    )
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)

    # 将常见的块级标签转换为换行
    html = re.sub(r"</?(p|div|br|h[1-6]|li|tr)[^>]*>", "\n", html, flags=re.IGNORECASE)

    # 移除所有其他 HTML 标签
    html = re.sub(r"<[^>]+>", "", html)

    # 处理 HTML 实体
    html = html.replace("&nbsp;", " ")
    html = html.replace("&amp;", "&")
    html = html.replace("&lt;", "<")
    html = html.replace("&gt;", ">")
    html = html.replace("&quot;", '"')
    html = html.replace("&#39;", "'")
    html = html.replace("\xa0", " ")  # 非断行空格

    # 合并多个连续换行为最多两个
    html = re.sub(r"\n\s*\n", "\n\n", html)

    # 去除首尾空白
    return html.strip()


def search_nowcoder_api(
    query: str,
    page: int = 1,
    tag: Optional[int] = None,
    order: str = "",
) -> dict:
    """调用牛客网搜索 API

    Args:
        query: 搜索关键词
        page: 页码，从1开始
        tag: 标签筛选 ID，可选值：818(面经)、861(求职进度)、823(内推)、856(公司评价)，None表示不筛选
        order: 排序方式，可选值：""(默认排序)、"create"(按时间排序)

    Returns:
        API 响应数据
    """
    # 构建 tag 参数
    tag_list = []
    if tag and tag in TAG_OPTIONS:
        tag_list = [{"name": TAG_OPTIONS[tag], "id": tag, "count": None}]

    payload = {
        "type": "all",
        "query": query,
        "page": page,
        "tag": tag_list,
        "order": order,
        "gioParams": {
            "searchFrom_var": "顶部导航栏",
            "searchEnter_var": "主站",
        },
    }

    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    response = requests.post(
        NOWCODER_API_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT
    )
    response.raise_for_status()
    return response.json()


def parse_search_response(response_data: dict) -> SearchResult:
    """解析搜索响应数据

    Args:
        response_data: API 响应数据

    Returns:
        解析后的搜索结果
    """
    data = response_data.get("data", {})
    records_raw = data.get("records", [])

    records = []
    for record in records_raw:
        rc_type = record.get("rc_type", 0)
        record_data = record.get("data", {})
        user_brief = record_data.get("userBrief", {})
        frequency_data = record_data.get("frequencyData", {})

        # 提取认证信息（公司和岗位）
        identity_list = user_brief.get("identityList") or []
        company = ""
        job_title = ""
        if identity_list and len(identity_list) > 0:
            first_identity = identity_list[0]
            company = first_identity.get("companyName", "")
            job_title = first_identity.get("jobName", "")

        # 根据 rc_type 处理不同类型
        if rc_type == 201:
            # Feed类型（动态），使用 momentData
            moment_data = record_data.get("momentData", {})
            if not moment_data:
                continue
            records.append(
                SearchRecord(
                    title=moment_data.get("title", ""),
                    rc_type=rc_type,
                    uuid=moment_data.get("uuid", ""),
                    content_id="",
                    created_at=moment_data.get("createdAt", 0),
                    edit_time=moment_data.get("editTime", 0),
                    view_count=frequency_data.get("viewCnt", 0),
                    like_count=frequency_data.get("likeCnt", 0),
                    comment_count=frequency_data.get("commentCnt", 0),
                    company=company,
                    job_title=job_title,
                )
            )
        elif rc_type == 207:
            # 讨论帖类型，使用 contentData
            content_data = record_data.get("contentData", {})
            if not content_data:
                continue
            records.append(
                SearchRecord(
                    title=content_data.get("title", ""),
                    rc_type=rc_type,
                    uuid="",
                    content_id=str(content_data.get("id", "")),
                    created_at=content_data.get("createTime", 0),
                    edit_time=content_data.get("editTime", 0),
                    view_count=frequency_data.get("viewCnt", 0),
                    like_count=frequency_data.get("likeCnt", 0),
                    comment_count=frequency_data.get("commentCnt", 0),
                    company=company,
                    job_title=job_title,
                )
            )
        # 其他类型暂不处理

    return SearchResult(
        current=data.get("current", 1),
        size=data.get("size", 0),
        total=data.get("total", 0),
        total_page=data.get("totalPage", 0),
        records=records,
    )


def get_feed_detail_from_page(uuid: str) -> FeedDetail:
    """从网页获取Feed详情（动态类型，rcType != 207）

    Args:
        uuid: 文章UUID

    Returns:
        Feed详情
    """
    if not uuid:
        raise ValueError("需要提供 uuid 参数")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    url = f"{NOWCODER_DETAIL_URL}/{uuid}"

    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    html = response.text

    # 检查内容是否存在
    if "内容不存在!" in html:
        raise ValueError(
            f"内容不存在! 请检查输入的uuid是否正确。"
            f"注意：此工具仅适用于Feed类型（动态），如果是讨论帖类型（rcType=207），请使用 get_discuss_details 工具并提供 content_id 参数。"
        )

    # 提取 title
    title_match = re.search(r'"title":"([^"]+)"', html)
    title = title_match.group(1) if title_match else ""

    # 提取正文：优先解析 feed-content-text 标签中的 HTML，再回退到 JSON 片段
    content = ""

    # 直接从页面中的 feed-content-text 区块提取
    content_match = re.search(
        r'<div[^>]*class="[^"]*feed-content-text[^"]*"[^>]*>(.*?)</div>',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if content_match:
        content_html = content_match.group(1)
        content = html_to_text(content_html)

    # 若页面结构变化导致未命中，则回退到原有的 JSON 片段提取
    if not content:
        content_matches = re.findall(r'"content":"([^"]+)"', html)
        for match in content_matches:
            if len(match) > 100 and "..." not in match:
                content = match
                break
        if content:
            content = (
                content.replace("\\n", "\n")
                .replace("\\u002F", "/")
                .replace("\\t", "\t")
            )

    return FeedDetail(
        title=title,
        content=content,
        uuid=uuid,
        url=url,
    )


def get_discuss_detail_from_api(content_id: str) -> DiscussDetail:
    """从API获取讨论帖详情（rcType=207）

    Args:
        content_id: 内容ID

    Returns:
        讨论帖详情
    """
    if not content_id:
        raise ValueError("需要提供 content_id 参数")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    api_url = f"{NOWCODER_DISCUSS_API_URL}/{content_id}"
    page_url = f"{NOWCODER_DISCUSS_URL}/{content_id}"

    response = requests.get(api_url, headers=headers, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()

    # 检查API响应是否成功
    if not data.get("success"):
        raise ValueError(
            f"内容不存在或请求失败! 请检查输入的content_id是否正确。"
            f"注意：此工具仅适用于讨论帖类型（rcType=207），如果是Feed类型（动态），请使用 get_feed_details 工具并提供 uuid 参数。"
        )

    content_data = data.get("data", {})

    # 将HTML内容转换为纯文本
    rich_text = content_data.get("richText", "") or content_data.get("content", "")
    plain_content = html_to_text(rich_text)

    return DiscussDetail(
        title=content_data.get("title", ""),
        content=plain_content,
        content_id=content_id,
        url=page_url,
    )


# ==================== MCP 工具 ====================


@mcp.tool(
    description="牛客网搜索，根据关键词搜索牛客网中的内容（Feed动态、讨论帖等）。支持单页或多页查询、标签筛选和排序。示例：'Java后端'、'秋招'、'字节跳动'",
    annotations={"readOnlyHint": True},
)
def search(
    query: str = Field(
        description="搜索关键词，如：'Java后端'、'推荐算法'、'字节跳动'、'秋招经验'"
    ),
    max_pages: int = Field(
        default=1,
        description="最大获取页数。默认1只获取第1页；设置为0或-1表示获取全部页面；建议不超过10页以避免请求过多",
        ge=-1,
    ),
    tag: Optional[int] = Field(
        default=818,
        description="标签筛选ID。可选值：818(面经)、861(求职进度)、823(内推)、856(公司评价)。不填或null表示不筛选",
    ),
    order: str = Field(
        default="create",
        description="排序方式。可选值：''(空字符串,默认排序)、'create'(按时间排序)",
    ),
) -> SearchResult:
    """搜索牛客网内容

    根据关键词搜索牛客网中的内容，支持单页或多页查询、标签筛选和排序。

    Args:
        query: 搜索关键词
        max_pages: 最大获取页数，默认1，设为0或-1获取全部
        tag: 标签筛选ID，818=面经, 861=求职进度, 823=内推, 856=公司评价
        order: 排序方式，""=默认排序, "create"=按时间排序

    Returns:
        搜索结果，包含合并后的内容列表和分页信息
    """
    try:
        # 校验参数
        if tag is not None and tag not in VALID_TAG_IDS:
            raise ValueError(f"无效的标签ID，可选值：{VALID_TAG_IDS}（818=面经, 861=求职进度, 823=内推, 856=公司评价）")
        if order not in VALID_ORDER_VALUES:
            raise ValueError(f"无效的排序方式，可选值：{VALID_ORDER_VALUES}（''=默认排序, 'create'=按时间排序）")

        # 先获取第一页，获取总页数信息
        first_response = search_nowcoder_api(query, page=1, tag=tag, order=order)
        if not first_response.get("success"):
            raise ValueError(f"API 请求失败: {first_response.get('msg', '未知错误')}")

        first_result = parse_search_response(first_response)
        total_page = first_result.total_page

        # 确定需要获取的页数
        if max_pages <= 0:  # 0 或 -1 表示获取全部
            pages_to_fetch = total_page
        else:
            pages_to_fetch = min(max_pages, total_page)

        # 如果只需要第一页，直接返回
        if pages_to_fetch <= 1:
            return first_result

        # 收集所有记录
        all_records = list(first_result.records)
        seen_ids = set()  # 用于去重
        for record in all_records:
            if record.uuid:
                seen_ids.add(record.uuid)
            elif record.content_id:
                seen_ids.add(record.content_id)

        # 获取剩余页面
        for page in range(2, pages_to_fetch + 1):
            try:
                response_data = search_nowcoder_api(query, page=page, tag=tag, order=order)
                if response_data.get("success"):
                    page_result = parse_search_response(response_data)
                    # 去重并添加记录
                    for record in page_result.records:
                        record_id = record.uuid if record.uuid else record.content_id
                        if record_id and record_id not in seen_ids:
                            seen_ids.add(record_id)
                            all_records.append(record)
            except Exception:
                # 单页失败不影响其他页面
                continue

        # 返回合并后的结果
        return SearchResult(
            current=1,  # 合并后从第1页开始
            size=len(all_records),  # 实际获取的记录数
            total=first_result.total,  # 总记录数
            total_page=total_page,  # 总页数
            records=all_records,
        )

    except requests.RequestException as e:
        raise ValueError(f"网络请求失败: {str(e)}")
    except Exception as e:
        raise ValueError(f"搜索失败: {str(e)}")


@mcp.tool(
    description="批量搜索多个关键词，一次性搜索多个关键词并返回结果。支持标签筛选和排序。示例：['Java后端', '推荐算法', '字节跳动']",
    annotations={"readOnlyHint": True},
)
def batch_search(
    keywords: list[str] = Field(
        description="关键词列表，如 ['Java后端', '推荐算法', '字节跳动']"
    ),
    max_pages: int = Field(
        default=1,
        description="每个关键词最大获取页数。默认1只获取第1页；设置为0或-1表示获取全部页面",
        ge=-1,
    ),
    tag: Optional[int] = Field(
        default=None,
        description="标签筛选ID。可选值：818(面经)、861(求职进度)、823(内推)、856(公司评价)。不填或null表示不筛选",
    ),
    order: str = Field(
        default="",
        description="排序方式。可选值：''(空字符串,默认排序)、'create'(按时间排序)",
    ),
) -> dict[str, SearchResult]:
    """批量搜索

    同时搜索多个关键词，返回每个关键词的搜索结果。支持标签筛选和排序。

    Args:
        keywords: 关键词列表
        max_pages: 每个关键词最大获取页数
        tag: 标签筛选ID，818=面经, 861=求职进度, 823=内推, 856=公司评价
        order: 排序方式，""=默认排序, "create"=按时间排序

    Returns:
        字典，键为关键词，值为对应的搜索结果
    """
    results = {}

    # 校验参数
    if tag is not None and tag not in VALID_TAG_IDS:
        raise ValueError(f"无效的标签ID，可选值：{VALID_TAG_IDS}（818=面经, 861=求职进度, 823=内推, 856=公司评价）")
    if order not in VALID_ORDER_VALUES:
        raise ValueError(f"无效的排序方式，可选值：{VALID_ORDER_VALUES}（''=默认排序, 'create'=按时间排序）")

    for keyword in keywords:
        try:
            # 先获取第一页
            first_response = search_nowcoder_api(keyword, page=1, tag=tag, order=order)
            if not first_response.get("success"):
                results[keyword] = SearchResult(
                    current=1, size=0, total=0, total_page=0, records=[]
                )
                continue

            first_result = parse_search_response(first_response)
            total_page = first_result.total_page

            # 确定需要获取的页数
            if max_pages <= 0:
                pages_to_fetch = total_page
            else:
                pages_to_fetch = min(max_pages, total_page)

            # 如果只需要第一页
            if pages_to_fetch <= 1:
                results[keyword] = first_result
                continue

            # 收集所有记录
            all_records = list(first_result.records)
            seen_ids = set()
            for record in all_records:
                if record.uuid:
                    seen_ids.add(record.uuid)
                elif record.content_id:
                    seen_ids.add(record.content_id)

            # 获取剩余页面
            for page in range(2, pages_to_fetch + 1):
                try:
                    response_data = search_nowcoder_api(keyword, page=page, tag=tag, order=order)
                    if response_data.get("success"):
                        page_result = parse_search_response(response_data)
                        for record in page_result.records:
                            record_id = (
                                record.uuid if record.uuid else record.content_id
                            )
                            if record_id and record_id not in seen_ids:
                                seen_ids.add(record_id)
                                all_records.append(record)
                except Exception:
                    continue

            results[keyword] = SearchResult(
                current=1,
                size=len(all_records),
                total=first_result.total,
                total_page=total_page,
                records=all_records,
            )

        except Exception:
            results[keyword] = SearchResult(
                current=1, size=0, total=0, total_page=0, records=[]
            )

    return results


@mcp.tool(
    description="获取牛客网Feed详情（动态类型），根据文章UUID获取完整内容。示例uuid：'abc123def456'",
    annotations={"readOnlyHint": True},
)
def get_feed_details(
    uuid: str = Field(
        description="文章UUID，从搜索结果中获取",
    ),
) -> FeedDetail:
    """获取Feed详情

    根据文章UUID获取完整的内容。适用于动态类型（非讨论帖）。

    Args:
        uuid: 文章UUID

    Returns:
        Feed详情，包含标题、内容和uuid
    """
    try:
        if not uuid:
            raise ValueError("需要提供 uuid 参数")
        return get_feed_detail_from_page(uuid=uuid)
    except requests.RequestException as e:
        raise ValueError(f"网络请求失败: {str(e)}")
    except Exception as e:
        raise ValueError(f"获取详情失败: {str(e)}")


@mcp.tool(
    description="获取牛客网讨论帖详情（rcType=207），根据内容ID获取完整的帖子内容。示例content_id：'827689925817458688'",
    annotations={"readOnlyHint": True},
)
def get_discuss_details(
    content_id: str = Field(
        description="内容ID，从搜索结果中获取（讨论帖类型使用）",
    ),
) -> DiscussDetail:
    """获取讨论帖详情

    根据内容ID获取完整的讨论帖内容。适用于rcType=207的讨论帖类型。

    Args:
        content_id: 内容ID

    Returns:
        讨论帖详情，包含标题、内容等
    """
    try:
        if not content_id:
            raise ValueError("需要提供 content_id 参数")
        return get_discuss_detail_from_api(content_id=content_id)
    except requests.RequestException as e:
        raise ValueError(f"网络请求失败: {str(e)}")
    except Exception as e:
        raise ValueError(f"获取详情失败: {str(e)}")


# ==================== 入口 ====================


if __name__ == "__main__":
    # 默认使用 stdio 传输（用于 Claude Desktop 等客户端）
    # 也可以通过命令行参数切换为 HTTP 传输
    import sys

    if "--http" in sys.argv:
        # HTTP 模式：fastmcp run nowcoder_mcp.py:mcp --transport http --port 8000
        # 或者直接：python nowcoder_mcp.py --http
        mcp.run(transport="http", port=8359)
    else:
        # stdio 模式（默认，用于 Claude Desktop）
        mcp.run()
