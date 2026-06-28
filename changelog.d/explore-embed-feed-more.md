### Explore: more open-archive + OSS embeds in the feed

- Four more curated `embed` panels in `data/explore/embeds.json` (9 total): **Pac-Man (1983)** (Internet Archive emulator), **2048** (MIT, served from its own GitHub Pages — the OSS/community slot), **Night of the Living Dead (1968)** (public-domain film, streamable in-page), and **Jazz Classics** (public-domain Armstrong/Ellington/Fitzgerald audio). Each verified live: archive.org `/embed/` resolves and `gabrielecirulli.github.io/2048/` sends no `X-Frame-Options`/CSP, so it frames.
- The embed-src allowlist in `explore.html` now also permits `*.github.io` (alongside archive.org / youtube-nocookie / vimeo / root-relative) so MIT-licensed OSS games hosted on GitHub Pages can be framed — still sandboxed.
