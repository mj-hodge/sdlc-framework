# Contributing

This is the org fork (`hpi-gorillacommerce/sdlc-framework`) of the upstream personal repo (`markoreta-os/sdlc-framework`). Both stay in sync via PRs. Changes always flow through this repo first.

## Repo Relationship

```
Your project → ~/.sdlc (local) → hpi-gorillacommerce/sdlc-framework (origin)
                                          ↓ PR
                                  markoreta-os/sdlc-framework (upstream)
```

`~/.sdlc` is a local clone of this repo. All projects symlink to it — changes are live immediately after `git pull`, no submodule updates needed.

## Making Changes

1. Edit locally in `~/.sdlc` or `/mnt/c/Projects/sdlc-framework`
2. Commit and push to `origin` (this org fork)
3. Sync upstream via PR:
   ```bash
   gh pr create -R markoreta-os/sdlc-framework \
     --head hpi-gorillacommerce:main \
     --title "sync: <description>"
   ```
4. Merge the PR

## Pulling Upstream Changes

If someone edits the personal repo directly:

```bash
git fetch upstream && git rebase upstream/main && git push origin main
```

## Retro Workflow

After a project retro produces `retro-proposal.yaml`, apply the accepted proposals to this repo and push. Reference the source project and proposal IDs in the commit message:

```
retro: apply proposals [P1, P3] from project-name retro
```
