# Troubleshooting

| Problem | Fix |
|---|---|
| The assistant ignores the rules | Run the [loading check](setup.md#3-check-that-your-assistant-actually-loads-the-files), then use the workaround for your client in [Other clients](how-it-works.md#other-clients). In Copilot, also try a more capable model: a small one may skip the rule files |
| Copilot CLI does not list the `.claude/rules` files | Update it: `.claude/rules` needs version 1.0.89 or later. Or install the [`github` layout](how-it-works.md#two-layouts) |
| The installer says the project already has rule files from the other layout | Keep that layout with `--layout`, or delete the files it lists and run it again. See [installing](setup.md#1-install-the-files) |
| The assistant uses a different MuleSoft workflow, looks up "latest" versions or insists on `mvn clean package` | Another MuleSoft skill was chosen. See [team setup](setup.md#4-make-sure-no-other-mulesoft-skill-can-take-over) |
| The assistant invents versions or upgrades dependencies | Fill in the project rows of `team-profile.md` ([how](setup.md#2-fill-in-the-projects-facts)) |
| The script says a file differs | Compare the project's file with the one under `overlay/shared/` and merge by hand, or run with `--update` for the shared rule files |
| `scripts/build.py --check` fails | `overlay/github` is out of date. Run `python3 scripts/build.py` and commit the result |
| You can't see `.claude` or `.github` on a Mac | Press Cmd+Shift+. in Finder |
