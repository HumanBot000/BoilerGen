import os


def process_post_generation_hook(output_path: str, hook_position: str):
    hook_position = os.path.join(hook_position, "hooks")
    os.chdir(output_path)
    if not os.path.exists(os.path.join(hook_position, "post-generation.txt")):
        return
    with open(os.path.join(hook_position, "post-generation.txt"), "r") as f:
        for line in f.readlines():
            os.system(line)


def process_pre_generation_hook(output_path: str, hook_position: str):
    hook_position = os.path.join(hook_position, "hooks")
    os.chdir(output_path)
    if not os.path.exists(os.path.join(hook_position, "pre-generation.txt")):
        return
    with open(os.path.join(hook_position, "pre-generation.txt"), "r") as f:
        for line in f.readlines():
            os.system(line)
