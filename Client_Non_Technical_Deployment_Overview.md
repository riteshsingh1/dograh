# Client Deployment Overview (Non-Technical)

This document explains what your organization needs to buy or arrange, and how the voice AI service will work in day-to-day use.

---

## 1) What the Client Needs to Purchase

Below are the typical services required for a production setup.

### A. Infrastructure (Required)

1. **Cloud server or hosted VM**
   - This is where the platform runs.
   - Recommended: a dedicated server with good uptime and support.

2. **Domain name**
   - Example: `voice.yourcompany.com`
   - Gives your team a professional URL to access the platform.

3. **SSL certificate**
   - Secures the website (`https://`).
   - Usually automated via Let's Encrypt or provided by your hosting partner.

### B. Telephony (Required for live calls)

4. **Telephony provider account**
   - Example providers: Twilio or Plivo (Recommended).
   - This connects phone networks to your AI voice agent.

5. **Phone numbers**
   - Buy one or more business numbers for inbound/outbound calls.
   - Cost depends on country and usage.

6. **Calling usage credits/billing**
   - Per-minute call charges apply.
   - Required for test and production calling.

### C. Optional but Recommended

7. **Support/maintenance package**
   - For updates, issue handling, and SLA-based support.

---

## 2) Commercial View (Simple)

### One-time setup items
- Initial deployment and configuration
- Domain/DNS setup
- SSL and security setup
- Telephony account onboarding

### Recurring monthly items
- Server hosting cost
- Domain renewal (annual, usually billed monthly/annually)
- Telephony number rental + call usage
- Optional support and monitoring subscriptions

---

## 3) Basic Flow (How It Works)

1. **Customer calls your business number**  
   The call first reaches your telephony provider.

2. **Telephony provider forwards call to your AI platform**  
   The provider securely connects the live audio stream.

3. **AI voice agent processes the conversation in real time**  
   It listens, understands intent, and responds naturally.

4. **Business rules/workflows are applied**  
   The platform follows your configured scripts, routing logic, and actions.

5. **Call details are stored securely**  
   Conversation metadata, recordings (if enabled), and outcomes are saved.

6. **Team reviews outcomes on dashboard**  
   Managers can review call results, quality, and performance metrics.

---

## 4) What Client Team Must Provide

- Final approved domain/subdomain
- Telephony provider choice (Twilio or Vonage)
- Billing owner for telephony and hosting accounts
- Security/IT point of contact
- Business owner for call scripts and approval

---

## 5) Responsibilities Split (Suggested)

### Implementation Partner
- Platform deployment and configuration
- Integration setup and validation
- Initial training and go-live support

### Client Team
- Purchase/manage hosting, domain, and telephony
- Provide credentials and approvals on time
- Own production operations and billing

---

## 6) Go-Live Acceptance (Non-Technical)

Before launch, confirm:

- [ ] Live URL opens securely (`https://`)
- [ ] Test inbound call works
- [ ] Test outbound call works
- [ ] Voice quality is acceptable
- [ ] Reporting/dashboard is visible to business users
- [ ] Support contacts are confirmed

---

## 7) Final Recommendation

For fastest and safest rollout:
- Start with one number and one use case
- Run a pilot for 1-2 weeks
- Review call quality and business outcomes
- Expand gradually to more numbers/use cases

