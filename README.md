# fresh-direct-poller
Poll FreshDirect grocery delivery timeslots to alert user on availability.

Usage
=====
1. Clone project and `pip install -r install requirements.txt` .
2. Configure `config.json` with valid Fresh Direct login credentials (see Suggestions below) and Message Bird api key to send text alerts. (You can subclass Alerter and follow my MessageBird example to implement Twilio or whatever you prefer).
3. Run `python fd_poller.py config.json` to start polling and alerting!

Suggestions
===========
1. I recommend against using your real fresh direct email address with this poller. I created a dummy fresh direct account just for this poller using a [Temp Mail](https://temp-mail.org/) address. 
2. I also recommend using a VPN in case using this app results in Fresh Direct blocking traffic from your address.

Contributing
============
Contributors are welcome :) If you have a stronger vision (than I) for how this could evolve into a production app to serve people during covid lets talk!
