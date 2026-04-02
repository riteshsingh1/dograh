# India Telephony Provider Recommendation

This note compares telephony options for India based on:
- running cost,
- integration effort with current platform,
- and go-live speed.

---

## 1) Executive Recommendation

For your platform, the most practical cost-effective path is:

1. **Immediate go-live**: use an already integrated provider (`Vobiz` or `Twilio`) and start pilot traffic.
2. **Cost optimization phase**: add **Plivo integration** if your monthly usage justifies engineering effort.
3. **Long-term enterprise control**: use **Asterisk (ARI) + India SIP trunk** if client has PBX/telecom ops maturity.

Why this approach:
- You avoid launch delays now.
- You still get a clear path to lower per-minute cost later.

---

## 2) What Is Already Supported in Your Platform

No new backend architecture is required for these:
- `Twilio`
- `Vonage`
- `Vobiz`
- `Cloudonix`
- `Asterisk (ARI)`

So you can launch without waiting for a new connector.

---

## 3) India Cost Snapshot (Publicly Visible Data)

> Note: Public pricing pages change frequently. Always validate with live dashboard quote before contract sign-off.

### Twilio (India voice page)
- Outbound India landline: `~$0.0497/min`
- Outbound India mobile: `~$0.0405/min`
- Strong reliability and docs, but usually not lowest India cost.

### Plivo (India voice page)
- Outbound local/mobile: `~INR 0.74/min`
- Inbound local: `~INR 2.8/min`
- Browser/SIP calls: `~INR 0.34/min`
- India local number rental: `~INR 250/month` (published on page)

### Plivo Setup (Practical)
1. Create a Plivo account and complete business/KYC verification for India traffic.
2. Buy a Plivo voice number and enable voice calling for your target regions.
3. In the app, open **Configure Telephony** and select **Plivo**.
4. Enter:
   - `Auth ID`
   - `Auth Token`
   - `From Number(s)` in E.164 format **without** `+` (example: `9198XXXXXXXX`)
5. Save configuration and run a test outbound call.
6. For inbound (optional), set your provider webhook to:
   - `https://<your-domain>/api/v1/telephony/inbound/<workflow_id>`
7. Keep Twilio/Vobiz as backup during first production week.

### Vonage
- India pricing not clearly visible in a static public table.
- Requires direct dashboard quote / sales quote for accurate India rates.

### India-native providers (Exotel/Knowlarity)
- Often quote via plans/credits instead of clean API-rate tables.
- Can be cost-effective for domestic traffic, but API voice bot fit must be validated case-by-case.

---

## 4) Decision Matrix (Cost + Fit)

| Option | Integration in your platform | Expected India cost position | Go-live speed | Notes |
|---|---|---|---|---|
| Vobiz | Already integrated | Unknown until quote; often competitive | Fast | Best "no-code-change" alternative to Twilio/Vonage |
| Twilio | Already integrated | Typically higher than India-first providers | Fastest | Strongest stability and ecosystem |
| Vonage | Already integrated | Unknown until quote | Fast | Good quality; confirm inbound/number availability for your use case |
| Plivo | Not yet integrated | Potentially low outbound cost | Medium | Best cost candidate if you can invest in connector build |
| Asterisk (ARI) + SIP trunk | Already integrated (ARI side) | Can be lowest at scale | Medium/Slow | Needs telephony ops and PBX ownership |

---

## 5) Best Cost-Effective Strategy by Use Case

### If priority is fastest launch (0 delay)
- Start with **Vobiz** (or Twilio fallback) because already integrated.
- Get commercial quote and run pilot.

### If priority is lowest outbound cost
- Add **Plivo integration** and benchmark side-by-side for 2 weeks.
- Keep existing provider as fallback.

### If priority is enterprise cost control at high volume
- Use **Asterisk (ARI) + local SIP trunk** architecture.
- Better unit economics possible, but more ops responsibility.

---

## 6) Should You Add New Integration Now?

Yes, if both are true:
- Monthly voice volume is significant (so rate delta matters), and
- Client accepts 1-2 additional weeks for integration + QA.

Otherwise:
- Launch first on existing provider, then optimize in phase 2.

---

## 7) Integration Effort Estimate (Plivo)

For your current architecture (`TelephonyProvider` abstraction), a Plivo connector is straightforward.

Typical effort:
- Backend provider implementation + webhook signature verification
- WebSocket media handling and status callbacks
- UI config form additions
- Integration tests + production hardening

Estimated timeline:
- **4-7 working days** for production-ready implementation and testing

---

## 8) Recommended Next Action

Collect quotes from:
- Vobiz (already integrated),
- Vonage (already integrated),
- Plivo (for cost benchmark),

then compare using the same traffic model:
- inbound minutes/month,
- outbound minutes/month,
- number count,
- recording minutes,
- expected peak concurrent calls.

Once you share these 5 inputs, final provider selection can be made with confidence.

