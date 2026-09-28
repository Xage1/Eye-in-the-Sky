import os

output_filename = "eye_in_the_sky.txt"
excluded_dirs = {
    "node_modules",
    ".git",
    "dist",
    "uploads",
    "__pycache__",
    "venv",
    ".venv",
    ".gradle",
    "build",
    "bin",
    "out",
    ".vs",
    ".idea",
}

print("Generating project export...")

with open(output_filename, "w", encoding="utf-8") as out:
  # 1. Write Project Structure
  out.write("==================== PROJECT STRUCTURE ====================\n")
  for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in excluded_dirs]
    parts = os.path.normpath(root).split(os.sep)
    if any(p in excluded_dirs for p in parts):
      continue
    out.write(os.path.abspath(root) + "\n")

  # 2. Write Source Code
  out.write("\n\n==================== SOURCE CODE ====================\n\n")

  for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if d not in excluded_dirs]
    parts = os.path.normpath(root).split(os.sep)
    if any(p in excluded_dirs for p in parts):
      continue

    for file in files:
      # Skip any export text files or the script itself
      if file == output_filename or file.endswith("_export.txt"):
        continue

      file_path = os.path.join(root, file)
      out.write(f"FILE_PATH: {os.path.abspath(file_path)}\n")
      out.write("-" * 79 + "\n")
      try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
          out.write(f.read() + "\n")
      except Exception:
        out.write("[Binary or unreadable file skipped]\n")

print(f"Export completed cleanly to {output_filename}")