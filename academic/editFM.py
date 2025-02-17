from pathlib import Path

from ruamel.yaml import YAML

yaml = YAML()


class EditableFM:
    def __init__(self, base_path: Path, delim: str = "---", dry_run: bool = False):
        self.base_path = base_path
        if delim != "---":
            raise NotImplementedError("Currently, YAML is the only supported front-matter format.")
        self.delim = delim
        self.fm = []
        self.content = []
        self.path = ""
        self.dry_run = dry_run

    def load(self, file: Path):
        self.fm = []
        self.content = []
        self.path = self.base_path / file
        if self.dry_run and not self.path.exists():
            self.fm = dict()
            return

        with self.path.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        delims_seen = 0
        for line in lines:
            if line.startswith(self.delim):
                delims_seen += 1
            else:
                if delims_seen < 2:
                    self.fm.append(line)
                else:
                    self.content.append(line)

        # Parse YAML, trying to preserve comments and whitespace
        self.fm = yaml.load("".join(self.fm))

    def dump(self):
        assert self.path, "You need to `.load()` first."
        if self.dry_run:
            return

        content_differs = True

        # Load Markdown file and compare to new one.
        with open(self.path, "r", encoding="utf-8") as f:
            old_content = [line for line in f.readlines()[1:-2] if not
                           (line == "" or line.strip().startswith("#") or
                            line.startswith("publishDate:"))]
            import io
            new_output = io.StringIO()
            yaml.dump(self.fm, new_output)
            # print(new_output)
            new_output_lines = new_output.getvalue().split("\n")
            new_output.close()

            new_content = [line+"\n" for line in new_output_lines if not
                           (line.startswith("publishDate:") or line == "")]
            import difflib
            print("".join(difflib.unified_diff(old_content, new_content)))
            if len(list(difflib.unified_diff(new_content, old_content))) == 0:
                content_differs = False

        # Save Markdown file.
        if content_differs:
            with open(self.path, "w", encoding="utf-8") as f:
                f.write("{}\n".format(self.delim))
                yaml.dump(self.fm, f)
                f.write("{}\n".format(self.delim))
                f.writelines(self.content)
        else:
            print(f"*NOT* saving identical Markdown to '{self.path}'")
