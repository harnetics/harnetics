from harnetics.release_notes import merge_install_guide


def test_merge_install_guide_appends_guide_when_missing() -> None:
    body = "## Harnetics v0.2.1\n\nRelease summary."
    guide = "<!-- hermes-install-guide:start -->\nGuide block\n<!-- hermes-install-guide:end -->"

    updated = merge_install_guide(body, guide)

    assert "Release summary." in updated
    assert guide in updated
    assert updated.count("<!-- hermes-install-guide:start -->") == 1


def test_merge_install_guide_replaces_existing_guide_block() -> None:
    body = "## Harnetics v0.2.1\n\nOld text\n\n<!-- hermes-install-guide:start -->\nold guide\n<!-- hermes-install-guide:end -->\n"
    guide = "<!-- hermes-install-guide:start -->\nnew guide\n<!-- hermes-install-guide:end -->"

    updated = merge_install_guide(body, guide)

    assert "old guide" not in updated
    assert "new guide" in updated
    assert updated.count("<!-- hermes-install-guide:start -->") == 1
