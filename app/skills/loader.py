from pathlib import Path

import yaml


SKILLS_DIR = Path(__file__).parent


def load_skill(skill_name: str) -> dict:
    skill_file = SKILLS_DIR / f"{skill_name}.yaml"
    if not skill_file.exists():
        raise FileNotFoundError(f"Skill not found: {skill_name}")

    with open(skill_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_prompt(skill: dict, variables: dict) -> str:
    prompt = skill["system_prompt"]
    for key, value in variables.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", str(value))
    return prompt
