export default function Hero() {
  return (
    <section className="container max-w-screen-2xl flex flex-col items-center gap-4 text-center py-24 px-4">
      <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl text-foreground">
        商业航天跨部门文档对齐系统
      </h1>
      <p className="text-xl text-muted-foreground max-w-2xl">
        Harnetics v3：以 ICD 为枢纽，构建跨越"任务-系统-分系统-单机"的文档追溯图谱，减少 80% 的跨部门对齐时间。
      </p>
      <div className="flex gap-4 mt-4">
        <button className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-8 py-2">
          开始对齐图谱
        </button>
        <button className="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-8 py-2">
          探索示例
        </button>
      </div>
    </section>
  );
}
