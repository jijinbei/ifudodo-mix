IFUDODO_CONTEXT = (
    "energetic Japanese march-style song, "
    "majestic and powerful, "
    "dramatic brass and percussion, "
    "triumphant and dignified atmosphere, "
    "Ifuudoudou style"
)


def build_prompt(user_description: str) -> str:
    cleaned = user_description.strip()
    if not cleaned:
        return IFUDODO_CONTEXT
    return f"{IFUDODO_CONTEXT}, remixed as {cleaned}"
