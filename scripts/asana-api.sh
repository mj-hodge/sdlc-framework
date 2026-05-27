#!/bin/bash

# Asana API helper for operations not supported by MCP
# Requires: ASANA_TOKEN environment variable

set -euo pipefail

ASANA_API="https://app.asana.com/api/1.0"

# Auto-source shell profile if token not in environment
if [ -z "${ASANA_TOKEN:-}" ]; then
  [ -f ~/.zshrc ] && source ~/.zshrc 2>/dev/null
  [ -f ~/.bashrc ] && source ~/.bashrc 2>/dev/null
fi

if [ -z "${ASANA_TOKEN:-}" ]; then
  echo "Error: ASANA_TOKEN environment variable not set"
  echo "Get your token from: https://app.asana.com/0/developer-console"
  exit 1
fi

auth_header="Authorization: Bearer $ASANA_TOKEN"

usage() {
  echo "Usage: asana-api.sh <command> [args]"
  echo ""
  echo "Commands:"
  echo "  projects                              List all projects"
  echo "  sections <project_gid>                List sections in a project"
  echo "  move <task_gid> <section_gid>         Move task to section"
  echo "  complete <task_gid>                   Mark task as completed"
  echo "  find-project <name>                   Find project by name"
  echo "  find-section <project_gid> <name>     Find section by name"
  echo "  create-section <project_gid> <name> [insert_before]  Create a new section"
  echo "  tasks <project_gid>                   List tasks in a project (gid, name)"
  echo "  tasks-detailed <project_gid>          List tasks with section and completion"
  echo "  create <project_gid> <name> [notes]   Create a new task in a project"
  echo "  get <task_gid>                        Get task details (name, notes, assignee, status)"
  echo "  get-meta <task_gid>                   Get task details without notes (safe for parsers)"
  echo "  update-name <task_gid> <name>         Update task name"
  echo "  update-notes <task_gid> <notes>       Update task notes/description"
  echo "  comment <task_gid> <text>             Add a comment to the task"
  echo "  create-subtask <parent_gid> <name> [notes]  Create subtask under a parent task"
  echo "  subtasks <task_gid>                   List subtasks of a task"
  echo "  set-parent <task_gid> <parent_gid>    Make a task a subtask of another"
  echo ""
  echo "Examples:"
  echo "  asana-api.sh projects"
  echo "  asana-api.sh find-project sdlc-myproject"
  echo "  asana-api.sh sections 1234567890"
  echo "  asana-api.sh move 1234567890 0987654321"
  echo "  asana-api.sh complete 1234567890"
  echo "  asana-api.sh create 1234567890 \"My Task Name\" \"Detailed notes here\""
  echo "  asana-api.sh get 1234567890"
  echo "  asana-api.sh get-meta 1234567890"
  echo "  asana-api.sh tasks-detailed 1234567890"
  echo "  asana-api.sh update-name 1234567890 \"STORY-016: New task name\""
  echo "  asana-api.sh update-notes 1234567890 \"Updated description here\""
  echo "  asana-api.sh comment 1234567890 \"Phase 1 completed. Seed created.\""
}

api_get() {
  local url="$1"
  curl -sS -H "$auth_header" "$url"
}

api_post() {
  local url="$1"
  local payload="$2"
  curl -sS -X POST -H "$auth_header" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    "$url"
}

api_put() {
  local url="$1"
  local payload="$2"
  curl -sS -X PUT -H "$auth_header" \
    -H "Content-Type: application/json" \
    -d "$payload" \
    "$url"
}

# Get user and team info
get_team_gid() {
  local me
  me=$(api_get "$ASANA_API/users/me")
  local user_gid workspace_gid
  user_gid=$(printf '%s' "$me" | jq -r '.data.gid')
  workspace_gid=$(printf '%s' "$me" | jq -r '.data.workspaces[0].gid')
  api_get "$ASANA_API/users/$user_gid/teams?organization=$workspace_gid" | jq -r '.data[0].gid'
}

# List all projects
projects() {
  local team_gid
  team_gid=$(get_team_gid)
  api_get "$ASANA_API/teams/$team_gid/projects" | jq -r '.data[] | "\(.gid)\t\(.name)"'
}

# List sections in a project
sections() {
  local project_gid=$1
  api_get "$ASANA_API/projects/$project_gid/sections" | jq -r '.data[] | "\(.gid)\t\(.name)"'
}

# Move task to section
move() {
  local task_gid=$1
  local section_gid=$2
  local payload
  payload=$(jq -n --arg t "$task_gid" '{data: {task: $t}}')
  api_post "$ASANA_API/sections/$section_gid/addTask" "$payload" | jq -r 'if .data then "OK: Task moved" else "Error: \(.errors[0].message)" end'
}

# Mark task as completed
complete() {
  local task_gid=$1
  api_put "$ASANA_API/tasks/$task_gid" '{"data": {"completed": true}}' | jq -r 'if .data.completed then "OK: Task marked complete" else "Error: \(.errors[0].message // "unknown")" end'
}

# Find project by name
find_project() {
  local name=$1
  local team_gid
  team_gid=$(get_team_gid)
  api_get "$ASANA_API/teams/$team_gid/projects" | jq -r --arg n "$name" '.data[] | select(.name == $n) | .gid'
}

# Find section by name in project
find_section() {
  local project_gid=$1
  local name=$2
  api_get "$ASANA_API/projects/$project_gid/sections" | jq -r --arg n "$name" '.data[] | select(.name == $n) | .gid'
}

# Create a section in a project
# Usage: asana-api.sh create-section <project_gid> <name> [insert_before_section_gid]
create_section() {
  local project_gid=$1
  local name=$2
  local insert_before=${3:-}
  local payload
  if [ -n "$insert_before" ]; then
    payload=$(jq -n --arg n "$name" --arg b "$insert_before" '{data: {name: $n, insert_before: $b}}')
  else
    payload=$(jq -n --arg n "$name" '{data: {name: $n}}')
  fi
  api_post "$ASANA_API/projects/$project_gid/sections" "$payload" | jq -r 'if .data then "\(.data.gid)\t\(.data.name)" else "Error: \(.errors[0].message)" end'
}

# List tasks in a project
tasks() {
  local project_gid=$1
  api_get "$ASANA_API/projects/$project_gid/tasks" | jq -r '.data[] | "\(.gid)\t\(.name)"'
}

# List tasks in a project with section/completion metadata
tasks_detailed() {
  local project_gid=$1
  api_get "$ASANA_API/projects/$project_gid/tasks?opt_fields=gid,name,completed,memberships.section.name&limit=100" | \
    jq -r '.data[] | "\(.gid)\t\(.name)\t\(.completed)\t\(.memberships[0].section.name // "unknown")"'
}

# Get task details (full includes notes, meta excludes notes)
get_task() {
  local task_gid=$1
  local mode=${2:-full}
  local fields="name,assignee.name,completed,memberships.section.name"

  if [ "$mode" = "full" ]; then
    fields="name,notes,assignee.name,completed,memberships.section.name"
  fi

  local response
  response=$(api_get "$ASANA_API/tasks/$task_gid?opt_fields=$fields")

  if [ "$mode" = "full" ]; then
    # Strip only non-printable control chars that can break downstream JSON consumers.
    printf '%s' "$response" | jq '{
      gid: .data.gid,
      name: .data.name,
      notes: ((.data.notes // "") | gsub("[\u0000-\u0008\u000B\u000C\u000E-\u001F]"; "")),
      assignee: (.data.assignee.name // "unassigned"),
      completed: .data.completed,
      section: (.data.memberships[0].section.name // "unknown")
    }'
  else
    printf '%s' "$response" | jq '{
      gid: .data.gid,
      name: .data.name,
      assignee: (.data.assignee.name // "unassigned"),
      completed: .data.completed,
      section: (.data.memberships[0].section.name // "unknown")
    }'
  fi
}

# Update task name
update_name() {
  local task_gid=$1
  local name=$2
  local json_name
  json_name=$(jq -n --arg n "$name" '{data: {name: $n}}')
  api_put "$ASANA_API/tasks/$task_gid" "$json_name" | jq -r 'if .data then "OK: Name updated" else "Error: \(.errors[0].message // "unknown")" end'
}

# Read text from arg $2, or from stdin if $2 is "-" or missing
_read_text() {
  local arg="${1:-}"
  if [ "$arg" = "-" ] || [ -z "$arg" ]; then
    cat
  else
    printf '%s' "$arg"
  fi
}

# Update task notes/description
# Usage: asana-api.sh update-notes <task_gid> <notes>
#    or: cat notes.txt | asana-api.sh update-notes <task_gid> -
update_notes() {
  local task_gid=$1
  local notes
  notes=$(_read_text "${2:-}")
  local json_notes
  json_notes=$(jq -n --arg n "$notes" '{data: {notes: $n}}')
  api_put "$ASANA_API/tasks/$task_gid" "$json_notes" | jq -r 'if .data then "OK: Notes updated" else "Error: \(.errors[0].message // "unknown")" end'
}

# Add comment to task
# Usage: asana-api.sh comment <task_gid> <text>
#    or: cat comment.txt | asana-api.sh comment <task_gid> -
comment() {
  local task_gid=$1
  local text
  text=$(_read_text "${2:-}")
  local json_payload
  json_payload=$(jq -n --arg t "$text" '{data: {text: $t}}')
  api_post "$ASANA_API/tasks/$task_gid/stories" "$json_payload" | jq -r 'if .data then "OK: Comment added" else "Error: \(.errors[0].message)" end'
}

# Create a subtask under a parent task
# Usage: asana-api.sh create-subtask <parent_task_gid> <name> [notes]
create_subtask() {
  local parent_gid=$1
  local name=$2
  local notes=${3:-}
  local json_payload
  json_payload=$(jq -n --arg p "$parent_gid" --arg n "$name" --arg d "$notes" '{data: {parent: $p, name: $n, notes: $d}}')
  local response
  response=$(api_post "$ASANA_API/tasks" "$json_payload")
  local subtask_gid
  subtask_gid=$(printf '%s' "$response" | jq -r 'if .data then .data.gid else empty end')
  if [ -z "$subtask_gid" ]; then
    printf '%s' "$response" | jq -r '"Error: \(.errors[0].message)"'
    return 1
  fi
  # Get parent's project membership to add subtask to same project
  local parent_project
  parent_project=$(api_get "$ASANA_API/tasks/$parent_gid?opt_fields=projects.gid" | jq -r '.data.projects[0].gid // empty')
  if [ -n "$parent_project" ]; then
    api_post "$ASANA_API/tasks/$subtask_gid/addProject" "$(jq -n --arg p "$parent_project" '{data: {project: $p}}')" > /dev/null
  fi
  echo "$subtask_gid"
}

# List subtasks of a task
# Usage: asana-api.sh subtasks <task_gid>
subtasks() {
  local task_gid=$1
  api_get "$ASANA_API/tasks/$task_gid/subtasks" | jq -r '.data[] | "\(.gid)\t\(.name)"'
}

# Set parent of a task (make it a subtask)
# Usage: asana-api.sh set-parent <task_gid> <parent_task_gid>
set_parent() {
  local task_gid=$1
  local parent_gid=$2
  local payload
  payload=$(jq -n --arg p "$parent_gid" '{data: {parent: $p}}')
  api_post "$ASANA_API/tasks/$task_gid/setParent" "$payload" | jq -r 'if .data then "OK: Parent set" else "Error: \(.errors[0].message)" end'
}

# Create a new task in a project
create() {
  local project_gid=$1
  local name=$2
  local notes=${3:-}
  local json_payload
  json_payload=$(jq -n --arg p "$project_gid" --arg n "$name" --arg d "$notes" '{data: {projects: [$p], name: $n, notes: $d}}')
  api_post "$ASANA_API/tasks" "$json_payload" | jq -r 'if .data then .data.gid else "Error: \(.errors[0].message)" end'
}

# Main
case "${1:-}" in
  projects)
    projects
    ;;
  sections)
    sections "$2"
    ;;
  move)
    move "$2" "$3"
    ;;
  complete)
    complete "$2"
    ;;
  find-project)
    find_project "$2"
    ;;
  find-section)
    find_section "$2" "$3"
    ;;
  create-section)
    create_section "$2" "$3" "${4:-}"
    ;;
  tasks)
    tasks "$2"
    ;;
  tasks-detailed)
    tasks_detailed "$2"
    ;;
  create)
    create "$2" "$3" "${4:-}"
    ;;
  get)
    get_task "$2" full
    ;;
  get-meta)
    get_task "$2" meta
    ;;
  update-name)
    update_name "$2" "$3"
    ;;
  update-notes)
    update_notes "$2" "$3"
    ;;
  comment)
    comment "$2" "$3"
    ;;
  create-subtask)
    create_subtask "$2" "$3" "${4:-}"
    ;;
  subtasks)
    subtasks "$2"
    ;;
  set-parent)
    set_parent "$2" "$3"
    ;;
  *)
    usage
    exit 1
    ;;
esac
