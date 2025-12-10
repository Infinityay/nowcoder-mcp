# NowCoder MCP API 文档

本文档详细描述了 NowCoder MCP Server 提供的所有工具接口。

## 目录

- [1. search - 搜索牛客网内容](#1-search---搜索牛客网内容)
- [2. batch_search - 批量搜索](#2-batch_search---批量搜索)
- [3. get_feed_details - 获取 Feed 动态详情](#3-get_feed_details---获取-feed-动态详情)
- [4. get_discuss_details - 获取讨论帖详情](#4-get_discuss_details---获取讨论帖详情)
- [典型使用流程](#典型使用流程)
- [错误处理](#错误处理)

---

## 1. `search` - 搜索牛客网内容

根据关键词搜索牛客网中的内容，支持单页或多页查询。

### 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `query` | string | ✅ | - | 搜索关键词，如 `"Java后端"`、`"秋招经验"` |
| `max_pages` | int | ❌ | 1 | 最大获取页数。`1`=仅第一页；`0`或`-1`=获取全部页面 |

### 输出结果

```json
{
  "current": 1,
  "size": 20,
  "total": 1234,
  "total_page": 62,
  "records": [
    {
      "title": "字节跳动后端一面凉经",
      "rc_type": 201,
      "uuid": "abc123def456",
      "content_id": "",
      "created_at": 1702195200000,
      "edit_time": 1702195200000,
      "view_count": 5000,
      "like_count": 200,
      "comment_count": 50,
      "company": "字节跳动",
      "job_title": "后端开发"
    }
  ]
}
```

### 输出字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `current` | int | 当前页码 |
| `size` | int | 当页记录数量 |
| `total` | int | 总记录数 |
| `total_page` | int | 总页数 |
| `records` | array | 搜索结果列表 |

### records 字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `title` | string | 文章标题 |
| `rc_type` | int | 内容类型：`201`=Feed 动态，`207`=讨论帖 |
| `uuid` | string | Feed UUID（rc_type=201 时有值） |
| `content_id` | string | 内容 ID（rc_type=207 时有值） |
| `created_at` | int | 创建时间戳（毫秒） |
| `edit_time` | int | 修改时间戳（毫秒） |
| `view_count` | int | 浏览量 |
| `like_count` | int | 点赞数 |
| `comment_count` | int | 评论数 |
| `company` | string | 作者认证公司 |
| `job_title` | string | 作者认证岗位 |

### 使用示例

```python
# 搜索 Java 后端相关内容
search(query="Java后端")

# 搜索并获取前 5 页结果
search(query="秋招经验", max_pages=5)

# 搜索并获取全部结果
search(query="字节跳动", max_pages=0)
```

---

## 2. `batch_search` - 批量搜索

一次性搜索多个关键词并返回结果。

### 输入参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| `keywords` | array[string] | ✅ | - | 关键词列表，如 `["Java后端", "算法工程师"]` |
| `max_pages` | int | ❌ | 1 | 每个关键词最大获取页数 |

### 输出结果

```json
{
  "Java后端": {
    "current": 1,
    "size": 20,
    "total": 500,
    "total_page": 25,
    "records": [...]
  },
  "算法工程师": {
    "current": 1,
    "size": 20,
    "total": 300,
    "total_page": 15,
    "records": [...]
  }
}
```

### 输出字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `{keyword}` | SearchResult | 以关键词为 key，对应搜索结果为 value |

### 使用示例

```python
# 批量搜索多个公司
batch_search(keywords=["字节跳动", "阿里巴巴", "腾讯"])

# 批量搜索多个岗位，每个获取 3 页
batch_search(keywords=["后端开发", "前端开发", "算法工程师"], max_pages=3)
```

---

## 3. `get_feed_details` - 获取 Feed 动态详情

根据 UUID 获取 Feed 动态的完整内容。

> ⚠️ **注意**：仅适用于 `rc_type=201` 的内容。

### 输入参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| `uuid` | string | ✅ | 文章 UUID，从搜索结果中获取 |

### 输出结果

```json
{
  "title": "字节跳动后端一面凉经",
  "content": "面试内容...\n1. 自我介绍\n2. 项目经历\n...",
  "uuid": "abc123def456",
  "url": "https://www.nowcoder.com/feed/main/detail/abc123def456"
}
```

### 输出字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `title` | string | 文章标题 |
| `content` | string | 文章完整内容（纯文本） |
| `uuid` | string | 文章 UUID |
| `url` | string | 文章访问链接 |

### 使用示例

```python
# 获取 Feed 详情
get_feed_details(uuid="abc123def456")
```

---

## 4. `get_discuss_details` - 获取讨论帖详情

根据内容 ID 获取讨论帖的完整内容。

> ⚠️ **注意**：仅适用于 `rc_type=207` 的内容。

### 输入参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| `content_id` | string | ✅ | 内容 ID，从搜索结果中获取 |

### 输出结果

```json
{
  "title": "阿里巴巴算法岗面试经验分享",
  "content": "面试流程...\n一面：\n1. 算法题\n...",
  "content_id": "827689925817458688",
  "url": "https://www.nowcoder.com/discuss/827689925817458688"
}
```

### 输出字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| `title` | string | 帖子标题 |
| `content` | string | 帖子完整内容（纯文本，已去除 HTML 标签） |
| `content_id` | string | 内容 ID |
| `url` | string | 帖子访问链接 |

### 使用示例

```python
# 获取讨论帖详情
get_discuss_details(content_id="827689925817458688")
```

---

## 典型使用流程

```
1. 调用 search("Java后端") 获取搜索结果
                ↓
2. 从 records 中获取感兴趣的内容
                ↓
3. 检查 rc_type 字段：
   - rc_type=201 → 调用 get_feed_details(uuid)
   - rc_type=207 → 调用 get_discuss_details(content_id)
                ↓
4. 获取完整的文章/帖子内容
```

### 流程图

```
┌─────────────────────────────────────────────────────────────┐
│                      search(query)                          │
│                           │                                 │
│                           ▼                                 │
│                    SearchResult                             │
│                    ├── records[0]                           │
│                    │   ├── rc_type: 201                     │
│                    │   └── uuid: "xxx"                      │
│                    └── records[1]                           │
│                        ├── rc_type: 207                     │
│                        └── content_id: "yyy"                │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
    rc_type == 201                  rc_type == 207
            │                               │
            ▼                               ▼
┌─────────────────────┐         ┌─────────────────────┐
│ get_feed_details    │         │ get_discuss_details │
│ (uuid="xxx")        │         │ (content_id="yyy")  │
└─────────────────────┘         └─────────────────────┘
            │                               │
            ▼                               ▼
┌─────────────────────┐         ┌─────────────────────┐
│     FeedDetail      │         │    DiscussDetail    │
│ ├── title           │         │ ├── title           │
│ ├── content         │         │ ├── content         │
│ ├── uuid            │         │ ├── content_id      │
│ └── url             │         │ └── url             │
└─────────────────────┘         └─────────────────────┘
```

---

## 错误处理

### 常见错误

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `需要提供 uuid 参数` | 调用 `get_feed_details` 时未提供 uuid | 从搜索结果中获取 uuid |
| `需要提供 content_id 参数` | 调用 `get_discuss_details` 时未提供 content_id | 从搜索结果中获取 content_id |
| `内容不存在!` | uuid 或 content_id 错误，或使用了错误的工具 | 检查 rc_type，选择正确的工具 |
| `网络请求失败` | 网络连接问题或牛客网服务异常 | 检查网络连接，稍后重试 |
| `API 请求失败` | 牛客网 API 返回错误 | 检查关键词是否合法 |

### 错误示例

```python
# ❌ 错误：对 rc_type=207 的内容使用 get_feed_details
get_feed_details(uuid="...")  # 会返回 "内容不存在!"

# ✅ 正确：根据 rc_type 选择正确的工具
if record.rc_type == 201:
    get_feed_details(uuid=record.uuid)
elif record.rc_type == 207:
    get_discuss_details(content_id=record.content_id)
```
