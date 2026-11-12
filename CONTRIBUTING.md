# Contributing

Thanks for your interest! Bug reports, ideas and pull requests are welcome.

## Reporting bugs and ideas

Use the [issue forms](https://github.com/spidero/github-stats-card/issues/new/choose).
For bugs, include the card, how you use the action, the version and the log output of
the "Generate" step. **Never paste tokens or secrets.**

## Development setup

No dependencies, just Python 3.9+ (standard library only).

```sh
git clone https://github.com/spidero/github-stats-card && cd github-stats-card
python3 -m unittest discover -s tests -t .   # offline unit + render tests
python3 preview.py                           # renders every card x theme to preview/index.html
```

Fetch real data (optional, needs a token):

```sh
GITHUB_TOKEN=$(gh auth token) python3 -m github_cards <login> dist --cards all
```

## Adding a card

See ["Adding a new card"](README.md#adding-a-new-card): one module in
`github_cards/cards/` with `fetch(api, login, options)` and `render(data, theme, options)`.

Please keep in mind:

- **Visible without animations**: animate *from* a hidden state (`animation: ... backwards`),
  never leave content at `opacity: 0`; a test checks this.
- **Works with the default `GITHUB_TOKEN`**: some GraphQL fields need more permissions;
  fetch optional fields with `api.try_query()` and leave them out when unavailable.
- **No repository names from private repos** on cards, only aggregated numbers.
- **Escape text** with `escape()` from `svg.py`; colors only via themes / `parse_colors`.
- Add sample data for the card to `samples/spidero.json` (`--dump-data`) and a render test.

## Adding a theme

Add an entry to `THEMES` in `github_cards/themes.py` (all keys: `bg`, `border`, `title`,
`label`, `value`, `accent`, `track`; optional `bg2` for a gradient). Check it with
`python3 preview.py` on both light and dark pages, and keep text readable (contrast).

## Pull requests

- One topic per PR, with tests passing (`python3 -m unittest discover -s tests -t .`).
- Don't change defaults or output file names in a way that breaks existing `@v1` users;
  breaking changes go to a new major version.
- Describe what changed and add a screenshot for visual changes.

By contributing you agree that your contributions are licensed under the [MIT License](LICENSE)
and to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
