#!/bin/bash

# Create a clean distribution copy of coding-ai-config
# Strips git history, private files, and prepares for a new org
#
# Usage:
#   scripts/distribute.sh                          # Create dist at ../coding-ai-config-dist
#   scripts/distribute.sh /path/to/output          # Create dist at specified path
#   scripts/distribute.sh --publish <org> [remote]  # Create + init repo + push to GitHub

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(dirname "$SCRIPT_DIR")"
DEFAULT_DIST_DIR="$(dirname "$SOURCE_DIR")/coding-ai-config-dist"

usage() {
  echo "Usage:"
  echo "  $(basename "$0")                            # Create clean copy at $DEFAULT_DIST_DIR"
  echo "  $(basename "$0") /path/to/output            # Create clean copy at specified path"
  echo "  $(basename "$0") --publish <org> [remote]    # Create + push to GitHub org"
  echo ""
  echo "Options:"
  echo "  --publish <org>    Push to github.com/<org>/coding-ai-config"
  echo "  [remote]           Custom remote URL (default: https://github.com/<org>/coding-ai-config.git)"
  echo ""
  echo "Examples:"
  echo "  $(basename "$0")                                          # Local copy only"
  echo "  $(basename "$0") --publish acme-corp                      # Push to acme-corp org"
  echo "  $(basename "$0") --publish acme-corp git@github.com:acme-corp/sdlc-framework.git"
  exit 1
}

# Files and directories to exclude from distribution
EXCLUDE_LIST=(
  ".git"
  "retrospectives"
  "*.bak"
  ".claude/projects"
)

# Files that may contain sensitive data — verify before distributing
SENSITIVE_CHECK=(
  "retrospectives/"
  "*.bak"
)

create_dist() {
  local dist_dir="$1"

  if [ -d "$dist_dir" ]; then
    echo "Distribution directory already exists: $dist_dir"
    read -p "Remove and recreate? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      rm -rf "$dist_dir"
    else
      echo "Aborted."
      exit 1
    fi
  fi

  echo "Creating clean distribution..."
  echo "  Source: $SOURCE_DIR"
  echo "  Target: $dist_dir"
  echo ""

  # Copy everything except excluded items
  mkdir -p "$dist_dir"
  rsync -a \
    --exclude='.git' \
    --exclude='retrospectives/' \
    --exclude='*.bak' \
    --exclude='.claude/projects' \
    "$SOURCE_DIR/" "$dist_dir/"

  echo "  ✓ Files copied (excluding: ${EXCLUDE_LIST[*]})"

  # Verify no sensitive files leaked
  local leaked=false
  for pattern in "${SENSITIVE_CHECK[@]}"; do
    # For directory patterns (trailing /), check with -d
    local check_path="$dist_dir/$pattern"
    if [[ "$pattern" == */ ]] && [ -d "${check_path%/}" ]; then
      echo "  ⚠ WARNING: Sensitive directory found in dist: $pattern"
      leaked=true
    elif [[ "$pattern" != */ ]] && compgen -G "$check_path" > /dev/null 2>&1; then
      echo "  ⚠ WARNING: Sensitive file found in dist: $pattern"
      leaked=true
    fi
  done

  if [ "$leaked" = false ]; then
    echo "  ✓ No sensitive files detected"
  fi

  # Verify no org-specific references remain (except YOUR-ORG placeholders)
  # Configure the source org name to scan for — set SDLC_SOURCE_ORG to your org name
  local source_org="${SDLC_SOURCE_ORG:-}"
  if [ -n "$source_org" ]; then
    local org_refs
    org_refs=$(grep -r "$source_org" "$dist_dir" --include="*.md" --include="*.sh" --include="*.yaml" --include="*.yml" -l 2>/dev/null || true)
    if [ -n "$org_refs" ]; then
      echo "  ⚠ WARNING: Found '$source_org' references in:"
      echo "$org_refs" | sed 's/^/    /'
      echo "  These should be replaced with your org name before publishing."
    else
      echo "  ✓ No personal/org references found"
    fi
  else
    echo "  ✓ Org reference scan skipped (set SDLC_SOURCE_ORG to enable)"
  fi

  # Check for accidental secrets
  local secret_refs
  secret_refs=$(grep -rE "(ASANA_ACCESS_TOKEN|ASANA_TOKEN|api_key|secret_key|password)=" "$dist_dir" --include="*.sh" --include="*.json" --include="*.yaml" --include="*.env" -l 2>/dev/null || true)
  if [ -n "$secret_refs" ]; then
    echo "  ⚠ WARNING: Possible secrets found in:"
    echo "$secret_refs" | sed 's/^/    /'
  else
    echo "  ✓ No secrets detected"
  fi

  echo ""
  echo "Distribution ready at: $dist_dir"
}

init_repo() {
  local dist_dir="$1"
  local remote_url="$2"

  cd "$dist_dir"
  git init
  git add .
  git commit -m "initial commit: SDLC framework for AI-assisted development"
  echo "  ✓ Git repo initialized with clean history"

  if [ -n "$remote_url" ]; then
    git remote add origin "$remote_url"
    echo "  ✓ Remote added: $remote_url"
    echo ""
    read -p "Push to remote? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      git push -u origin main
      echo "  ✓ Pushed to $remote_url"
    else
      echo "  Skipped push. Run manually: cd $dist_dir && git push -u origin main"
    fi
  fi
}

replace_org() {
  local dist_dir="$1"
  local org="$2"

  # Replace YOUR-ORG placeholder with actual org name
  find "$dist_dir" -type f \( -name "*.md" -o -name "*.sh" \) -exec \
    sed -i '' "s|YOUR-ORG|$org|g" {} +

  echo "  ✓ Replaced YOUR-ORG → $org in all files"
}

# --- Main ---

MODE="local"
DIST_DIR="$DEFAULT_DIST_DIR"
ORG=""
REMOTE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --publish)
      MODE="publish"
      if [ $# -lt 2 ]; then
        echo "Error: --publish requires an org name"
        usage
      fi
      ORG="$2"
      shift 2
      if [ $# -gt 0 ] && [[ ! "$1" =~ ^-- ]]; then
        REMOTE="$1"
        shift
      else
        REMOTE="https://github.com/$ORG/coding-ai-config.git"
      fi
      ;;
    -h|--help)
      usage
      ;;
    *)
      DIST_DIR="$1"
      shift
      ;;
  esac
done

echo "SDLC Distribution Builder"
echo "========================="
echo ""

# Create the clean copy
create_dist "$DIST_DIR"

# Replace org placeholder if publishing
if [ "$MODE" = "publish" ]; then
  echo ""
  replace_org "$DIST_DIR" "$ORG"
  init_repo "$DIST_DIR" "$REMOTE"
fi

echo ""
echo "Next steps:"
if [ "$MODE" = "local" ]; then
  echo "  1. Review the dist: ls $DIST_DIR"
  echo "  2. Replace YOUR-ORG placeholders: grep -r YOUR-ORG $DIST_DIR"
  echo "  3. Initialize git: cd $DIST_DIR && git init && git add . && git commit -m 'initial commit'"
  echo "  4. Push to your org: git remote add origin <url> && git push -u origin main"
  echo ""
  echo "  Or use --publish to do steps 2-4 automatically:"
  echo "    $(basename "$0") --publish <your-org>"
else
  echo "  1. Add as submodule to projects: git submodule add $REMOTE .sdlc"
  echo "  2. Run setup: .sdlc/setup-project.sh --init /path/to/project"
  echo "  3. Set SDLC_SUBMODULE_URL=$REMOTE in your environment (optional, for setup-project.sh)"
fi
