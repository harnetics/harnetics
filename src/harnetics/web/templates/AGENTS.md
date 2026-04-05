# templates/
> L2 | 父级: src/harnetics/web/AGENTS.md

成员清单
base.html: 全站基础布局，提供导航骨架和页面内容占位。
documents.html: 文档目录页，提供上传表单、筛选器和文档列表。
document_detail.html: 文档详情页，展示单篇文档元数据与 sections。
draft_new.html: 草稿创建页，先提交主题再选择候选来源并触发生成。
draft_show.html: 草稿工作台页，展示正文、告警、引注并支持轻编辑与导出。

法则: 母版只定义共享外壳，页面模板只表达状态，不内嵌业务判断。

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
