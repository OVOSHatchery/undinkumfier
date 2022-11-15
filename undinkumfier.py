import shutil


class DeDinkumFier:
    def __init__(self, skill_folder):
        self.path = skill_folder
        with open(f"{self.path}/__init__.py") as f:
            self.code = f.read()
        self.lines = self.code.split("\n")

    @property
    def is_dinkum(self):
        if "def create_skill(skill_id:" in self.code \
                and "def __init__(self, skill_id" in self.code:
            return True
        return False

    def fix(self):
        if not self.is_dinkum:
            raise RuntimeError("Not a dinkum skill!")
        if "CommonPlaySkill" in self.code:
            raise ValueError("CommonPlaySkill not yet supported")
        if "FallbackSkill" in self.code:
            raise ValueError("FallbackSkill not yet supported")
        if "CommonQuerySkill" in self.code:
            raise ValueError("CommonQuerySkill not yet supported")
        if "MycroftSkill" not in self.code:
            raise ValueError("MycroftSkill class import not found")
        if "get_pantacor_device_id" in self.code:
            raise ValueError("this skill is tied to pantacor")
        self.fix_regex()
        self.fix_imports()
        self.fix_skill_id_init()
        self.fix_classes()
        self.fix_adapt()
        self.code = "\n".join([l for l in self.lines if l is not None])
        self.lines = self.code.split("\n")

    def fix_adapt(self):
        in_intent = False
        for idx, l in enumerate(self.lines):
            if l is None:
                continue
            if "IntentBuilder(" in l or "AdaptIntent(" in l:
                in_intent = True
            if in_intent:
                if ".exactly()" in l:
                    self.lines[idx] = l.replace(".exactly()", "")
                if ".exclude(" in l:
                    a, b = l.split(".exclude(")
                    b = b.split(")", 1)[-1]
                    self.lines[idx] = a+b
            if "def" in l:
                in_intent = False

    def fix_regex(self):
        in_intent = False
        for idx, l in enumerate(self.lines):
            if "@intent_handler(" in l:
                in_intent = True
            if in_intent and ".rx" in l:
                # TODO - convert to adapt intent or something
                raise ValueError("this skill uses pure regex intents")
            if ")" in l:
                in_intent = False

    def fix_skill_id_init(self):
        in_class = False
        in_init = False
        in_create = False
        for idx, l in enumerate(self.lines):
            if l is None:
                continue
            if "class " in l:
                in_class = True
                continue
            if in_class and "def __init__" in l:
                in_init = True
            elif in_init and "def " in l and "(self" in l and "):" in l:
                in_init = False
            if "skill_id" not in l:
                continue
            if in_init:
                if "super(" in l and ".__init__(" in l:
                    self.lines[idx] = l.split("__init__(")[0] + "__init__(*args, **kwargs)"
                if "__init__(self, skill_id" in l:
                    self.lines[idx] = l.split(", skill_id")[0] + ", *args, **kwargs):"
            else:
                if "def create_skill(" in l:
                    in_create = True
                    self.lines[idx] = "def create_skill():"
                elif "skill_id" in l and in_create and "return " in l:
                    self.lines[idx] = l.split("(")[0] + "()"

    def fix_classes(self):
        for idx, l in enumerate(self.lines):
            if l is None:
                continue
            if "MycroftSkill" in l:
                self.lines[idx] = l.replace("MycroftSkill", "UnDinkumSkill")

    def fix_imports(self):
        import_start = 0
        in_import = False
        for idx, l in enumerate(self.lines):
            if l is None:
                continue
            if not in_import and "import " not in l:
                continue
            if "import (" in l:
                in_import = True
            if in_import and ")" in l:
                in_import = False
            if not import_start:
                import_start = idx
            if "from mycroft.skills " in l or in_import:
                l = l.replace(" MycroftSkill", "").replace(",,", ","). \
                    replace(" GuiClear", "").replace(",,", ","). \
                    replace(" MessageSend", "").replace(",,", ","). \
                    replace("import,", "import")
                if l.strip().endswith(" import") or l.strip() == ",":
                    l = None
                self.lines[idx] = l
                continue
            if " SkillControl" in l:
                l = l.replace(" SkillControl", "").replace(",,", ","). \
                    replace("import,", "import")
                if l.strip().endswith(" import"):
                    l = None
                self.lines[idx] = l
        self.lines.insert(import_start, "from ovos_workshop.skills.dinkum import GuiClear, UnDinkumSkill, SkillControl, MessageSend")

    def export(self, output_path):
        self.fix()
        shutil.copytree(self.path, output_path, dirs_exist_ok=True)
        with open(f"{output_path}/__init__.py", "w") as f:
            f.write(self.code)


if __name__ == "__main__":
    import os
    from os.path import dirname

    skills = f"{dirname(__file__)}/test/skills"
    for folder in os.listdir(skills):
        dedinkumfi = DeDinkumFier(f"{skills}/{folder}")

        # output = f"/tmp/exported_dinkum/{folder.replace('.mark2', '.undinkum')}"
        output = f"{dirname(__file__)}/test/out/{folder.replace('.mark2', '.undinkum')}"
        os.makedirs(output, exist_ok=True)

        try:
            dedinkumfi.export(output)
        except Exception as e:
            print(folder, e)
            # TODO - fallback + commonXXX skills support
            # query-wolfram-alpha.mark2 CommonQuerySkill not yet supported
            # query-duck-duck-go.mark2 CommonQuerySkill not yet supported
            # support.mark2 Not a dinkum skill! <- ?????
            # query-wiki.mark2 CommonQuerySkill not yet supported
            # news.mark2 CommonPlaySkill not yet supported
            # play-music.mark2 CommonPlaySkill not yet supported
            # fallback-unknown.mark2 FallbackSkill not yet supported
            # play-radio.mark2 CommonPlaySkill not yet supported
            # fallback-query.mark2 FallbackSkill not yet supported
            continue

