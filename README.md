# CC Codriver

Tooling to examine RBR Pacenotes and the RBR Pacenotes plugin and conversion to CrewChief Codriver format


## Copilot links

*  https://thecrewchief.org/showthread.php?825-Authoring-alternative-Crew-Chief-voice-packs
*  https://thecrewchief.org/showthread.php?1851-Richard-Burns-Rally-Crew-Chief-setup-and-known-issues
*  https://gitlab.com/mr_belowski/CrewChiefV4/-/blob/master/complete-radioerize-from-raw.txt
*  https://nerdynav.com/best-ai-voice-generators/
*  https://github.com/Smo-RBR/RBR-German-tts-Codriver
*  https://racemarket.net/blog/rally-pacenotes-what-why-how


## TTS Links

*  https://github.com/anton264/voice_gen
*  https://github.com/suno-ai/bark
*  https://github.com/neonbjb/tortoise-tts
*  https://github.com/DigitalPhonetics/IMS-Toucan/blob/ToucanTTS/run_text_to_file_reader.py
*  https://github.com/DigitalPhonetics/IMS-Toucan/issues/134
*  https://github.com/rhasspy/tts-prompts/blob/master/en-us/en-us_prompts.csv
*  https://www.redhat.com/en/blog/a-guide-to-gpu-enhanced-text-to-speech-model-training-with-red-hat-openshift-data-science-and-coqui-tts
*  https://www.redhat.com/en/blog/voice-cloning-and-tts-with-ims-toucan-and-red-hat-openshift-data-science
*  [Some AI generated samples in the CC #development channel](https://discord.com/channels/322071247032942592/1088819988917395496/1097596688362917948)
*  https://github.com/coqui-ai/TTS/discussions/2507
*  https://edresson.github.io/YourTTS/
*  https://sep.com/blog/helpful-tools-to-make-your-first-voice-clone-dataset-easy-to-build/
*  https://www.reddit.com/r/selfhosted/comments/17oabw3/selfhosted_texttospeech_and_voice_cloning_review/
*

```
sox input.wav output.wav \
compand 0.2,1 6:-70,-60,-20 5 -90 0.2 \
equalizer 100 0.707 -5 highpass 300 lowpass 3000 equalizer 1000 0.707 3 \
gain 2.3 \
compand 0.2,1.0 6:-60,-1,-1 -5 -90 0.2

sox input.wav output.wav \
compand 0.2,1 6:-70,-60,-20 5 -90 0.2 \
equalizer 100 0.707 -5 highpass 300 lowpass 3000 equalizer 1000 0.707 3

sox input.wav output.wav \
highpass 300 lowpass 3000 \
compand 0.3,1 6:-70,-60,-20 5 -90 0.2 \
overdrive 10 \
equalizer 1000 0.707 3


sox input.wav output.wav \
highpass 300 lowpass 3000 \
compand 0.3,1.5 6:-60,-30 5 -90 0.2 \
overdrive 10 \
equalizer 1000 0.707 3


sox input.wav output.wav \
highpass 300 lowpass 3000 \
compand 0.3,2.5 6:-30,-40 5 -90 0.2 \
overdrive 10 \
equalizer 1000 0.707 3
```


## RBR Pacenotes Modifiers

53493760 - none
53493761 - narrows
53493762 - wideout
53493764 - tightens
53493792 - dont
53493824 - cut
53493888 - double tightens
53494784 - long
53501952 - maybe


We have documented the pacenote IDs used by the plugin (see xls/ods).
Custom IDs should be in the range from 1000 to 4000.
Don't use IDs over 4000, or you will break Pacenote plugin features!
Don't use or try to change those flags, they are all occupied and used internally, and even possibly crash the game when used in the wrong place.
Modifiers cannot be added, so you're always going to have at worst 8 flags to worry about

