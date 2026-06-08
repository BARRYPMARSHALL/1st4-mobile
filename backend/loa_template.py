"""Letter of Authority — Legal template for 1st 4 Mobile.

This is a professional Australian legal document that authorises
1st 4 Mobile Pty Ltd to act on behalf of a client in billing
disputes with Telstra and/or Optus.
"""

LETTER_OF_AUTHORITY_TEMPLATE = """LETTER OF AUTHORITY

DATE: {date}

TO: {carrier}
    Accounts / Billing Disputes Department

FROM: {company_name}
      ABN: {abn}

RE: AUTHORITY TO ACCESS BILLING RECORDS AND ACT AS AGENT
    FOR BILLING DISPUTE RESOLUTION

1. AUTHORISATION

We, {company_name} (ABN: {abn}) ("the Client"), hereby authorise
1st 4 Mobile Pty Ltd (ACN: 666 369 915) ("the Agent") to act as
our authorised representative and agent in all matters pertaining
to the review, audit, and disputation of our telecommunications
billing accounts with {carrier}.

2. SCOPE OF AUTHORITY

This Letter of Authority grants the Agent full authority to:

   (a) Access, inspect, and obtain copies of all billing records,
       invoices, call detail records, usage reports, and account
       statements held by {carrier} in relation to the Client's
       account(s);

   (b) Communicate directly with {carrier}'s billing, accounts,
       and disputes departments regarding the Client's accounts;

   (c) Request and review historical billing data for the period
       commencing {period_start} and continuing for the duration
       of this authority;

   (d) Engage in dispute resolution proceedings, including the
       lodgement of formal billing disputes, requests for credit
       adjustments, and escalation of unresolved matters through
       the Telecommunications Industry Ombudsman (TIO) if required;

   (e) Appoint and instruct third-party billing analysts,
       telecommunications consultants, and legal advisors as
       reasonably necessary to give effect to this authority.

3. DURATION OF AUTHORITY

This authority shall commence on the date of signing and shall
remain in full force and effect until:

   (a) The Client provides written revocation to both the Agent
       and {carrier}; or

   (b) The completion of the billing audit and all associated
       dispute resolution processes; or

   (c) 24 months from the date of signing, whichever occurs first.

4. CONFIDENTIALITY

The Agent agrees to treat all information obtained under this
authority as confidential and shall not disclose it to any third
party except as necessary for the purposes set out in this
document or as required by law.

5. INDEMNIFICATION

The Client agrees to indemnify and hold harmless 1st 4 Mobile
Pty Ltd, its directors, employees, and agents from and against
all claims, losses, damages, costs, and expenses arising out of
or in connection with:

   (a) Any act or omission by the Agent performed in good faith
       under this authority;

   (b) Any reliance by the Agent on information or instructions
       provided by the Client;

   (c) The accuracy or completeness of any information obtained
       from {carrier} under this authority.

The Client acknowledges that the Agent shall not be liable for
any indirect, consequential, or special damages arising from the
performance of services under this authority.

6. ACKNOWLEDGEMENT — PRIVACY ACT 1988 (CTH)

The Client acknowledges and consents to:

   (a) The collection, use, and disclosure of personal and
       account information by the Agent for the purposes set out
       in this document;

   (b) The disclosure of such information to {carrier} and the
       TIO as reasonably required;

   (c) The Agent complying with the Privacy Act 1988 (Cth) and
       the Australian Privacy Principles in handling the Client's
       information.

7. REPRESENTATIONS AND WARRANTIES

The Client represents and warrants that:

   (a) It is duly authorised to execute this document and has
       obtained all necessary internal approvals;

   (b) The information provided to the Agent is true, accurate,
       and complete;

   (c) It has the legal capacity to grant the authorities set
       out in this document;

   (d) It is not aware of any matter that would prevent {carrier}
       from honouring this authority.

8. GOVERNING LAW

This Letter of Authority shall be governed by and construed in
accordance with the laws of the State of New South Wales,
Australia.

────────────────────────────────────────────────────────────────

SIGNED this {day} day of {month}, {year}.

SIGNED for and on behalf of {company_name}
(ABN: {abn})

_________________________________________
Signature of Authorised Officer

_________________________________________
Name of Authorised Officer (please print)

_________________________________________
Position / Title

_________________________________________
Date

────────────────────────────────────────────────────────────────

ACKNOWLEDGED AND ACCEPTED by 1st 4 Mobile Pty Ltd

_________________________________________
Signature of Authorised Representative

_________________________________________
Name of Authorised Representative (please print)

_________________________________________
Date

────────────────────────────────────────────────────────────────

This document is a Letter of Authority under the
Telecommunications Act 1997 (Cth) and the
Telecommunications Consumer Protections Code (C628:2021).
"""


def get_loa_text(company_name: str, abn: str, carrier: str) -> str:
    """Generate a populated Letter of Authority for a given client.

    Args:
        company_name: The client's company name.
        abn: The client's Australian Business Number.
        carrier: The telecommunications carrier (e.g., 'Telstra', 'Optus').

    Returns:
        Fully formatted LOA text with placeholders replaced.
    """
    from datetime import date
    today = date.today()
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    return LETTER_OF_AUTHORITY_TEMPLATE.format(
        date=today.strftime("%d %B %Y"),
        company_name=company_name,
        abn=abn,
        carrier=carrier,
        period_start=today.strftime("%B %Y"),
        day=today.day,
        month=months[today.month - 1],
        year=today.year,
    )
