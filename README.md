# fresh-direct-poller
Poll FreshDirect grocery delivery timeslots to alert user on availability.

Requirements
============
Requires a valid fresh direct email account for authentication, and a MessageBird api key to send text alerts. 

You can subclass Alerter and follow my MessageBird example to implement Twilio or whatever you prefer.

Suggestions
===========
I recommend using a VPN, and not using your real fresh direct email address with this poller. I created a dummy fresh direct account for this poller using a [Temp Mail](https://temp-mail.org/) address. 

Note: after serious amounts of testing and pattern usage, fresh direct has neither blocked my account nor my VPN address.

Contributing
============
Contributors are welcome :) If you have a stronger vision (than I) for how this could evolve into a production app to serve people during covid lets talk!