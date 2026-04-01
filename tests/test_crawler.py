from vangrondwelle.crawler import _discover_contact_links


def test_discover_contact_links_skips_non_http_schemes() -> None:
    html = """
    <html>
      <body>
        <a href="/contact">Contact</a>
        <a href="tel:0701234567">Telefoon</a>
        <a href="mailto:info@example.nl">Email</a>
      </body>
    </html>
    """

    links = _discover_contact_links(html, "https://voorbeeldzorg.nl", "voorbeeldzorg.nl")

    assert links == ["https://voorbeeldzorg.nl/contact"]
