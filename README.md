# 用户与权限管理交接知识库

这是一个用于离职交接的公开静态网站 MVP，面向普通同事查询“用户与权限管理”项目中已经确认的权限规则、流程页面和 Pixso 索引。

网站只做确定性搜索和浏览，不使用 AI、不需要登录、不依赖后端或数据库。

## 文件结构

```text
.
├── index.html   # 页面结构
├── styles.css   # 响应式样式
├── data.js      # 自动生成的公开数据
├── app.js       # 搜索、筛选和结果渲染
├── scripts/
│   └── sync_data.py # 从 workskills 同步公开数据
├── README.md    # 项目说明
└── .gitignore
```

## 本地预览

直接用浏览器打开 `index.html` 即可预览。

也可以在仓库目录中启动任意静态文件服务，但不是必需条件。

## 从 workskills 同步数据

`workskills` 是规则和页面索引的唯一源仓库。修改规则只在 `workskills` 中进行，`auth-handover` 只保存适合公开交接的网站数据。

运行同步脚本：

```bash
python3 scripts/sync_data.py \
  --source ../workskills/.agents/skills/skill-auth/references
```

脚本会读取 `逻辑规则.md` 和 `页面索引.md`，覆盖生成网站使用的 `data.js`。

注意事项：

1. `data.js` 是自动生成文件，不建议手动编辑。
2. 脚本只导入已确认的 RULE 和 PAGE，以及公开展示所需字段。
3. 标记为待确认、二次授权相关、历史废稿、内部维护说明和 Skill 回答约束的内容不会导入。
4. 对同时包含已确认结论和待确认说明的规则，脚本会保留已确认结论，并在终端报告中列出被排除片段。
5. 同步后必须审核 Git 差异，再提交到公开仓库。

## GitHub Pages 发布

1. 将本仓库推送到 GitHub。
2. 进入仓库的 `Settings`。
3. 打开 `Pages`。
4. 在 `Build and deployment` 中选择从分支发布。
5. 选择要发布的分支和根目录 `/`。
6. 保存后等待 GitHub Pages 生成访问地址。

## 数据范围

当前版本导入 28 条权限规则、7 个页面索引。

页面底部固定说明：本网站仅整理已确认的交接资料；未记录或待确认事项不作推断。
