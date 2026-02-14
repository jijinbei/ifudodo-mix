IFUDODO_CONTEXT = (
    "Japanese vocal song, 3 verses, "
    "powerful anthem of courage and determination, "
    "marching forward through a corrupt world with unwavering faith"
)

IFUDODO_LYRICS = """\
[Verse 1]
濁悪の此の世行く 学会の
行く手を阻むは 何奴なるぞ
威風堂々と 信行たてて
進む我らの 確信ここに

[Verse 2]
今日もまた明日もまた 折伏の
行軍進めば 血は沸き上がる
威風堂々と 邪法を砕き
民を救わん 我らはここに

[Verse 3]
我ら住む日本の 楽土見ん
北山南河は邪宗の都
威風堂々と 正法かざし
駒を進めば 草木もなびく\
"""


def build_prompt(user_description: str) -> str:
    cleaned = user_description.strip()
    if not cleaned:
        return IFUDODO_CONTEXT
    return (
        f"{cleaned} remix of a {IFUDODO_CONTEXT}, "
        f"reimagined with {cleaned} instrumentation, rhythm, and production"
    )
