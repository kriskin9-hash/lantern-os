### Keystone Radio — a retro Pip-Boy MP3 player

- New `/fallout-radio.html`: a self-contained retro radio with a phosphor-green CRT / tube-radio skin (scanlines, flicker, VU meter, tuning dial). Tune a station on the dial and the deck plays it. Five public-domain stations to start — the Fallout-radio canon: Ink Spots "I Don't Want to Set the World on Fire", Danny Kaye & the Andrews Sisters "Civilization", Bing Crosby "Pistol Packin' Mama", plus Sinatra radio years and Jazz Classics.
- Audio engine is the Internet Archive `/embed/` player per station (needs only the verified item id — no rate-limited API calls). Adding a song is a one-row edit to the `STATIONS` array. A discreet "📻 Radio" link sits in the Explore quick-links row.
