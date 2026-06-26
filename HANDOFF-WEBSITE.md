# 权限规则查询网站交接说明

本文用于把当前“用户与权限管理交接知识库 / 权限规则查询网站”任务交给另一台电脑的新 Codex 对话继续处理。内容基于当前 `auth-handover` 仓库和本对话真实进展，不重复粘贴完整规则正文。

## 1. 目标和当前阶段

网站目标是提供一个公开 GitHub Pages 静态查询入口，面向普通同事浏览和搜索“用户与权限管理”交接资料。不要求安装 Codex，不使用 AI，不需要登录。

当前阶段：

- 已有首页、快速查询、查询结果卡片、索引与逻辑概览、Codex 进阶查询入口和 Pixso 链接展示。
- 网站是零依赖静态站点，可直接打开 `index.html`，也可用本地静态服务预览。
- 当前分支是 `main`，最近相关提交包括：
  - `b818ea1 Create HANDOFF-SKILL.md`
  - `04c1b76 0626 - 终版`
  - `e489e85 0626完善规则`
  - `4d90996 0622优化`
  - `328577c feat: publish auth handover site`
- 当前未提交内容只有本轮新增的 `HANDOFF-WEBSITE.md`。

## 2. 已完成的页面、功能和交互

已完成页面和入口：

- `index.html`：网站首页。
- `codex-guide.html`：Codex 进阶查询使用手册页面。
- `docs/CODEX-USER-GUIDE.md`：手册 Markdown 源。

首页已完成的主要交互：

- 顶部展示网站名称、用途说明、设计稿维护说明入口、Codex 进阶版入口、主流程和已有规则统计。
- “快速查询”卡片作为主视觉入口，搜索框支持中文关键词查询。
- 输入框内使用自定义 `×` 清空图标；输入为空时隐藏。
- 快速查询结果独立展示在“索引与逻辑概览”上方，标题格式为 `查询结果 n条`。
- 快速查询结果是聚合搜索，不受下方概览 Tab 影响，会同时搜索：
  - 页面 / 设计稿索引；
  - 已确定规则；
  - 待确定事项。
- 规则类搜索结果在编号左侧显示 `已确定` 或 `待确定` 标签。
- 页面类结果标题前显示链接图标，标题整体可点击打开 Pixso；下方不再显示单独的“查看 Pixso”按钮，也不显示“当前状态”行。
- “索引与逻辑概览”默认收起，标题右侧使用箭头 icon 展开 / 收起。
- “索引与逻辑概览”始终展示全量资料，不随搜索框过滤。
- 概览一级 Tab：
  - `设计稿索引 7`
  - `规则概览 82`
- 概览二级 Tab：
  - `已确定 79`
  - `待确定 3`
- 移动端已检查过 390px 宽度，无明显横向溢出。

## 3. 数据来源、展示方式和关键决策

唯一规则源在私有仓库 `workskills`：

```text
../workskills/.agents/skills/skill-auth/references/逻辑规则.md
../workskills/.agents/skills/skill-auth/references/页面索引.md
```

公开仓库 `auth-handover` 只保存适合公开交接的网站数据和公开 Skill 数据，不复制 `workskills` 中其他 Skill、个人资料、历史对话、项目过程记录或 Git 历史。

当前 `data.js` 数据计数：

- 已确定规则：79 条，来自 `L-XXX` 和 `I-XXX`。
- 待确定事项：3 条，来自 `P-XXX`。
- 页面 / Pixso 索引：7 条，来自 `PAGE-XXX`。
- 设计稿维护说明：3 条。

关键展示决策：

- `data.js` 是自动生成文件，不建议手动编辑。
- 页面搜索和概览使用同一份 `data.js`，但行为不同：
  - 快速查询：按关键词过滤并聚合展示所有命中项。
  - 索引与逻辑概览：始终展示全量数据，只由 Tab 控制类别。
- 没有搜索结果时固定展示：

```text
现有交接资料中没有相关记录，无法根据已有规则判断。
```

- 待确定事项可以展示为 `待确定`，但不得包装成当前现行确定规则。
- 规则正文详细内容不在交接文件中重复粘贴，应查看 `data.js` 或公开 Skill references。

## 4. 主要目录、文件及用途

网站相关文件：

- `index.html`：首页结构、快速查询、概览区和脚本引用。
- `styles.css`：首页和手册页样式、响应式布局、卡片、Tab、搜索框和折叠按钮样式。
- `app.js`：首页搜索、评分、聚合结果、概览 Tab、折叠状态和结果渲染逻辑。
- `data.js`：网站静态数据，由 `scripts/sync_data.py` 生成。
- `codex-guide.html`：Codex 进阶查询使用手册页面。
- `guide.js`：手册 Markdown 渲染脚本。
- `docs/CODEX-USER-GUIDE.md`：手册正文。
- `scripts/sync_data.py`：从私有 `workskills` references 单向同步生成公开数据。

公开 Skill 相关文件：

- `.agents/skills/skill-auth/SKILL.md`
- `.agents/skills/skill-auth/references/逻辑规则.md`
- `.agents/skills/skill-auth/references/页面索引.md`

交接文件：

- `HANDOFF-SKILL.md`：公开 Skill 维护交接。
- `HANDOFF-WEBSITE.md`：当前网站维护交接。

## 5. 本地启动、构建和验证方式

本项目没有构建步骤、npm 依赖、后端或数据库。

本地预览方式：

```bash
python3 -m http.server 8000
```

然后访问：

```text
http://localhost:8000/
```

也可以直接用浏览器打开 `index.html`，但用本地服务更接近 GitHub Pages 路径行为。

基础验证命令：

```bash
node --check app.js
```

数据同步命令：

```bash
python3 scripts/sync_data.py \
  --source ../workskills/.agents/skills/skill-auth/references
```

同步后必须审核 Git diff，确认 `data.js` 和公开 Skill references 没有引入不应公开的内容。

## 6. 尚未完成、待确认或可继续优化的问题

当前明确未完成 / 需下一轮确认的事项：

- `HANDOFF-WEBSITE.md` 本身是本轮新增文件，也尚未提交。
- 未在本轮重新跑完整桌面和移动端截图视觉回归，只做了浏览器 DOM 行为检查和语法检查。
- 若后续继续优化视觉，需要注意“快速查询结果”和“索引与逻辑概览”必须保持解耦：
  - 查询结果随输入变化；
  - 概览始终全量。
- 若继续改搜索排序，需要同时验证页面、已确定规则、待确定事项三类聚合结果。
- 若私有规则源更新，不要手改 `data.js`，应先改 `workskills` 并运行同步脚本。

## 7. 已执行的测试和当前验证结果

本对话中已执行过的验证包括：

- `node --check app.js`：通过。
- 浏览器访问 `http://localhost:8000/`：页面可加载。
- 快速查询行为：
  - 搜索 `用户组` 时可显示聚合结果。
  - 搜索 `002` 时上方查询结果不随下方概览 Tab 切换变化。
  - 搜索 `岗位` 时快速查询显示 `查询结果 1条`，概览仍保持全量计数。
- 概览行为：
  - 默认收起。
  - 展开后 `设计稿索引` 显示 7 条。
  - 切换 `规则概览` 后已确定显示 79 条。
  - 切换 `待确定` 后显示 3 条。
  - 概览 Tab 数字保持全量：`设计稿索引 7`、`规则概览 82`、`已确定 79`、`待确定 3`。
- 输入框行为：
  - 只保留自定义 `×` 清空按钮。
  - 输入为空时清空按钮隐藏。
- 浏览器控制台：最近一次检查未发现页面 JavaScript error。

注意：上述结果是本对话中的验证结果；接手后仍应重新运行 `git status`、`node --check app.js` 和浏览器检查。

## 8. 下一台电脑的新 Codex 对话应先读取哪些文件

建议按顺序读取：

1. `HANDOFF-WEBSITE.md`
2. `git status --short --branch`
3. `README.md`
4. `index.html`
5. `app.js`
6. `styles.css`
7. `data.js`
8. `scripts/sync_data.py`
9. `HANDOFF-SKILL.md`

如果任务涉及公开 Skill 或规则同步，再读取：

```text
.agents/skills/skill-auth/SKILL.md
.agents/skills/skill-auth/references/逻辑规则.md
.agents/skills/skill-auth/references/页面索引.md
```

如果任务涉及修改规则源，再读取私有源：

```text
../workskills/.agents/skills/skill-auth/references/逻辑规则.md
../workskills/.agents/skills/skill-auth/references/页面索引.md
```

## 9. 与 HANDOFF-SKILL、公开 Skill 和 workskills 的边界

`HANDOFF-WEBSITE.md` 只记录网站查询体验、前端交互、页面结构和网站验证状态。

`HANDOFF-SKILL.md` 记录公开 Skill Auth 的维护边界，包括：

- `.agents/skills/skill-auth/SKILL.md`
- 公开 Skill references；
- Codex 进阶查询回答格式；
- 与私有 `workskills` 规则源的同步关系。

边界原则：

- 网站 UI 修改优先只动 `index.html`、`app.js`、`styles.css`。
- 规则内容修改必须以 `workskills` 为源，不在公开仓库中人工维护两套规则。
- `scripts/sync_data.py` 是同步边界，改它会同时影响网站数据和公开 Skill references，需谨慎。
- 不要把私有 `workskills` 中的其他目录、其他 Skill、个人资料或历史过程内容复制到公开仓库。
- 不要把 `P-XXX` 待确定事项写成现行确定规则。
