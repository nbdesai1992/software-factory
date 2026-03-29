#!/usr/bin/env python3
"""
Software Factory — Project Onboarding

Sets up the Claude Code orchestration system for a target project.
Copies generic skills, renders customizable templates, and generates
project-specific CLAUDE.md and settings.

Usage:
    python onboard.py                       # Setup in current directory
    python onboard.py /path/to/project      # Setup in target directory
    python onboard.py --reconfigure         # Re-run with saved config
"""

import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

@dataclass
class ProjectConfig:
    project_name: str = ""
    project_slug: str = ""
    project_description: str = ""
    domain: str = ""
    frontend_framework: str = "none"
    backend_framework: str = "none"
    database: str = "none"
    deploy_platform: str = "none"
    design_context: str = ""
    dev_server_port: int = 3000
    dev_server_command: str = "npm run dev"
    testing_policy: str = "local"

    def to_replacements(self) -> dict:
        """Return a dict of {{PLACEHOLDER}} → value for template rendering."""
        return {
            "{{PROJECT_NAME}}": self.project_name,
            "{{PROJECT_SLUG}}": self.project_slug,
            "{{PROJECT_DESCRIPTION}}": self.project_description,
            "{{DOMAIN}}": self.domain,
            "{{FRONTEND_FRAMEWORK}}": self.frontend_framework,
            "{{BACKEND_FRAMEWORK}}": self.backend_framework,
            "{{DATABASE}}": self.database,
            "{{DEPLOY_PLATFORM}}": self.deploy_platform,
            "{{DESIGN_CONTEXT}}": self.design_context,
            "{{DEV_SERVER_PORT}}": str(self.dev_server_port),
            "{{DEV_SERVER_COMMAND}}": self.dev_server_command,
            "{{TESTING_POLICY}}": self.testing_policy,
        }


# Smart defaults by framework
FRAMEWORK_DEFAULTS = {
    "react":       {"port": 5173, "command": "npm run dev"},
    "vue":         {"port": 5173, "command": "npm run dev"},
    "svelte":      {"port": 5173, "command": "npm run dev"},
    "nextjs":      {"port": 3000, "command": "npm run dev"},
    "static-html": {"port": 3000, "command": "npx serve public -l 3000"},
    "express":     {"port": 3000, "command": "node server.js"},
    "fastapi":     {"port": 8000, "command": "uvicorn main:app --reload --port 8000"},
    "django":      {"port": 8000, "command": "python manage.py runserver 8000"},
    "flask":       {"port": 5000, "command": "flask run --port 5000"},
}


# ──────────────────────────────────────────────
# Interactive Questionnaire
# ──────────────────────────────────────────────

def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    result = input(f"  {prompt}{suffix}: ").strip()
    return result or default


def ask_choice(prompt: str, choices: list, default: str = "") -> str:
    print(f"\n  {prompt}")
    for i, choice in enumerate(choices, 1):
        marker = " *" if choice == default else ""
        print(f"    {i}. {choice}{marker}")
    while True:
        raw = input(f"  Choose [1-{len(choices)}]: ").strip()
        if not raw and default:
            return default
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            if raw in choices:
                return raw
        print(f"  Please enter a number 1-{len(choices)}")


def interview() -> ProjectConfig:
    config = ProjectConfig()

    print()
    print("=" * 60)
    print("  SOFTWARE FACTORY — Project Onboarding")
    print("=" * 60)
    print()
    print("  Answer a few questions to set up the orchestration system.")
    print("  Press Enter to accept defaults shown in [brackets].")
    print()

    # ── Identity ──
    print("  --- Project Identity ---")
    config.project_name = ask("Project name")
    config.project_slug = re.sub(r"[^a-z0-9-]", "-", config.project_name.lower())
    config.project_slug = re.sub(r"-+", "-", config.project_slug).strip("-")
    config.project_slug = ask("Project slug (for URLs)", config.project_slug)
    config.project_description = ask("Describe your project in 1-2 sentences")
    config.domain = ask("Domain/industry (e.g., 'finance', 'healthcare', 'e-commerce')")

    # ── Design Direction ──
    print("\n  --- Design Direction ---")
    config.design_context = ask(
        "Design context (brand aesthetic, visual feel — or press Enter to auto-generate)"
    )
    if not config.design_context:
        config.design_context = (
            f"This product lives in the world of {config.domain}. "
            f"Design choices should feel domain-specific, not generic SaaS. "
            f"See `session/design-direction.md` for the full design direction when it exists."
        )

    # ── Tech Stack ──
    print("\n  --- Tech Stack ---")
    config.frontend_framework = ask_choice(
        "Frontend framework:",
        ["react", "vue", "svelte", "nextjs", "static-html", "none"],
        default="nextjs",
    )
    config.backend_framework = ask_choice(
        "Backend framework:",
        ["fastapi", "express", "django", "flask", "none"],
        default="fastapi",
    )
    config.database = ask_choice(
        "Database:",
        ["postgresql", "sqlite", "mongodb", "none"],
        default="postgresql",
    )

    # ── Deployment ──
    print("\n  --- Deployment ---")
    config.deploy_platform = ask_choice(
        "Deployment platform:",
        ["render", "vercel", "fly", "none"],
        default="render",
    )

    # ── Dev Server ──
    print("\n  --- Dev Server ---")
    fe = FRAMEWORK_DEFAULTS.get(config.frontend_framework, {})
    be = FRAMEWORK_DEFAULTS.get(config.backend_framework, {})

    if config.frontend_framework != "none":
        default_port = fe.get("port", 3000)
        default_cmd = fe.get("command", "npm run dev")
    elif config.backend_framework != "none":
        default_port = be.get("port", 3000)
        default_cmd = be.get("command", "npm start")
    else:
        default_port = 3000
        default_cmd = "npm start"

    config.dev_server_port = int(ask("Dev server port", str(default_port)))
    config.dev_server_command = ask("Dev server start command", default_cmd)

    # ── Testing ──
    print("\n  --- Testing ---")
    config.testing_policy = ask_choice(
        "Testing policy:",
        ["local", "deploy-only"],
        default="local",
    )

    return config


# ──────────────────────────────────────────────
# Template Rendering
# ──────────────────────────────────────────────

def render_template(content: str, replacements: dict) -> str:
    result = content
    for placeholder, value in replacements.items():
        result = result.replace(placeholder, value)
    return result


def render_file(src: Path, dest: Path, replacements: dict):
    content = src.read_text(encoding="utf-8")
    rendered = render_template(content, replacements)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(rendered, encoding="utf-8")
    print(f"    + {dest.relative_to(dest.parent.parent.parent) if len(dest.parts) > 3 else dest.name}")


def copy_file(src: Path, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    print(f"    + {dest.relative_to(dest.parent.parent.parent) if len(dest.parts) > 3 else dest.name}")


def copy_directory(src: Path, dest: Path):
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    file_count = sum(1 for _ in dest.rglob("*") if _.is_file())
    print(f"    + {dest.name}/ ({file_count} files)")


# ──────────────────────────────────────────────
# Render Blueprint Generation
# ──────────────────────────────────────────────

# Render production commands by framework (monorepo: commands run from rootDir)
RENDER_BACKEND = {
    "fastapi": {
        "runtime": "python",
        "buildCommand": "pip install -r requirements.txt",
        "startCommand": "uvicorn main:app --host 0.0.0.0 --port $PORT",
    },
    "django": {
        "runtime": "python",
        "buildCommand": "pip install -r requirements.txt && python manage.py collectstatic --noinput",
        "startCommand": "gunicorn project.wsgi:application --bind 0.0.0.0:$PORT",
    },
    "flask": {
        "runtime": "python",
        "buildCommand": "pip install -r requirements.txt",
        "startCommand": "gunicorn app:app --bind 0.0.0.0:$PORT",
    },
    "express": {
        "runtime": "node",
        "buildCommand": "npm install",
        "startCommand": "node server.js",
    },
}

RENDER_FRONTEND = {
    "nextjs": {
        "buildCommand": "npm install --legacy-peer-deps && npm run build",
        "startCommand": "npm run start",
    },
    "react": {
        "buildCommand": "npm install && npm run build",
        "startCommand": "npx serve build -l $PORT",
    },
    "vue": {
        "buildCommand": "npm install && npm run build",
        "startCommand": "npx serve dist -l $PORT",
    },
    "svelte": {
        "buildCommand": "npm install && npm run build",
        "startCommand": "npx serve build -l $PORT",
    },
    "static-html": {
        "buildCommand": "npm install",
        "startCommand": "node server.js",
    },
}


def generate_render_yaml(config: ProjectConfig, target: Path):
    """Generate a starter render.yaml blueprint based on project config.

    Uses monorepo layout: backend/ and frontend/ subdirectories, each
    configured as a separate Render web service with rootDir.
    """
    dest = target / "render.yaml"
    if dest.exists():
        print(f"    . render.yaml (already exists — skipping)")
        return

    lines = [
        f"# Render Blueprint — {config.project_name}",
        f"# Generated by software-factory onboarding. Customize as needed.",
        f"# Docs: https://docs.render.com/blueprint-spec",
        "",
    ]

    services = []

    # Backend service (runs from backend/ directory)
    if config.backend_framework != "none":
        be = RENDER_BACKEND.get(config.backend_framework, RENDER_BACKEND["express"])
        svc = [
            f"  - type: web",
            f"    name: {config.project_slug}-api",
            f"    runtime: {be['runtime']}",
            f"    rootDir: backend",
            f"    plan: starter",
            f"    region: oregon",
            f"    buildCommand: {be['buildCommand']}",
            f"    startCommand: {be['startCommand']}",
            f"    healthCheckPath: /health",
            f"    envVars:",
        ]
        if be["runtime"] == "python":
            svc.extend([
                f"      - key: PYTHON_VERSION",
                f'        value: "3.11.6"',
            ])
        if config.database == "postgresql":
            svc.extend([
                f"      - key: DATABASE_URL",
                f"        fromDatabase:",
                f"          name: {config.project_slug}-db",
                f"          property: connectionString",
            ])
        services.append("\n".join(svc))

    # Frontend service (runs from frontend/ directory)
    if config.frontend_framework != "none":
        fe = RENDER_FRONTEND.get(config.frontend_framework, RENDER_FRONTEND["nextjs"])
        svc = [
            f"  - type: web",
            f"    name: {config.project_slug}-frontend",
            f"    runtime: node",
            f"    rootDir: frontend",
            f"    plan: starter",
            f"    region: oregon",
            f"    buildCommand: {fe['buildCommand']}",
            f"    startCommand: {fe['startCommand']}",
            f"    healthCheckPath: /api/health",
            f"    envVars:",
            f"      - key: NODE_ENV",
            f"        value: production",
            f"      - key: PORT",
            f'        value: "10000"',
        ]
        services.append("\n".join(svc))

    if services:
        lines.append("services:")
        lines.append("\n\n".join(services))
        lines.append("")

    # Database (Basic-256mb — $6/month, persistent, no expiry)
    if config.database == "postgresql":
        lines.extend([
            "databases:",
            f"  - name: {config.project_slug}-db",
            f"    plan: basic-256mb",
            f"    region: oregon",
            f"    postgresMajorVersion: 16",
            "",
        ])

    dest.write_text("\n".join(lines), encoding="utf-8")
    print(f"    + render.yaml")


# ──────────────────────────────────────────────
# App Skeleton Generation
# ──────────────────────────────────────────────

BACKEND_SKELETONS = {
    "fastapi": {
        "main.py": '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}
''',
        "requirements.txt": "fastapi\nuvicorn\n",
    },
    "express": {
        "server.js": '''const express = require("express");
const cors = require("cors");
const app = express();
app.use(cors());
app.use(express.json());

app.get("/health", (req, res) => res.json({ status: "ok" }));

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => console.log(`Backend running on port ${PORT}`));
''',
        "package.json": '{\n  "name": "backend",\n  "version": "0.1.0",\n  "private": true,\n  "scripts": { "start": "node server.js" },\n  "dependencies": { "express": "^4.18.0", "cors": "^2.8.5" }\n}\n',
    },
    "django": {
        "requirements.txt": "django\ngunicorn\n",
    },
    "flask": {
        "app.py": '''from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/health")
def health():
    return jsonify(status="ok")
''',
        "requirements.txt": "flask\nflask-cors\ngunicorn\n",
    },
}

FRONTEND_SKELETONS = {
    "nextjs": {
        "package.json": '''{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start"
  },
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/react": "^18.0.0",
    "@types/node": "^20.0.0"
  }
}
''',
        "tsconfig.json": '''{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": false,
    "noEmit": true,
    "incremental": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}
''',
        "app/layout.tsx": '''export const metadata = {
  title: "APP_TITLE",
  description: "APP_DESC",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
''',
        "app/page.tsx": '''export default function Home() {
  return (
    <main>
      <h1>APP_TITLE</h1>
      <p>Coming soon...</p>
    </main>
  );
}
''',
        "app/api/health/route.ts": '''import { NextResponse } from "next/server";

export async function GET() {
  return NextResponse.json({ status: "ok" });
}
''',
    },
}


def generate_backend_skeleton(config: ProjectConfig, target: Path):
    """Create minimal backend directory so Render's first build succeeds."""
    backend_dir = target / "backend"
    if backend_dir.exists() and any(backend_dir.iterdir()):
        print(f"    . backend/ (already exists — skipping)")
        return

    skeleton = BACKEND_SKELETONS.get(config.backend_framework)
    if not skeleton:
        print(f"    ! No skeleton for {config.backend_framework}")
        return

    backend_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in skeleton.items():
        filepath = backend_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
    print(f"    + backend/ (skeleton: {config.backend_framework})")


def generate_frontend_skeleton(config: ProjectConfig, target: Path):
    """Create minimal frontend directory so Render's first build succeeds."""
    frontend_dir = target / "frontend"
    if frontend_dir.exists() and any(frontend_dir.iterdir()):
        print(f"    . frontend/ (already exists — skipping)")
        return

    skeleton = FRONTEND_SKELETONS.get(config.frontend_framework)
    if not skeleton:
        print(f"    ! No skeleton for {config.frontend_framework}")
        return

    frontend_dir.mkdir(parents=True, exist_ok=True)
    for filename, content in skeleton.items():
        content = content.replace("APP_TITLE", config.project_name)
        content = content.replace("APP_DESC", config.project_description)
        filepath = frontend_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
    print(f"    + frontend/ (skeleton: {config.frontend_framework})")


# ──────────────────────────────────────────────
# Project Setup
# ──────────────────────────────────────────────

def setup_project(config: ProjectConfig, target: Path, factory: Path):
    skills_src = factory / "skills"
    templates = factory / "templates"
    replacements = config.to_replacements()

    claude_dir = target / ".claude"
    skills_dir = claude_dir / "skills"
    agents_dir = claude_dir / "agents"

    print()
    print("-" * 40)
    print("  Installing orchestration system...")
    print("-" * 40)

    # ── 1. Generic skills (copy as-is) ──
    print("\n  Generic skills:")
    for skill_name in ["orchestrate", "worker-protocol", "backend-test", "spec", "status", "bold-design"]:
        src = skills_src / skill_name
        dest = skills_dir / skill_name
        if src.exists():
            copy_directory(src, dest)

    # ── 2. Customized skills (render from templates) ──
    print("\n  Customized skills:")

    # verify-ui (only if frontend)
    if config.frontend_framework != "none":
        src = templates / "skills" / "verify-ui" / "SKILL.md.tpl"
        if src.exists():
            render_file(src, skills_dir / "verify-ui" / "SKILL.md", replacements)

    # deploy skill (platform-specific)
    if config.deploy_platform != "none":
        platform_dir = templates / "skills" / "deploy" / config.deploy_platform
        if platform_dir.exists():
            # Render the main SKILL.md
            skill_tpl = platform_dir / "SKILL.md.tpl"
            if skill_tpl.exists():
                render_file(skill_tpl, skills_dir / "deploy" / "SKILL.md", replacements)

            # Copy reference files (non-template .md files)
            for ref_file in sorted(platform_dir.glob("*.md")):
                if not ref_file.name.endswith(".tpl"):
                    copy_file(ref_file, skills_dir / "deploy" / ref_file.name)
        else:
            print(f"    ! No deploy adapter for '{config.deploy_platform}' — skipping")
            print(f"      (only 'render' is currently supported)")

    # ── 3. Agent definitions (render from templates) ──
    print("\n  Agent definitions:")

    agent_configs = {
        "backend-worker": config.backend_framework != "none",
        "frontend-worker": config.frontend_framework != "none",
        "infra-worker": config.deploy_platform != "none",
    }

    for agent_name, should_install in agent_configs.items():
        if not should_install:
            print(f"    - {agent_name} (skipped — not needed)")
            continue
        src = templates / "agents" / f"{agent_name}.md.tpl"
        if src.exists():
            render_file(src, agents_dir / f"{agent_name}.md", replacements)

    # ── 4. Settings.json ──
    print("\n  Configuration:")

    # Build permissions list — orchestrator spawns workers via claude -p
    permissions = ["Bash(dev-browser *)", "Bash(claude -p *)"]

    settings = {"permissions": {"allow": permissions}}
    settings_path = claude_dir / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"    + settings.json")

    # ── 5. CLAUDE.md ──
    claude_tpl = templates / "CLAUDE.md.tpl"
    if claude_tpl.exists():
        render_file(claude_tpl, target / "CLAUDE.md", replacements)

    # ── 6. .gitignore ──
    gitignore_path = target / ".gitignore"
    lines_to_add = ["session/", ".claude/settings.local.json", ".env", ".env.local", "*.env.local"]
    if gitignore_path.exists():
        existing = gitignore_path.read_text(encoding="utf-8")
        additions = [l for l in lines_to_add if l not in existing]
        if additions:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write("\n# Orchestration (added by software-factory)\n")
                for line in additions:
                    f.write(f"{line}\n")
            print(f"    + .gitignore (updated)")
        else:
            print(f"    . .gitignore (already configured)")
    else:
        gitignore_path.write_text(
            "# Orchestration\nsession/\n.claude/settings.local.json\n",
            encoding="utf-8",
        )
        print(f"    + .gitignore (created)")

    # ── 7. render.yaml (if platform is render) ──
    if config.deploy_platform == "render":
        print("\n  Infrastructure:")
        generate_render_yaml(config, target)

    # ── 8. Skeleton app directories (so first Render deploy succeeds) ──
    print("\n  App skeleton:")
    if config.backend_framework != "none":
        generate_backend_skeleton(config, target)
    if config.frontend_framework != "none":
        generate_frontend_skeleton(config, target)

    # ── 9. Save config for re-onboarding ──
    config_path = claude_dir / "factory-config.json"
    config_path.write_text(json.dumps(asdict(config), indent=2) + "\n", encoding="utf-8")
    print(f"    + factory-config.json (for re-onboarding)")

    # ── Done ──
    print()
    print("=" * 60)
    print("  SETUP COMPLETE")
    print("=" * 60)
    print(f"""
  Your project is now configured with the orchestration system.

  Next steps:
    1. cd {target}
    2. Open Claude Code
    3. Run:  /spec create "describe what you want to build"
    4. Review and approve the spec
    5. Run:  /orchestrate
    6. Use:  /status  at any time to check progress

  Skills installed:
    - /spec          Create and manage development specifications
    - /orchestrate   Decompose and execute the spec with worker agents
    - /status        Check progress, blockers, and requirements
""")

    if config.frontend_framework != "none":
        print("    - /bold-design   Domain-specific UI design enforcement")
        print("    - /verify-ui     Visual verification with dev-browser screenshots")

    if config.deploy_platform != "none":
        platform_name = config.deploy_platform.capitalize()
        print(f"    - /deploy        {platform_name} infrastructure management")

    print(f"""
  Workers (spawned via claude -p):
    - backend-worker   {'Installed' if config.backend_framework != 'none' else 'Skipped (no backend)'}
    - frontend-worker  {'Installed' if config.frontend_framework != 'none' else 'Skipped (no frontend)'}
    - infra-worker     {'Installed' if config.deploy_platform != 'none' else 'Skipped (no deploy platform)'}

  See docs/HUMAN-INTERVENTION-GUIDE.md in the software-factory
  repo for when you'll need to step in during orchestration.
""")


# ───────────────────────────────���──────────────
# Main
# ──────────────────────────────────────────────

def main():
    # Determine factory directory (where this script lives)
    script_dir = Path(__file__).resolve().parent
    factory_dir = script_dir / "factory"

    if not factory_dir.exists():
        print(f"Error: factory/ directory not found at {factory_dir}")
        print("Make sure you're running this from the software-factory repo.")
        sys.exit(1)

    # Determine target directory
    reconfigure = "--reconfigure" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if args:
        target = Path(args[0]).resolve()
    else:
        target = Path.cwd()

    if not target.exists():
        print(f"Error: Target directory does not exist: {target}")
        sys.exit(1)

    print(f"\n  Target project: {target}")

    # Check for existing config (re-onboarding)
    existing_config = target / ".claude" / "factory-config.json"
    if reconfigure and existing_config.exists():
        print(f"  Loading saved configuration from {existing_config.name}...")
        saved = json.loads(existing_config.read_text(encoding="utf-8"))
        config = ProjectConfig(**saved)

        print()
        print("  Saved configuration:")
        for key, value in asdict(config).items():
            print(f"    {key}: {value}")

        confirm = input("\n  Re-apply this configuration? [Y/n]: ").strip().lower()
        if confirm in ("n", "no"):
            config = interview()
        # else use saved config
    else:
        config = interview()

    # Show summary
    print()
    print("-" * 40)
    print("  Configuration Summary:")
    print("-" * 40)
    for key, value in asdict(config).items():
        print(f"    {key}: {value}")

    confirm = input("\n  Proceed with setup? [Y/n]: ").strip().lower()
    if confirm in ("n", "no"):
        print("  Aborted.")
        sys.exit(0)

    setup_project(config, target, factory_dir)


if __name__ == "__main__":
    main()
