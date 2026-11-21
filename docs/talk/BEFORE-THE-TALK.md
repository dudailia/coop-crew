# Before the talk: install coop-crew the day before

The room Wi-Fi will be shared by everyone, and the install downloads a browser engine (about 150 MB). Do it at home the
day before. It takes about 10 minutes, most of it downloads. Bring your laptop charged.

## 1. What to install

| You need | Check it with | Get it |
|---|---|---|
| A Mac, Linux, or Windows with WSL (Ubuntu) | | Windows: `wsl --install` in PowerShell (admin), then restart |
| git | `git --version` | Mac: `xcode-select --install`. Ubuntu/WSL: `sudo apt install git` |
| Python 3.9 or newer | `python3 --version` | Mac: `xcode-select --install`. Ubuntu/WSL: `sudo apt install python3` |
| Node.js 18 or newer (22+ for the form filler) | `node --version` | nodejs.org, or `nvm install 22` |
| Claude Code, signed in on a **paid** Claude plan (Pro or Max) | `claude --version` | `curl -fsSL https://claude.ai/install.sh \| bash` (Windows: inside WSL), from [code.claude.com/docs/en/setup](https://code.claude.com/docs/en/setup). Open a new terminal, run `claude` and follow the browser prompts to sign in; no API key is needed |

Then, in a terminal (on Windows: inside the WSL Ubuntu terminal, in your Linux home folder, not under `/mnt/c`):

```
git clone https://github.com/dudailia/coop-crew && cd coop-crew && ./install.sh && claude
```

On Windows you can also open PowerShell in the cloned folder and run `.\install.ps1` (it does the same inside WSL).

When `claude` starts the first time in the folder, **accept the trust dialog**. The crew's permissions and its safety
hook only load in a trusted folder.

## 2. Check that it works

Inside Claude Code, in the `coop-crew` folder:

1. `/crew-doctor`: the health check. It should end with `0 problem(s)`. A `WARN` line is a note, not a failure (for
   example "no profile yet" before `/setup`, or Mail not set up).
2. `/demo`: the crew runs on a made-up student, in about 5 minutes. It should end with `Submitted: 0. Sent: 0.` and open
   TODAY.html with one review pack. This uses your Claude plan, like any Claude Code session.

No Claude access, or short on time? This runs the same demo without agents, in seconds, and needs no network:

```
python3 -I tools/demo.py run --offline
```

You do **not** need to run `/setup` before the talk. Bring your CV as a PDF if you want to set up your own profile
afterwards (about 30 minutes).

## 3. Common errors and fixes

| You see | Fix |
|---|---|
| `Stopped: git is missing` / `python3 is missing` | Mac: `xcode-select --install`. Ubuntu/WSL: `sudo apt install git python3` |
| `Stopped: python3 is 3.8.x; 3.9 or newer is needed` | Install a newer Python (python.org, or `brew install python`), open a new terminal |
| `Stopped: python3 lacks sqlite3 or zoneinfo` | Ubuntu/WSL: `sudo apt install python3-full` |
| `Stopped: Node.js is missing` or `... is too old` | Install Node 22 from nodejs.org or `nvm install 22`, open a new terminal, run `./install.sh` again |
| `Skipping jev-job-search: it needs Node 22+` | Not an error: everything else works. Upgrade Node later and run `vendor/jev/install.sh` |
| Chromium download fails or hangs | Retry on another network: `npx playwright install chromium` (WSL: `npx playwright install --with-deps chromium`) |
| `./install.sh: Permission denied` | `bash install.sh` |
| `claude: command not found` | Install Claude Code: `curl -fsSL https://claude.ai/install.sh \| bash` ([code.claude.com/docs/en/setup](https://code.claude.com/docs/en/setup)), then open a new terminal |
| `/demo` stops at permission prompts, or the safety hook seems off | Run `claude` in the folder and accept the trust dialog, then try again |
| `/demo` says your plan has no access | Claude Code needs a paid plan (Pro or Max). Use the offline demo above |
| `STOP: the kill switch is on` | Type `/crew-resume` |
| WSL is very slow | You cloned under `/mnt/c`. Clone again in your Linux home folder (`cd ~`) |
| Anything else | Run `/crew-doctor` and bring the output; we will fix it at the start |

Nothing in this setup sends an email or submits an application: the crew works in prepare mode, and nothing leaves your
laptop until you approve that exact item.
