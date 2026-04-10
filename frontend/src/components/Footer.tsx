export default function Footer() {
  return (
    <footer className="border-t py-4 mt-8">
      <div className="container mx-auto max-w-screen-xl flex flex-col gap-1 items-center justify-between px-4 sm:flex-row">
        <p className="text-sm text-muted-foreground">
          Harnetics · 商业航天文档对齐平台 · MVP Prototype v3
        </p>
        <p className="text-xs text-muted-foreground">
          设计约束：一切颜色与组件来自 shadcn/ui + amethyst-haze 设计系统
        </p>
      </div>
    </footer>
  )
}

