### Dream-chat: Vision — analyze uploaded images (Claude / GPT-4o)

- Upload an image via the `+` (chip shows 🖼️) and ask about it — the chat now *sees* the image. The bytes go to a vision model server-side (`lib/vision.js` + `POST /api/vision/analyze`; **Claude** primary, **gpt-4o-mini** fallback, key stays server-side) and the answer renders inline with a 👁 vision badge. Sticky like other attachments, so follow-up questions about the same image keep working. Closes the image *understanding* gap that complements the image *generation* shipped earlier. (#1201)
