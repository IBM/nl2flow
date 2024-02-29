def trim_pddl_str(pddl_text: str, keyword: str) -> str:
    lines = pddl_text.split("\n")
    idx_pddl_start = -1
    for idx, line in enumerate(lines):
        if keyword in line:
            idx_pddl_start = idx
            break
    if idx_pddl_start == -1:
        return ""
    return "\n".join(lines[idx_pddl_start:])
