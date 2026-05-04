// [INPUT]: 依赖 tauri、portpicker、ureq 与 harnetics-server sidecar
// [OUTPUT]: 提供 Harnetics 桌面壳 main 入口，启动/健康检查/日志转发/清理本地后端，并优先从可执行文件目录解析 sidecar
// [POS]: desktop/src-tauri 的进程编排核心，业务请求全部转交 Python FastAPI sidecar
// [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::{Duration, Instant};

use tauri::{AppHandle, Manager, State, WindowEvent};

struct BackendProcess(Mutex<Option<Child>>);

impl Drop for BackendProcess {
    fn drop(&mut self) {
        if let Ok(mut guard) = self.0.lock() {
            if let Some(mut child) = guard.take() {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    }
}

fn sidecar_name() -> &'static str {
    if cfg!(windows) {
        "harnetics-server.exe"
    } else {
        "harnetics-server"
    }
}

fn find_sidecar_in(dir: &Path, target_triple: &str) -> Option<PathBuf> {
    [
        dir.join(sidecar_name()),
        dir.join(format!("harnetics-server-{target_triple}")),
        dir.join(format!("harnetics-server-{target_triple}.exe")),
    ]
    .into_iter()
    .find(|path| path.exists())
}

fn sidecar_path(app: &AppHandle) -> Result<PathBuf, String> {
    let target_triple = option_env!("TAURI_ENV_TARGET_TRIPLE").unwrap_or("");
    if let Some(path) = std::env::current_exe()
        .ok()
        .and_then(|exe| exe.parent().map(Path::to_path_buf))
        .and_then(|dir| find_sidecar_in(&dir, target_triple))
    {
        return Ok(path);
    }

    let resource_dir = app.path().resource_dir().ok();
    if let Some(path) = resource_dir
        .as_deref()
        .and_then(|dir| find_sidecar_in(dir, target_triple))
    {
        return Ok(path);
    }

    let searched = resource_dir
        .map(|path| path.display().to_string())
        .unwrap_or_else(|| "resource directory unavailable".to_string());
    Err(format!("cannot find backend sidecar; searched executable directory and {searched}"))
}

fn wait_for_health(port: u16) -> Result<(), String> {
    let url = format!("http://127.0.0.1:{port}/health");
    let deadline = Instant::now() + Duration::from_secs(60);
    while Instant::now() < deadline {
        if let Ok(response) = ureq::get(&url).timeout(Duration::from_secs(2)).call() {
            if response.status() == 200 {
                return Ok(());
            }
        }
        thread::sleep(Duration::from_millis(300));
    }
    Err(format!("backend did not become healthy at {url}"))
}

fn start_backend(app: &AppHandle, state: State<BackendProcess>) -> Result<u16, String> {
    let port = portpicker::pick_unused_port().ok_or("cannot find an available localhost port")?;
    let data_dir = app
        .path()
        .app_data_dir()
        .map_err(|error| format!("cannot resolve app data directory: {error}"))?;
    let var_dir = data_dir.join("var");
    let logs_dir = data_dir.join("logs");
    std::fs::create_dir_all(var_dir.join("uploads")).map_err(|error| error.to_string())?;
    std::fs::create_dir_all(var_dir.join("exports")).map_err(|error| error.to_string())?;
    std::fs::create_dir_all(var_dir.join("chroma")).map_err(|error| error.to_string())?;
    std::fs::create_dir_all(&logs_dir).map_err(|error| error.to_string())?;
    let sidecar_log = logs_dir.join("sidecar-bootstrap.log");
    let stdout = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&sidecar_log)
        .map_err(|error| error.to_string())?;
    let stderr = stdout.try_clone().map_err(|error| error.to_string())?;
    std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(data_dir.join(".env"))
        .map_err(|error| error.to_string())?;

    let mut child = Command::new(sidecar_path(app)?)
        .arg("serve")
        .arg("--host")
        .arg("127.0.0.1")
        .arg("--port")
        .arg(port.to_string())
        .arg("--db")
        .arg(var_dir.join("harnetics-graph.db"))
        .arg("--no-browser")
        .env("HARNETICS_ENV_FILE", data_dir.join(".env"))
        .env("HARNETICS_GRAPH_DB_PATH", var_dir.join("harnetics-graph.db"))
        .env("HARNETICS_CHROMA_DIR", var_dir.join("chroma"))
        .env("HARNETICS_RAW_UPLOAD_DIR", var_dir.join("uploads"))
        .env("HARNETICS_EXPORT_DIR", var_dir.join("exports"))
        .env("HARNETICS_LOG_DIR", logs_dir)
        .env("HARNETICS_SERVER_PORT", port.to_string())
        .stdout(Stdio::from(stdout))
        .stderr(Stdio::from(stderr))
        .spawn()
        .map_err(|error| format!("failed to start backend sidecar: {error}"))?;

    if let Err(error) = wait_for_health(port) {
        let _ = child.kill();
        return Err(error);
    }

    *state.0.lock().map_err(|_| "backend lock poisoned")? = Some(child);
    Ok(port)
}

fn stop_backend(state: State<BackendProcess>) {
    if let Ok(mut guard) = state.0.lock() {
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(BackendProcess(Mutex::new(None)))
        .setup(|app| {
            let handle = app.handle().clone();
            let state = app.state::<BackendProcess>();
            let port = start_backend(&handle, state)?;
            if let Some(window) = app.get_webview_window("main") {
                let url: url::Url = format!("http://127.0.0.1:{port}")
                    .parse()
                    .map_err(|error: url::ParseError| error.to_string())?;
                window
                    .navigate(url)
                    .map_err(|error| error.to_string())?;
                window.show().map_err(|error| error.to_string())?;
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, WindowEvent::CloseRequested { .. }) {
                stop_backend(window.state::<BackendProcess>());
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running Harnetics desktop shell");
}

fn main() {
    run();
}

#[cfg(test)]
mod tests {
    use super::find_sidecar_in;

    #[test]
    fn finds_unsuffixed_sidecar_next_to_executable() {
        let dir = tempfile::tempdir().expect("temp dir");
        let sidecar = dir.path().join(super::sidecar_name());
        std::fs::write(&sidecar, b"").expect("sidecar");

        assert_eq!(find_sidecar_in(dir.path(), "aarch64-apple-darwin"), Some(sidecar));
    }

    #[test]
    fn finds_target_suffixed_sidecar_when_unsuffixed_is_missing() {
        let dir = tempfile::tempdir().expect("temp dir");
        let sidecar = dir.path().join("harnetics-server-aarch64-apple-darwin");
        std::fs::write(&sidecar, b"").expect("sidecar");

        assert_eq!(find_sidecar_in(dir.path(), "aarch64-apple-darwin"), Some(sidecar));
    }
}
