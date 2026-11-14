#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把带 renderAt 接口的 HTML 动画逐帧渲染成 MP4。

用法：
  python render_anim.py --html 片头.html --out out.mp4 --duration 12 --fps 30
依赖：Edge/Chrome（CDP）、ffmpeg。无需 playwright。
"""
from __future__ import annotations
import argparse, base64, json, os, shutil, subprocess, sys, tempfile, time, urllib.request

CDP_PORT = 9335
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FFMPEG = r"C:\Users\Administrator\.dsh\tools\ffmpeg\bin\ffmpeg.exe"


def http_json(path):
    with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}{path}", timeout=10) as r:
        return json.loads(r.read().decode())


def alive():
    try:
        http_json("/json/version"); return True
    except Exception:
        return False


class Tab:
    def __init__(self):
        import websocket
        pages = [t for t in http_json("/json/list") if t.get("type") == "page"]
        self.ws = websocket.create_connection(pages[0]["webSocketDebuggerUrl"], timeout=120)
        self._id = 0

    def call(self, method, params=None, timeout=120):
        self._id += 1
        mid = self._id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        end = time.time() + timeout
        while time.time() < end:
            m = json.loads(self.ws.recv())
            if m.get("id") == mid:
                if "error" in m: raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result", {})
        raise TimeoutError(method)

    def js(self, expr, timeout=60):
        r = self.call("Runtime.evaluate", {"expression": expr, "returnByValue": True,
                                           "awaitPromise": True}, timeout=timeout)
        res = r.get("result", {})
        if res.get("subtype") == "error": raise RuntimeError(res.get("description", "JS error"))
        return res.get("value")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--duration", type=float, default=12.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--width", type=int, default=1920)
    ap.add_argument("--height", type=int, default=1080)
    args = ap.parse_args()

    path = os.path.abspath(args.html)
    frames_dir = tempfile.mkdtemp(prefix="anim-frames-")
    user_data = tempfile.mkdtemp(prefix="anim-render-")
    total = int(args.duration * args.fps) + (1 if args.duration * args.fps % 1 else 0)
    print(f"渲染 {args.duration}s @ {args.fps}fps = {total} 帧")

    started = False
    if not alive():
        subprocess.Popen(
            [EDGE, f"--remote-debugging-port={CDP_PORT}", f"--user-data-dir={user_data}",
             "--no-first-run", "--no-default-browser-check",
             f"--window-size={args.width},{args.height}", "--hide-scrollbars",
             "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        started = True
        for _ in range(60):
            if alive(): break
            time.sleep(0.5)

    tab = None
    try:
        tab = Tab()
        tab.call("Page.enable")
        tab.call("Runtime.enable")
        tab.call("Emulation.setDeviceMetricsOverride",
                 {"width": args.width, "height": args.height, "deviceScaleFactor": 1, "mobile": False})
        tab.call("Page.navigate", {"url": "file:///" + path.replace("\\", "/") + "?export=1"})
        time.sleep(3)
        if not tab.js("typeof window.renderAt === 'function'"):
            print("❌ 页面没有 renderAt 接口", file=sys.stderr); return 1

        t0 = time.time()
        for f in range(total):
            t = f / args.fps
            tab.js(f"window.renderAt({t:.6f})")
            data = tab.call("Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(frames_dir, f"f{f:05d}.png"), "wb") as fh:
                fh.write(base64.b64decode(data["data"]))
            if f % 30 == 0:
                el = time.time() - t0
                print(f"  {f}/{total} 帧，{el:.0f}s", flush=True)

        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        r = subprocess.run(
            [FFMPEG, "-y", "-framerate", str(args.fps),
             "-i", os.path.join(frames_dir, "f%05d.png"),
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
             args.out],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        if r.returncode != 0:
            print(f"ffmpeg 失败: {r.stderr[-500:]}", file=sys.stderr); return 1

        size = os.path.getsize(args.out)
        print(f"✅ 完成：{args.out}（{size/1024/1024:.1f} MB，{total} 帧，耗时 {time.time()-t0:.0f}s）")
        return 0
    finally:
        if tab: tab.close()
        if started:
            try:
                ps = ("Get-CimInstance Win32_Process | "
                      "Where-Object { $_.CommandLine -like '*--remote-debugging-port={}*' } | "
                      "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }").format(CDP_PORT)
                subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=25)
            except Exception: pass
        shutil.rmtree(frames_dir, ignore_errors=True)
        shutil.rmtree(user_data, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
