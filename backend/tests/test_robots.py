from app.crawler.machine_readability import AI_BOTS, parse_robots


def test_all_allowed_when_no_root_disallow():
    # Rivian-like: wildcard group with only path disallows -> AI bots allowed.
    robots = "User-agent: *\nDisallow: /api/\nDisallow: /experience/r1t\n"
    policy = parse_robots(robots)
    assert set(policy) == set(AI_BOTS)
    assert all(v == "allowed" for v in policy.values())


def test_wildcard_root_disallow_blocks_everyone():
    robots = "User-agent: *\nDisallow: /\n"
    policy = parse_robots(robots)
    assert all(v == "blocked" for v in policy.values())


def test_specific_bot_block_overrides_wildcard():
    robots = "User-agent: *\nDisallow: /api/\n\nUser-agent: GPTBot\nDisallow: /\n"
    policy = parse_robots(robots)
    assert policy["GPTBot"] == "blocked"
    assert policy["ClaudeBot"] == "allowed"  # falls back to permissive wildcard


def test_empty_robots_is_permissive():
    policy = parse_robots("")
    assert all(v == "allowed" for v in policy.values())
