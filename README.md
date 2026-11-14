
A limited context voice assistant that takes your McDonald's order, kind of like those self-order kiosks but you just talk to it. Say "Hey Dummy", tell it what you want, and it adds stuff to your order on a fake kiosk screen while it talks back. It'll also try to upsell you on fries, which felt accurate.

Made this for fun over a weekend. Not affiliated with McDonald's in any way, the menu and prices are just roughly what I remember from India.

## what it does

 wakes up when you say "Hey Dummy" (or press space if it doesn't hear you)
 glowing orb on the left that changes when it's listening / thinking / talking
 fake kiosk on the right that updates live as you order
 suggests meals, drinks, deals, tells you when you're close to the 10% off
 answers random questions too, then drags you back to ordering
 reads your order back and "checks out" at the end

## running it


Get a free Gemini API key from https://aistudio.google.com/apikey
pip install -r requirements.txt


Run it with python main.py


Esc closes the window.

## if something's off

Run "python check.py" first. It tests your key against each model, lists your mics, and checks if it can actually hear you.

- it can't hear me: add MIC_THRESHOLD=150 to .env, go lower if it still misses you
- wrong mic: check.py prints a numbered list, put your number in MIC_INDEX
- "my brain lagged": usually the free tier rate limit, wait a minute
- want a different voice: try `en-IN-PrabhatNeural`, `en-IN-NeerjaNeural` or `en-GB-RyanNeural` in `VOICE`

Needs internet the whole time, the speech recognition and the voice both run online.

## built with

Gemini for the brain, Google speech recognition for listening, edge-tts for the voice, and plain tkinter for the UI.