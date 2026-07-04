# Grond — Helm's Deep 2D RPG

Godot 4.2 project repository.

## Import the complete archive

The repository includes `import_project.ps1`, which replaces the temporary files with the complete contents of the project archive and pushes them to `main`.

Run in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\import_project.ps1 -ArchivePath "C:\Users\YOUR_NAME\Downloads\helms_deep_2d_rpg_v3_0_2_typefix(1).zip"
```

The script:

1. Extracts the ZIP into a temporary directory.
2. Finds the folder containing `project.godot`.
3. Clones this repository.
4. Replaces the temporary repository contents with the complete Godot project.
5. Creates a commit and pushes it to `main`.

GitHub authentication must already be configured through Git Credential Manager or GitHub CLI (`gh auth login`).
