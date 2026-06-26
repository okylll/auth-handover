# Skill Auth 交接维护说明

本文用于把当前“完善 Skill Auth 交接”任务交给另一台电脑上的新 Codex 对话继续处理。内容基于当前 `auth-handover` 仓库状态和本对话已经形成的交付边界，不重复粘贴完整规则正文。

## 1. 当前目标和阶段

当前目标是维护公开仓库 `auth-handover` 中的 Skill Auth 交接能力，让进阶同事可以克隆本仓库后在 Codex 中选择 `Skill Auth`，基于公开交接资料进行权限逻辑、交互规则、待确认事项和 Pixso 页面查询。

当前仓库位于 `main` 分支。开始本交接文件前检查到工作区是干净的，未发现待提交修改。最近与本任务相关的提交包括：

- `04c1b76 0626 - 终版`
- `e489e85 0626完善规则`
- `4d90996 0622优化`
- `8c2621d 完善分级交付`
- `328577c feat: publish auth handover site`

本文件是新的交接记录，不代表已经提交。

## 2. 已完成的 Skill 交接工作

- 已在公开仓库中建立公开版 Skill：`.agents/skills/skill-auth/SKILL.md`。
- 已建立公开 Skill references：
  - `.agents/skills/skill-auth/references/逻辑规则.md`
  - `.agents/skills/skill-auth/references/页面索引.md`
- `SKILL.md` 已适配新版编号体系：
  - `L-001` 至 `L-060`
  - `I-001` 至 `I-019`
  - `P-001` 至 `P-003`
  - `PAGE-XXX`
- Skill 回答边界已写入：
  - 已确认问题需要给出结论、必要说明和来源编号。
  - 可组合多条 `L / I` 已确认规则回答。
  - 命中 `P-XXX` 时必须标记“待确认，不作为当前现行规则。”
  - 没有资料时固定回答“现有交接资料中没有相关记录，无法根据已有规则判断。”
  - 不允许根据行业常识、旧稿、个人资料或未确认方案补充结论。
- `README.md` 已记录普通查询和 Codex 进阶查询入口，并说明 `data.js` 和公开 references 由同步脚本生成。

## 3. 已确认结构、规则来源和关键决策

私有规则源仍在相邻私有仓库：

```text
../workskills/.agents/skills/skill-auth/references/逻辑规则.md
../workskills/.agents/skills/skill-auth/references/页面索引.md
```

公开仓库只保存允许交接的同步结果，不保存其他 Skill、个人资料、历史对话或未确认方案之外的私人内容。

当前公开资料结构为：

- 60 条逻辑规则：`L-001` 至 `L-060`
- 19 条交互规则：`I-001` 至 `I-019`
- 3 条待确认事项：`P-001` 至 `P-003`
- 7 条页面索引：`PAGE-001` 至 `PAGE-007`

关键业务边界已经写入公开 Skill：

- 父用户组权限向下级传递。
- 父级权限属于共有配置。
- 子用户组不能取消父级共有权限。
- 子用户组和用户可以继续增加权限。
- 用户组不是权限上限。
- 对象能够看到的权限，即视为可以配置。
- 角色和用户组本身不支持限制，只支持授予和回收。
- 具体用户可以限制来自角色和用户组的权限。
- 限制压过所有权限来源，包括用户自定义授予。
- 重新授予已限制权限时需要确认。
- 重复授予和回收遵循最终操作优先。
- 点位采用单一组织和单一区域归属。

## 4. 当前主要文件及用途

- `.agents/skills/skill-auth/SKILL.md`：公开版 Skill Auth 的能力、资料范围、回答格式和边界。
- `.agents/skills/skill-auth/references/逻辑规则.md`：公开 Skill 使用的权限逻辑、交互规则和待确认事项。
- `.agents/skills/skill-auth/references/页面索引.md`：公开 Skill 使用的页面流程和 Pixso 索引。
- `scripts/sync_data.py`：从私有 `workskills` references 单向生成公开 `data.js` 和公开 Skill references。
- `data.js`：网站使用的静态数据，由脚本生成，不建议手动编辑。
- `app.js`：网站搜索、筛选和结果渲染逻辑。
- `index.html`、`styles.css`：网站首页结构和样式。
- `docs/CODEX-USER-GUIDE.md`：Codex 使用手册的 Markdown 内容源。
- `codex-guide.html`、`guide.js`：把 Markdown 手册渲染成只读 HTML 阅读页。
- `README.md`：仓库用途、快速开始、同步方式和数据范围说明。

## 5. 与 workskills 的关系和同步边界

`workskills/.agents/skills/skill-auth/` 是私有规则源。公开仓库只做单向同步，不反向修改私有仓库。

同步命令：

```bash
python3 scripts/sync_data.py \
  --source ../workskills/.agents/skills/skill-auth/references
```

同步脚本当前职责：

- 读取私有 `逻辑规则.md` 和 `页面索引.md`。
- 解析 `L / I / P / PAGE` 编号。
- 生成网站使用的 `data.js`。
- 覆盖生成公开 Skill references。
- 避免导入其他 Skill、私人资料、Codex 对话或本机绝对路径。

继续维护时，规则正文应优先在 `workskills` 中修改并确认，再同步到 `auth-handover`。除非用户明确要求，不要在公开 references 中手改业务规则。

## 6. 尚未完成、待确认或可继续优化的问题

- 当前仓库未提交本交接文件；另一台电脑接手前需要先看 `git status`。
- 若后续私有规则源再更新，需要重新运行同步脚本并检查 `L / I / P / PAGE` 数量。
- 网站展示和视觉细节可能仍由另一个“权限规则查询网站”对话继续维护，本文件只记录 Skill 交接相关边界。
- 若 Codex 本地 Skill 选择列表未出现 `Skill Auth`，应优先检查是否打开了仓库根目录，以及 `.agents/skills/skill-auth/SKILL.md` 是否存在。

## 7. 已完成的测试和验证

本轮创建交接文件前，已重新检查：

- `git status --short --branch`：仓库在 `main` 分支且开始时工作区干净。
- 最近相关提交：通过 `git log --oneline` 查看。
- 仓库主要目录结构：通过 `find` 和 `rg --files` 查看。
- `SKILL.md` 当前支持 `L / I / P / PAGE` 编号体系。
- `data.js` 当前包含 `L-001` 至 `L-060`、`I-001` 至 `I-019`、`P-001` 至 `P-003`、`PAGE-001` 至 `PAGE-007`。
- 公开 references 中未在本轮检查输出中发现 `P-004` 或旧 `RULE-XXX` 命中。

注意：本交接文件不重新同步数据、不重新修改网站，也不代表完成新的浏览器视觉验收。

## 8. 下一台电脑应先读取哪些文件

新 Codex 对话建议按顺序读取：

1. `HANDOFF-SKILL.md`
2. `README.md`
3. `.agents/skills/skill-auth/SKILL.md`
4. `.agents/skills/skill-auth/references/逻辑规则.md`
5. `.agents/skills/skill-auth/references/页面索引.md`
6. `scripts/sync_data.py`
7. `data.js`
8. `docs/CODEX-USER-GUIDE.md`

如果任务是继续同步最新私有源，再读取：

```text
../workskills/.agents/skills/skill-auth/references/逻辑规则.md
../workskills/.agents/skills/skill-auth/references/页面索引.md
```

然后运行同步脚本并检查 Git diff。

## 9. 本对话与网站对话的分工

属于本“完善 Skill Auth 交接”任务的内容：

- 公开 Skill 的结构、说明和回答边界。
- 公开 Skill references 的同步和数据范围。
- 与私有 `workskills` 规则源的单向同步关系。
- Codex 使用手册中与 Skill 调用有关的说明。
- 同步脚本对规则结构的解析和生成边界。

应交给“权限规则查询网站”对话处理的内容：

- 首页视觉排版、按钮、颜色、响应式细节。
- 搜索结果卡片样式和 Tab 文案展示。
- 手册页纯视觉阅读体验。
- 网站静态查询体验的进一步 UI 优化。

如果网站展示修改会影响 `data.js`、`app.js` 或同步脚本，应先确认是否同时属于 Skill 交接的数据边界，再继续修改。
