import os

HOOK_DIR = os.path.join(os.getcwd(), "boilergen", "hooks")


def process_post_generation_hook(output_path: str):
    os.chdir(output_path)
    if not os.path.exists(os.path.join(HOOK_DIR, "post-generation.txt")):
        return
    with open(os.path.join(HOOK_DIR, "post-generation.txt"), "r") as f:
        for line in f.readlines():
            os.system(line)

def process_pre_generation_hook(output_path: str):
    os.chdir(output_path)
    if not os.path.exists(os.path.join(HOOK_DIR, "pre-generation.txt")):
        return
    with open(os.path.join(HOOK_DIR, "pre-generation.txt"), "r") as f:
        for line in f.readlines():
            os.system(line)
