#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用 CDP 打开本地 HTML 动画，截取指定时间点的帧，检查画面是否正确。

用法：
  python check_anim.py --html "E:\\...\\片头.html" --times 1.8,4.0,9.0,11.5 --out-dir shots
"""
from __future__ import annotations
import argparse, base64, json, os, subprocess, sys, time, urllib.request

CDP_PORT = 9334
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"


def http_json(path):
    with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}{path}", timeout=10) as r:
        return json.loads(r.read().decode())


def alive():
    try:
        http_json("/json/version")
        return True
    except Exception:
        return False


class Tab:
    def __init__(self):
        import websocket
        pages = [t for t in http_json("/json/list") if t.get("type") == "page"]
        self.ws = websocket.create_connection(pages[0]["webSocketDebuggerUrl"], timeout=60)
        self._id = 0

    def call(self, method, params=None, timeout=60):
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            m = json.loads(self.ws.recv())
            if m.get("id") == mid:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result", {})
        raise TimeoutError(method)

    def js(self, expr, timeout=60):
        r = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True,
                                           "awaitPromise": True}, timeout=timeout)
        res = r.get("result", {})
        if res.get("subtype") == "error":
            raise RuntimeError(res.get("description", "JS error"))
        return res.get("value")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--times", default="1.8,4.0,9.0,11.5")
    ap.add_argument("--out-dir", default="shots")
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    args = ap.parse_args()

    path = os.path.abspath(args.html)
    if not os.path.exists(path):
        print(f"HTML 不存在: {path}", file=sys.stderr)
        return 1
    os.makedirs(args.out_dir, exist_ok=True)

    started = False
    if not alive():
        print("启动浏览器…", file=sys.stderr)
        subprocess.Popen(
            [EDGE, f"--remote-debugging-port={CDP_PORT}",
             f"--user-data-dir={os.path.join(os.environ.get('TEMP', '.'), 'anim-check')}",
             "--no-first-run", "--no-default-browser-check",
             f"--window-size={args.width},{args.height}",
             "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        started = True
        for _ in range(40):
            if alive():
                break
            time.sleep(0.5)

    tab = Tab()
    try:
        tab.call("Page.enable")
        tab.call("Runtime.enable")
        url = "file:///" + path.replace("\\", "/") + "?export=1"
        tab.call("Page.navigate", {"url": url})
        time.sleep(3)

        # 检查 renderAt 是否存在
        has = tab.js("typeof window.renderAt === 'function'")
        print(f"renderAt 存在: {has}")
        if not has:
            print("❌ 页面没有暴露 window.renderAt，无法逐帧导出", file=sys.stderr)
            return 1

        # 检查有无 JS 报错
        err = tab.js("window.__err || null")
        if err:
            print(f"⚠️ 页面错误: {err}")

        results = []
        for t in [float(x) for x in args.times.split(",")]:
            tab.js(f"window.renderAt({t})")
            time.sleep(0.35)
            data = tab.call("Page.captureScreenshot", {"format": "png",
                                                       "captureBeyondViewport": False})
            out = os.path.join(args.out_dir, f"t{t:05.2f}.png")
            with open(out, "wb") as f:
                f.write(base64.b64decode(data["data"]))
            results.append(out)
            print(f"  t={t:.2f}s -> {out}")

        # 确定性检查：同一 t 画两次，像素是否一致
        same = tab.js("""
          (() => {
            const c = document.querySelector('canvas');
            window.renderAt(5.0);
            const a = c.toDataURL();
            window.renderAt(5.0);
            const b = c.toDataURL();
            return a === b;
          })()
        """)
        print(f"确定性（同一 t 两次结果一致）: {same}")

        print(f"\n共 {len(results)} 张")
        return 0
    finally:
        tab.close()
        if started:
            try:
                ps = ("Get-CimInstance Win32_Process | "
                      "Where-Object { $_.CommandLine -like '*--remote-debugging-port={}*' } | "
                      "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }").format(CDP_PORT)
                subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                               capture_output=True, timeout=25)
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(main())
