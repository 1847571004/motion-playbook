# 来源与许可

## 本仓库自己产出的东西

| 文件 | 作者 | 许可 |
|---|---|---|
| `SKILL.md` | 本仓库 | MIT |
| `structures.md` | 本仓库 | MIT |
| `CHEATSHEET.md` | 本仓库 | MIT |
| `templates/PROMPTS.md` | 本仓库 | MIT |
| `templates/render_anim.py` | 本仓库 | MIT |
| `templates/check_anim.py` | 本仓库 | MIT |
| `examples/example-12s.html` | 本仓库 | MIT |

MIT 全文见 [LICENSE](LICENSE)。

---

## 知识来源

本仓库的方法论，来自对下面这个开源合集 **341 份风格提示词的全量精读**
（含结构统计、禁令句提取、帧率分布、逐系列抽样精读），加上一支实际渲染的成片验证。

### 原始合集

- **仓库**：[XiaoyeCodes/code-animation-prompts](https://github.com/XiaoyeCodes/code-animation-prompts)
- **原始素材整理者**：哔哩哔哩 [**俯仰观照**](https://space.bilibili.com/3690990015613855/)
- **技能封装与仓库维护**：[XiaoyeCodes](https://github.com/XiaoyeCodes)

**⚠️ 原始素材（那 341 份提示词与配图）不在本仓库内。** 请去上面的原仓库获取。

### 原素材的分享约定（原文）

> 全部免费，不用私信，不用买课。
>
> 你可以免费用、免费转给别人；转的时候也请免费分享。
>
> 禁止把这些内容包装成课程、付费 skills 或任何收费的东西拿去卖。

**本仓库严格遵守该约定：完全免费，不用于任何付费产品、课程或付费 skill。**

### 合集内的第三方许可

原合集内混合了多个来源，各自保留原许可：

| 来源 | 许可 | 署名 |
|---|---|---|
| Lemo-Opuscar | MIT | Copyright (c) 2026 LemoLab |
| mg-styles-15 | MIT | Copyright (c) 2026 Vincentwei1021 |
| code-video | MIT | Copyright (c) 2026 Bae-ChangHyun |

本仓库**未复制**这些文件，仅引用其方法论层面的结论（如"混合帧率""受控的不完美"等通用原则），
这些结论属于思想而非表达，不受版权保护。如需原文，请去原仓库。

---

## 引用建议

如果你在文章/视频里用到本仓库的结论，建议这样注明：

```text
方法论来自「代码动效 Playbook」，
其知识来源为 XiaoyeCodes/code-animation-prompts（341 份动效提示词合集）。
```

---

## 免责

本仓库提供的参数与工作流，是在特定环境下实测有效的，不保证在所有工具链上一致。
渲染脚本依赖 Edge/Chrome + ffmpeg + `websocket-client`，路径为 Windows 默认值，
在其他系统上需自行修改 `EDGE` / `FFMPEG` 常量。
