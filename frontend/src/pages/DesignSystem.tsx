import { CheckCircle, AlertTriangle, XCircle, Info } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Separator } from '@/components/ui/separator'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-4">
      <div className="flex items-center gap-3">
        <h2 className="text-lg font-semibold">{title}</h2>
        <Separator className="flex-1" />
      </div>
      {children}
    </section>
  )
}

export default function DesignSystem() {
  return (
    <div className="container mx-auto max-w-screen-xl px-4 py-10 space-y-12">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">设计系统</h1>
        <p className="mt-2 text-muted-foreground">
          Harnetics · amethyst-haze 主题 · shadcn/ui + Tailwind v4
        </p>
      </div>

      {/* Typography */}
      <Section title="Typography">
        <div className="space-y-2">
          <p className="text-4xl font-bold">H1 系统文档对齐平台</p>
          <p className="text-2xl font-semibold">H2 文档库与草稿管理</p>
          <p className="text-xl font-medium">H3 变更影响分析</p>
          <p className="text-base">Body 正文：TQ-12 发动机接口参数版本对齐核查</p>
          <p className="text-sm text-muted-foreground">Small muted：最近更新时间 2026-04-06</p>
          <p className="text-xs text-muted-foreground">XS muted：version tag · doc_id</p>
          <code className="text-sm font-mono bg-muted px-2 py-0.5 rounded">DOC-ICD-001 v2.3</code>
        </div>
      </Section>

      {/* Colors */}
      <Section title="Color Palette">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6">
          {[
            { name: 'primary', bg: 'bg-primary', text: 'text-primary-foreground' },
            { name: 'secondary', bg: 'bg-secondary', text: 'text-secondary-foreground' },
            { name: 'muted', bg: 'bg-muted', text: 'text-muted-foreground' },
            { name: 'accent', bg: 'bg-accent', text: 'text-accent-foreground' },
            { name: 'destructive', bg: 'bg-destructive', text: 'text-destructive-foreground' },
            { name: 'card', bg: 'bg-card border', text: 'text-card-foreground' },
          ].map(({ name, bg, text }) => (
            <div key={name} className={`${bg} ${text} rounded-lg p-4 text-sm font-medium text-center shadow-sm`}>
              {name}
            </div>
          ))}
        </div>
      </Section>

      {/* Buttons */}
      <Section title="Buttons">
        <div className="space-y-3">
          <div className="flex flex-wrap gap-3 items-center">
            <Button>Default</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="link">Link</Button>
          </div>
          <div className="flex flex-wrap gap-3 items-center">
            <Button size="lg">Large</Button>
            <Button>Default</Button>
            <Button size="sm">Small</Button>
            <Button size="icon"><CheckCircle className="h-4 w-4" /></Button>
          </div>
          <div className="flex flex-wrap gap-3 items-center">
            <Button disabled>Disabled</Button>
            <Button variant="outline" disabled>Disabled outline</Button>
          </div>
        </div>
      </Section>

      {/* Badges */}
      <Section title="Badges">
        <div className="flex flex-wrap gap-3">
          <Badge>default</Badge>
          <Badge variant="secondary">secondary</Badge>
          <Badge variant="outline">outline</Badge>
          <Badge variant="destructive">destructive</Badge>
          <Badge variant="warning">warning</Badge>
          <Badge variant="success">success</Badge>
        </div>
      </Section>

      {/* Alerts */}
      <Section title="Alerts">
        <div className="space-y-3 max-w-2xl">
          <Alert>
            <Info className="h-4 w-4" />
            <AlertTitle>信息提示</AlertTitle>
            <AlertDescription>草稿已自动保存，上次保存时间 14:32。</AlertDescription>
          </Alert>
          <Alert variant="warning">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>版本告警</AlertTitle>
            <AlertDescription>DOC-ICD-001 引用版本落后，当前最新为 v2.3。</AlertDescription>
          </Alert>
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertTitle>冲突阻断</AlertTitle>
            <AlertDescription>检测到上游来源冲突，请人工审核后再签发。</AlertDescription>
          </Alert>
          <Alert variant="success">
            <CheckCircle className="h-4 w-4" />
            <AlertTitle>评估通过</AlertTitle>
            <AlertDescription>所有引注均已追溯到源文档，ICD 参数一致。</AlertDescription>
          </Alert>
        </div>
      </Section>

      {/* Progress */}
      <Section title="Progress">
        <div className="space-y-3 max-w-md">
          {[{ v: 100, label: 'ICD 一致性' }, { v: 78, label: '引用最新版本率' }, { v: 42, label: '引注覆盖率' }].map(({ v, label }) => (
            <div key={label} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span>{label}</span>
                <span className={v >= 90 ? 'text-green-600' : v >= 70 ? 'text-amber-500' : 'text-destructive'}>{v}%</span>
              </div>
              <Progress value={v} />
            </div>
          ))}
        </div>
      </Section>

      {/* Form elements */}
      <Section title="Form Elements">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 max-w-2xl">
          <div className="space-y-1.5">
            <Label>文档标题</Label>
            <Input placeholder="例如：TQ-12 发动机测试大纲" />
          </div>
          <div className="space-y-1.5">
            <Label>文档类型</Label>
            <select className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring">
              <option>测试大纲</option>
              <option>需求文档</option>
              <option>设计文档</option>
            </select>
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label>草稿描述</Label>
            <Textarea rows={3} placeholder="请描述草稿内容与目标范围…" />
          </div>
        </div>
      </Section>

      {/* Table */}
      <Section title="Table">
        <div className="rounded-xl border overflow-hidden max-w-3xl">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead>文档编号</TableHead>
                <TableHead>标题</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>版本</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {[
                { id: 'DOC-ICD-001', title: '全局接口控制文档', status: 'Approved', v: 'v2.3' },
                { id: 'DOC-SYS-001', title: '动力系统总体需求规格说明', status: 'Approved', v: 'v3.1' },
                { id: 'DOC-TST-002', title: 'TQ-12 发动机地面试车测试大纲', status: 'UnderReview', v: 'v1.2' },
              ].map((row) => (
                <TableRow key={row.id} className="hover:bg-muted/30">
                  <TableCell><code className="text-xs bg-muted px-1.5 rounded font-mono">{row.id}</code></TableCell>
                  <TableCell className="font-medium text-sm">{row.title}</TableCell>
                  <TableCell>
                    <Badge variant={row.status === 'Approved' ? 'success' : 'warning'}>
                      {row.status === 'Approved' ? '已审批' : '审核中'}
                    </Badge>
                  </TableCell>
                  <TableCell><code className="text-xs text-muted-foreground">{row.v}</code></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </Section>

      {/* Tabs */}
      <Section title="Tabs">
        <div className="max-w-lg">
          <Tabs defaultValue="a">
            <TabsList>
              <TabsTrigger value="a">概览</TabsTrigger>
              <TabsTrigger value="b">详情</TabsTrigger>
              <TabsTrigger value="c">历史</TabsTrigger>
            </TabsList>
            <TabsContent value="a">
              <Card>
                <CardContent className="pt-4">
                  <p className="text-sm text-muted-foreground">此处显示文档整体概览信息。</p>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="b">
              <Card>
                <CardContent className="pt-4">
                  <p className="text-sm text-muted-foreground">此处显示详细章节与参数列表。</p>
                </CardContent>
              </Card>
            </TabsContent>
            <TabsContent value="c">
              <Card>
                <CardContent className="pt-4">
                  <p className="text-sm text-muted-foreground">此处显示版本历史记录。</p>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </Section>

      {/* Cards */}
      <Section title="Cards">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>基础卡片</CardTitle>
              <CardDescription>用于展示独立信息单元</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">内容区域最小间距 p-6。</p>
            </CardContent>
          </Card>
          <Card className="border-primary/40">
            <CardHeader>
              <CardTitle className="text-primary">强调卡片</CardTitle>
              <CardDescription>带主题色边框的卡片变体</CardDescription>
            </CardHeader>
            <CardContent>
              <Badge variant="success">已对齐</Badge>
            </CardContent>
          </Card>
          <Card className="border-destructive/40">
            <CardHeader>
              <CardTitle className="text-destructive">警告卡片</CardTitle>
              <CardDescription>红色边框表示需要立即关注</CardDescription>
            </CardHeader>
            <CardContent>
              <Badge variant="destructive">需审核</Badge>
            </CardContent>
          </Card>
        </div>
      </Section>
    </div>
  )
}
