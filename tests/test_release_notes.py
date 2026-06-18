from harnetics.release_notes import build_install_guide, merge_install_guide


def test_build_install_guide_includes_platform_specific_assets() -> None:
    guide = build_install_guide("0.2.1")

    assert "Harnetics_0.2.1_x64-setup.exe" in guide
    assert "Harnetics_0.2.1_aarch64.dmg" in guide
    assert "Harnetics_0.2.1_x64.dmg" in guide
    assert guide.count("Harnetics_0.2.1_") == 5


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
