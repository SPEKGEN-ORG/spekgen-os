---
name: WhatsApp Notifications Discarded
description: WhatsApp notifications via CallMeBot were discarded long ago. Do not configure or mention as a pending item.
type: feedback
---

## Rule

The WhatsApp notification system (CallMeBot) for the Content Hub was discarded. Do NOT:
- Flag missing GIBRAN_WHATSAPP or CALLMEBOT_API_KEY env vars as errors
- Suggest configuring WhatsApp notifications
- Mention it as a pending/broken feature

The smoke test at /api/smoke-test should still check it (informational) but it's not a blocker.

## Origin

Gibran explicitly said "lo del WhatsApp hace tiempo que se descartó" on 2026-03-31 when the smoke test flagged it as a failure.
