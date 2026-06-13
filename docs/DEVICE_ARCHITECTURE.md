# Device Architecture

## Hardware

| Property | Value |
|----------|-------|
| SoC | MediaTek Dimensity (ARM64) |
| Architecture | aarch64 |
| CPU cores | 8 (4+4 big.LITTLE) |
| RAM | 7.3 GiB |
| Storage | 229 GiB (189 used, 39 free) |
| GPU | Mali-GPU (MediaTek, no lspci access) |

## Operating System

| Property | Value |
|----------|-------|
| Host OS | Android 16 (SDK 36) — MIUI/Xiaomi |
| Linux layer | PRoot Distro (Debian Trixie/13 container) |
| Kernel | 6.17.0-PRoot-Distro (custom) |
| Terminal | Termux (com.termux) |
| Display | :0 (Xvfb available for headless rendering) |

## Environment

| Property | Value |
|----------|-------|
| User | root (UID 0) |
| Node | v20.19.2 |
| Python | 3.13.5 |
| Package manager | npm, pip3 |
| Shell | /bin/bash (xterm-256color) |

## Installed Tools

### Available natively
- git, curl, wget, ffmpeg
- playwright (1.60.0) + Xvfb
- Python: Flask 3.1.3, Pillow 12.2.0, google-api-* stack
- npm globals: @modelcontextprotocol/server-sequential-thinking, openwork-orchestrator, continuum-mcp, codedev-mcp, brave-search-mcp, firecrawl-mcp, open-websearch, bun

### NOT available (would need install)
- ImageMagick (`convert`) — apt install imagemagick
- mermaid-cli (`mmdc`) — npm install -g @mermaid-js/mermaid-cli
- Inkscape — apt install inkscape
- Cairo — apt install libcairo2-dev
- LaTeX — apt install texlive-latex-base
- Chromium/Firefox browser binaries

## Known Constraints

1. **Process killing**: Android OOM killer terminates Node.js processes (`opencode`) in "tracing stop" state frequently
2. **n8n unstable**: Node.js processes killed within seconds due to Android tracing-stop behavior
3. **Containerized**: PRoot distro — cannot run systemd, Docker, or real init
4. **No GPU accel**: Mali GPU not accessible from PRoot container
5. **Network**: Android host manages networking; PRoot uses NAT/adb tunnel
6. **Display**: Xvfb works for headless browser rendering (playwright screenshots)

## Image Generation Capability

| Method | Available | Quality | Use case |
|--------|-----------|---------|----------|
| PIL/Pillow | ✅ | 6/10 | Flat diagrams, box layouts |
| Playwright + HTML | ✅ | 8/10 | CSS-styled carousels, infographics |
| SVG (hand-coded) | ✅ | 7/10 | Badges, simple vectors |
| Mermaid CLI | ❌ | 9/10 | Would need npm install mmdc |
| Inkscape | ❌ | 10/10 | Would need apt install |

## Typical Ports Used

| Port | Service |
|------|---------|
| 5000 | Flask dev server |
| 5678 | n8n (when running) |
| 8080 | Various HTTP |
| 3000 | Node.js apps |

## Storage Mapping

| Path | Purpose |
|------|---------|
| `/sdcard/` | Termux home / shared storage |
| `/sdcard/Gotjobalert/` | **Project root** (Job Tracker) |
| `/sdcard/OfferTracker_clean/` | Git-clean clone for distribution |
| `/root/` | PRoot root home |
| `/tmp/opencode/` | Temporary workspace for tools |

## Auto-detection Script

Run this to refresh device info:

```bash
echo "CPU:" $(cat /proc/cpuinfo | grep -m1 "model name\|Hardware" | cut -d: -f2)
echo "RAM:" $(free -h | grep Mem | awk '{print $2}')
echo "Kernel:" $(uname -r)
echo "OS:" $(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')
echo "Python:" $(python3 --version 2>&1)
echo "Node:" $(node --version 2>&1)
echo "Disk:" $(df -h / | tail -1 | awk '{print $2, "total,", $4, "free"}')
echo "Android:" $(getprop ro.build.version.release) "SDK" $(getprop ro.build.version.sdk)
```

## Output Display

This environment has no physical display. Images are generated headlessly and written to files. Image preview via Read tool (returns as file attachment).
