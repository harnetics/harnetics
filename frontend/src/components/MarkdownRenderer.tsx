/**
 * [INPUT]: 依赖 react-markdown, remark-gfm
 * [OUTPUT]: 对外提供 MarkdownRenderer 组件
 * [POS]: components 的通用 Markdown 渲染器，被 DraftShow 消费
 * [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
 */

import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownRendererProps {
  content: string
  className?: string
}

export default function MarkdownRenderer({ content, className = '' }: MarkdownRendererProps) {
  if (!content || !content.trim()) {
    return <p className="text-sm text-muted-foreground italic py-8 text-center">暂无内容</p>
  }

  return (
    <div className={`prose prose-sm dark:prose-invert max-w-none prose-headings:mt-4 prose-headings:mb-2 prose-p:my-1.5 prose-li:my-0.5 prose-pre:bg-muted prose-pre:text-foreground prose-code:text-primary prose-code:before:content-none prose-code:after:content-none ${className}`}>
      <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
    </div>
  )
}
