# Teacher Testing Guide (no secrets)

Share **`backend/teacher-handoff.txt`** with your teacher privately. Generate it with:

```bash
cd backend && source venv/bin/activate && python scripts/export_teacher_package.py
```

## Links to send

| Item | URL |
|------|-----|
| Web app | https://mini-n8n-gilt.vercel.app |
| Backend status | https://mini-n8n-production.up.railway.app/setup/status |

## Teacher steps

1. Open the web app → **Open Editor**
2. **Credentials** → paste values from `teacher-handoff.txt` → **Save Credentials**
3. Add nodes: WhatsApp Trigger → AI Extractor → Google Sheets → WhatsApp Reply
4. Connect nodes and configure each one
5. **Execute Workflow** to test manually
6. WhatsApp test: message **+1 555 185 1299** (student must add teacher's number in Meta test recipients)

## Sample WhatsApp order

```
Hi, I want 2 blue shirts and 1 black shoe.
Name: Ahmed
Address: Karachi
Phone: 03001234567
```

## Important

- Never commit `teacher-handoff.txt` or share tokens on public channels
- In Meta **Development** mode, only pre-added phone numbers receive confirmations
- Saving credentials on the live app updates the shared production server
