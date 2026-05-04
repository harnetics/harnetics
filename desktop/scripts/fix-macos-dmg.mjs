// [INPUT]: 依赖 macOS hdiutil、SetFile、chflags 与 Tauri 生成的 bundle/dmg 产物
// [OUTPUT]: 提供 macOS DMG 后处理脚本，隐藏 .VolumeIcon.icns 并重新压缩安装镜像
// [POS]: desktop/scripts 的打包修正工具，被 desktop/package.json 的 build 脚本串联调用
// [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, join } from "node:path";
import { execFileSync } from "node:child_process";

const root = new URL("..", import.meta.url).pathname;
const targetDir = join(root, "src-tauri", "target");

function run(command, args) {
  return execFileSync(command, args, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
}

function dmgFiles() {
  if (!existsSync(targetDir)) {
    return [];
  }

  const output = run("find", [targetDir, "-path", "*/release/bundle/dmg/*.dmg", "-type", "f", "-print"]);
  return output.split("\n").filter(Boolean);
}

function mountPoint(output) {
  const line = output
    .split("\n")
    .reverse()
    .find((item) => item.includes("/Volumes/"));

  return line?.match(/\/Volumes\/.+$/)?.[0]?.trim() ?? null;
}

function postprocess(dmg) {
  const tempDir = mkdtempSync(join(tmpdir(), "harnetics-dmg-"));
  const writableDmg = join(tempDir, basename(dmg));
  const source = join(tempDir, "source.dmg");
  let mount = null;

  try {
    run("hdiutil", ["convert", dmg, "-format", "UDRW", "-o", source]);
    const attachOutput = run("hdiutil", ["attach", "-nobrowse", "-readwrite", source]);
    mount = mountPoint(attachOutput);
    if (!mount) {
      throw new Error("cannot resolve mounted DMG path");
    }

    const volumeIcon = join(mount, ".VolumeIcon.icns");
    if (existsSync(volumeIcon)) {
      run("SetFile", ["-a", "V", "-c", "icnC", volumeIcon]);
      run("chflags", ["hidden", volumeIcon]);
    }

    run("hdiutil", ["detach", mount]);
    mount = null;
    run("hdiutil", ["convert", source, "-format", "UDZO", "-o", writableDmg]);
    run("mv", [writableDmg, dmg]);
    console.log(`Fixed macOS DMG volume icon visibility: ${dmg}`);
  } finally {
    if (mount) {
      try {
        run("hdiutil", ["detach", mount]);
      } catch {
        run("hdiutil", ["detach", "-force", mount]);
      }
    }
    rmSync(tempDir, { recursive: true, force: true });
  }
}

if (process.platform !== "darwin") {
  process.exit(0);
}

for (const dmg of dmgFiles()) {
  postprocess(dmg);
}
